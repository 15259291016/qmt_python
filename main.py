# coding=utf-8
import asyncio
import tornado.platform.asyncio
import logging
import threading
import time

import tornado
tornado.platform.asyncio.AsyncIOMainLoop().install()
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
from modules.strategy_manager.manager import StrategyManager
from modules.strategy_manager.api import add_strategy_handlers
from modules.strategy_manager.backtest_engine import BacktestEngine as StrategyBacktestEngine
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

# 多策略回测示例
def run_multi_strategy_backtest():
    """运行多策略回测"""
    try:
        logger.info("开始多策略回测...")
        
        # 1. 创建模拟历史数据
        dates = pd.date_range('2023-01-01', '2023-03-01')
        symbols = ['000001.SZ', '000002.SZ', '000858.SZ', '002415.SZ', '600036.SH']
        data = []
        
        for symbol in symbols:
            price = 10 + random.random() * 10
            for dt in dates:
                price += random.uniform(-0.2, 0.2)
                data.append({
                    'datetime': dt, 
                    'symbol': symbol, 
                    'open': price, 
                    'high': price + 0.1, 
                    'low': price - 0.1, 
                    'close': price, 
                    'volume': random.randint(1000, 10000)
                })
        
        df = pd.DataFrame(data)
        logger.info(f"生成模拟数据: {len(df)} 条记录，{len(symbols)} 个品种")
        
        # 2. 初始化策略管理器
        from modules.strategy_manager.manager import StrategyManager
        from modules.tornadoapp.oms.order_manager import OrderManager
        from modules.tornadoapp.risk.risk_manager import RiskManager
        from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
        from modules.tornadoapp.audit.audit_logger import AuditLogger
        
        # 创建模拟交易器
        class MockXtTrader:
            def query_stock_positions(self, account):
                return []
        
        mock_trader = MockXtTrader()
        risk_manager = RiskManager()
        compliance_manager = ComplianceManager()
        audit_logger = AuditLogger()
        order_manager = OrderManager(mock_trader, risk_manager, compliance_manager, audit_logger)
        
        strategy_manager = StrategyManager(
            xt_trader=mock_trader,
            order_manager=order_manager,
            base_path="backtest_data"
        )
        
        # 3. 添加账户和品种
        strategy_manager.add_account("backtest_account", None)
        for symbol in symbols:
            strategy_manager.add_symbol(symbol)
        
        # 4. 加载策略配置
        strategy_manager.load_strategies_from_config()
        
        # 5. 分配策略到账户
        strategy_manager.assign_strategy_to_account("ma_5_20", "backtest_account", ["000001.SZ", "000002.SZ"])
        strategy_manager.assign_strategy_to_account("ma_10_30", "backtest_account", ["000858.SZ", "002415.SZ", "600036.SH"])
        
        # 6. 运行回测
        from modules.strategy_manager.backtest_engine import BacktestEngine as StrategyBacktestEngine
        
        backtest_engine = StrategyBacktestEngine(
            strategy_manager=strategy_manager,
            data=df,
            initial_capital=1000000,
            commission_rate=0.0003,
            slippage=0.001
        )
        
        results = backtest_engine.run_backtest(
            start_date=pd.Timestamp('2023-01-01'),
            end_date=pd.Timestamp('2023-03-01')
        )
        
        # 7. 输出回测结果
        logger.info("回测完成，结果如下:")
        for strategy_name, result in results.items():
            logger.info(f"策略: {strategy_name}")
            logger.info(f"  总收益率: {result.total_return:.2%}")
            logger.info(f"  年化收益率: {result.annual_return:.2%}")
            logger.info(f"  夏普比率: {result.sharpe_ratio:.2f}")
            logger.info(f"  最大回撤: {result.max_drawdown:.2%}")
            logger.info(f"  胜率: {result.win_rate:.2%}")
            logger.info(f"  总交易次数: {result.total_trades}")
            logger.info("")
        
        # 8. 生成回测报告
        report = backtest_engine.generate_report()
        logger.info("回测报告:")
        logger.info(report)
        
        # 9. 保存回测结果
        backtest_engine.save_results()
        
        logger.info("多策略回测完成")
        
    except Exception as e:
        logger.error(f"多策略回测失败: {e}")
        import traceback
        traceback.print_exc()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 必须在所有import和代码之前调用install，彻底避免事件循环冲突
# ！！！请勿移动此行！！！


def get_config(environment: str = 'SIMULATION'):
    """获取配置信息"""
    try:
        from utils.environment_manager import get_env_manager
        env_manager = get_env_manager()
        
        # 切换到指定环境
        if not env_manager.switch_environment(environment):
            logger.error(f"切换到 {environment} 环境失败")
            raise Exception(f"环境切换失败: {environment}")
        
        path = env_manager.get_qmt_path()
        account = env_manager.get_account()
        
        logger.info(f"使用 {environment} 环境: QMT路径={path}, 账户={account}")
        return path, account
    except Exception as e:
        logger.error(f"配置读取失败: {e}")
        raise


def run_tornado_server():
    """启动Tornado Web 服务"""
    try:
        logger.info("正在启动 Tornado 服务...")
        import tornado.httpserver
        from modules.tornadoapp.app import app
        from modules.tornadoapp.db.dbUtil import init_beanie
        from modules.data_service.api.tornado_integration import add_data_handlers
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init_beanie())
        add_data_handlers(app)
        http_server = tornado.httpserver.HTTPServer(app, max_body_size=1024 * 5)
        http_server.listen(8888)
        logger.info("Tornado 服务启动成功，监听端口: 8888")
        tornado.ioloop.IOLoop.current().start()
        
    except Exception as e:
        logger.error(f"Tornado 服务启动失败: {e}")
        raise


def auto_select_and_buy(xt_trader, acc, order_manager, top_n=10):
    try:
        from utils.environment_manager import get_env_manager
        env_manager = get_env_manager()
        
        toshare_token = env_manager.get_tushare_token()
        db_config = env_manager.get_database_config()
        
        # 使用简化的选股器
        from user_strategy.simple_select_stock import SimpleStockSelector
        selector = SimpleStockSelector(token=toshare_token, db_config=db_config)
        stock_pool = selector.get_top_stocks(top_n=top_n)
        
        if not stock_pool:
            logger.warning("未获取到推荐股票")
            return
        
        logger.info(f"获取到 {len(stock_pool)} 只推荐股票: {stock_pool}")
        
        # 查询当前持仓
        positions = xt_trader.query_stock_positions(acc)
        held_stocks = {p.stock_code for p in positions} if positions else set()
        
        # 过滤掉已持有的股票
        new_stocks = [stock for stock in stock_pool if stock not in held_stocks]
        
        if not new_stocks:
            logger.info("所有推荐股票都已持有")
            return
        
        logger.info(f"准备买入 {len(new_stocks)} 只新股票: {new_stocks}")
        
        # 执行买入操作，使用数据服务获取最新价格
        from modules.data_service.integration import get_data_service_manager
        data_manager = get_data_service_manager()
        
        for stock in new_stocks:
            try:
                # 从数据服务获取最新价格
                bars = data_manager.get_bar_data(stock, '20240101', '20991231', '1min')
                if bars:
                    price = bars[-1].close
                else:
                    price = None  # 或做异常处理
                
                if price is None:
                    logger.warning(f"无法获取 {stock} 最新价格，使用默认价格")
                    price = 10.0
                
                quantity = 100
                order = order_manager.create_order(stock, "买", price, quantity, acc)
                logger.info(f"自动买入下单: {stock}, 价格: {price}, 订单: {order}")
            except Exception as e:
                logger.error(f"买入 {stock} 失败: {e}")
        
        # 关闭选股器连接
        selector.close()
        
    except Exception as e:
        logger.error(f"自动选股买入失败: {e}")


async def run_trader_system(path, account, environment='SIMULATION'):
    """多策略量化交易系统"""
    try:
        from utils.environment_manager import get_env_manager
        env_manager = get_env_manager()
        
        logger.info(f"正在启动多策略量化交易系统 ({environment})...")
        logger.info(f"环境信息: {env_manager.get_environment_name()}")
        logger.info(f"QMT路径: {path}")
        logger.info(f"账户: {account}")
        
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
        
        # 删除 data_manager.start_data_collection(auto_collect=True) 的所有调用
        # 如果需要采集功能，请用 daily_collector.collect_all_daily 独立实现
        
        # 初始化多策略管理器
        strategy_manager = StrategyManager(
            xt_trader=xt_trader,
            order_manager=order_manager,
            data_service_manager=None, # 移除 data_manager
            base_path="strategy_data"
        )
        
        # 添加账户和品种
        strategy_manager.add_account(account, acc)
        strategy_manager.add_symbol("000001.SZ")
        strategy_manager.add_symbol("000002.SZ")
        strategy_manager.add_symbol("000858.SZ")
        strategy_manager.add_symbol("002415.SZ")
        strategy_manager.add_symbol("600036.SH")
        
        # 加载策略配置
        strategy_manager.load_strategies_from_config()
        
        # 分配策略到账户
        strategy_manager.assign_strategy_to_account("ma_5_20", account, ["000001.SZ", "000002.SZ"])
        strategy_manager.assign_strategy_to_account("ma_10_30", account, ["000858.SZ", "002415.SZ", "600036.SH"])
        
        # 启动所有策略
        strategy_manager.start_all_strategies()
        
        # 集成策略管理API到Tornado
        add_strategy_handlers(app, strategy_manager)
        logger.info("策略管理API已集成到Tornado")
        
        # 启动自动选股-下单闭环，每日定时执行
        def daily_select_and_buy():
            while True:
                auto_select_and_buy(xt_trader, acc, order_manager, top_n=10)
                time.sleep(86400)  # 每天执行一次
        threading.Thread(target=daily_select_and_buy, daemon=True).start()
        
        # 启动策略绩效计算定时任务
        def daily_performance_calculation():
            while True:
                try:
                    for strategy_name in strategy_manager.strategies:
                        strategy_manager.calculate_performance(strategy_name)
                    logger.info("策略绩效计算完成")
                except Exception as e:
                    logger.error(f"策略绩效计算失败: {e}")
                time.sleep(3600)  # 每小时计算一次
        threading.Thread(target=daily_performance_calculation, daemon=True).start()
        
        logger.info("多策略量化交易系统启动完成")
        xt_trader.run_forever()
        
    except Exception as e:
        logger.error(f"多策略量化交易系统启动失败: {e}")
        raise
    finally:
        try:
            scheduler.shutdown()
            logger.info("调度器已关闭")
        except Exception as e:
            logger.error(f"调度器关闭失败: {e}")


def trader_thread_func(path, account, environment):
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_trader_system(path, account, environment))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='多策略量化交易平台')
    parser.add_argument('--env', '--environment', 
                       choices=['SIMULATION', 'PRODUCTION'], 
                       default='SIMULATION',
                       help='运行环境 (SIMULATION: 模拟环境, PRODUCTION: 实盘环境)')
    parser.add_argument('--mode', '--run-mode',
                       choices=['live', 'backtest'],
                       default='live',
                       help='运行模式 (live: 实盘/模拟交易, backtest: 回测)')
    args = parser.parse_args()

    logger.info(f"程序启动中... 环境: {args.env}, 模式: {args.mode}")
    if args.mode == 'backtest':
        run_multi_strategy_backtest()
    else:
        path, account = get_config(args.env)
        t = threading.Thread(target=trader_thread_func, args=(path, account, args.env), daemon=True)
        t.start()
        run_tornado_server()

