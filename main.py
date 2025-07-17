# coding=utf-8
import asyncio
import logging
import threading
import time

import tornado
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import configs.ConfigServer as Cs
from user_strategy import auto_Buy, select_stock, sell
from utils.callback import MyXtQuantTraderCallback
from utils.data import download_all_data
from modules.tornadoapp.app import app
from modules.tornadoapp.db.dbUtil import init_beanie
from modules.tornadoapp.oms.order_manager import OrderManager
from modules.tornadoapp.risk.risk_manager import RiskManager
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
from modules.tornadoapp.audit.audit_logger import AuditLogger
from user_strategy.select_stock import QuantitativeStockSelector
from modules.tornadoapp.oms.backtest_engine import BacktestEngine
import pandas as pd
import random

# 策略模板示例
class SimpleMAStrategy:
    def __init__(self, short_window=5, long_window=20):
        self.short_window = short_window
        self.long_window = long_window
        self.prices = {}
    def on_bar(self, bar, account_id):
        symbol = bar['symbol']
        if symbol not in self.prices:
            self.prices[symbol] = []
        self.prices[symbol].append(bar['close'])
        if len(self.prices[symbol]) < self.long_window:
            return 0
        short_ma = pd.Series(self.prices[symbol][-self.short_window:]).mean()
        long_ma = pd.Series(self.prices[symbol][-self.long_window:]).mean()
        if short_ma > long_ma:
            return 1  # 买入
        elif short_ma < long_ma:
            return -1  # 卖出
        else:
            return 0

# 主流程回测集成示例
def run_backtest_demo():
    # 1. 加载A股多品种历史数据（假设已准备好DataFrame，包含symbol字段）
    # 示例：data = pd.read_csv('multi_stock_data.csv')
    # 这里用模拟数据
    dates = pd.date_range('2023-01-01', '2023-03-01')
    symbols = ['000001.SZ', '000002.SZ']
    data = []
    for symbol in symbols:
        price = 10 + random.random()
        for dt in dates:
            price += random.uniform(-0.2, 0.2)
            data.append({'datetime': dt, 'symbol': symbol, 'open': price, 'high': price+0.1, 'low': price-0.1, 'close': price, 'volume': 10000})
    df = pd.DataFrame(data)
    # 2. 多账户多策略
    accounts = ['acc1', 'acc2']
    strategies = {
        'acc1': SimpleMAStrategy(short_window=5, long_window=20),
        'acc2': SimpleMAStrategy(short_window=10, long_window=30)
    }
    # 3. 回测引擎，支持滑点、成交概率
    engine = BacktestEngine(strategies, df, accounts, initial_capital=1000000, slippage=0.02, fill_prob=0.95)
    reports = engine.run()
    for aid, rep in reports.items():
        print(f"账户: {aid}")
        print(f"总收益: {rep['total_return']:.2%}, 年化: {rep['annual_return']:.2%}, 夏普: {rep['sharpe']:.2f}, 最大回撤: {rep['max_drawdown']:.2%}")
        print(rep['equity_curve'].tail())

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_config():
    """获取配置信息"""
    try:
        configData = Cs.returnConfigData()
        path = configData["QMT_PATH"][0]
        account = configData["account"][0]
        return path, account
    except Exception as e:
        logger.error(f"配置读取失败: {e}")
        raise


def run_tornado_server():
    """启动Tornado Web 服务"""
    try:
        logger.info("正在启动 Tornado 服务...")
        tornado.ioloop.IOLoop.current().run_sync(init_beanie)
        http_server = tornado.httpserver.HTTPServer(app, max_body_size=1024 * 5)
        http_server.listen(8888)
        logger.info("Tornado 服务启动成功，监听端口: 8888")
        tornado.ioloop.IOLoop.current().start()
    except Exception as e:
        logger.error(f"Tornado 服务启动失败: {e}")
        raise


def auto_select_and_buy(xt_trader, acc, order_manager, top_n=10):
    configData = Cs.returnConfigData()
    toshare_token = configData["toshare_token"]
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '6116988.niu',
        'database': 'stock_data',
        'port': 3306,
        'charset': 'utf8mb4'
    }
    selector = QuantitativeStockSelector(token=toshare_token, db_config=db_config)
    stock_pool = selector.get_top_stocks(top_n=top_n)
    positions = xt_trader.query_stock_positions(acc)
    held_stocks = {p.stock_code for p in positions} if positions else set()
    for stock in stock_pool:
        if stock not in held_stocks:
            price = 10.0  # 可替换为实时价格
            quantity = 100
            order = order_manager.create_order(stock, "买", price, quantity, acc)
            print(f"自动买入下单: {stock}, 订单: {order}")


async def run_trader_system(path, account):
    """动量化交易系统"""
    try:
        logger.info("正在启动量化交易系统...")
        
        # 初始化调度器
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            download_all_data,
            trigger=CronTrigger(day_of_week="0-4", hour=15, minute=40),
            id="morning_analysis",
            replace_existing=True
        )
        scheduler.start()
        logger.info("数据下载调度器启动成功")
        
        # 初始化交易账户
        acc = StockAccount(account, 'STOCK')
        session_id = int(time.time())
        xt_trader = XtQuantTrader(path, session_id)
        xt_trader.start()
        xt_trader.connect()
        
        # 集成风控、合规、审计
        risk_manager = RiskManager()
        compliance_manager = ComplianceManager()
        audit_logger = AuditLogger()
        order_manager = OrderManager(xt_trader, risk_manager, compliance_manager, audit_logger)
        
        # 注册回调
        callback = MyXtQuantTraderCallback(order_manager)
        xt_trader.register_callback(callback)
        
        # 订阅账户
        subscribe_result = xt_trader.subscribe(acc)
        if subscribe_result == -1:
            logger.error("账户订阅失败，请重新打开QMT")
            raise Exception('重新打开qmt')
        
        logger.info("交易账户连接成功")
        
        # 启动策略线程
        thread_list = []
        # thread_list.append(threading.Thread(target=auto_Buy.run_strategy, args=(acc, xt_trader, order_manager)))
        # thread_list.append(threading.Thread(target=select_stock.run_strategy, args=()))
        thread_list.append(threading.Thread(target=sell.run_strategy, args=("000011.SZ", acc, xt_trader, order_manager)))
        
        for thread in thread_list:
            thread.daemon = True
            thread.start()
            logger.info(f"策略线程启动: {thread.name}")
        
        # 启动自动选股-下单闭环，每日定时执行
        def daily_select_and_buy():
            while True:
                auto_select_and_buy(xt_trader, acc, order_manager, top_n=10)
                time.sleep(86400)  # 每天执行一次
        threading.Thread(target=daily_select_and_buy, daemon=True).start()
        
        logger.info("量化交易系统启动完成")
        xt_trader.run_forever()
        
    except Exception as e:
        logger.error(f"量化交易系统启动失败: {e}")
        raise
    finally:
        try:
            scheduler.shutdown()
            logger.info("调度器已关闭")
        except Exception as e:
            logger.error(f"调度器关闭失败: {e}")


async def main():
    """主程序入口"""
    try:
        # 获取配置
        path, account = get_config()
        logger.info(f"配置加载成功 - QMT路径: {path}, 账户: {account}")
        
        # 启动量化交易系统（在后台线程中运行）
        trader_task = asyncio.create_task(run_trader_system(path, account))
        
        # 启动 Tornado 服务（在后台线程中运行）
        # tornado_task = asyncio.create_task(
        #     asyncio.to_thread(run_tornado_server)
        # )
        
        # 等待两个服务运行
        # await asyncio.gather(trader_task, tornado_task)
        await asyncio.gather(trader_task)
        
    except Exception as e:
        logger.error(f"主程序运行异常: {e}")
        raise


if __name__ == "__main__":
    try:
        logger.info("程序启动中...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.exception(f"程序异常退出: {e}")
        exit(1)
    # 回测集成示例
    run_backtest_demo()

