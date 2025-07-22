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
from modules.tornadoapp.auto_trader import monitor_positions_and_trade, TechnicalAnalyzer
from modules.stock_selector.selector import StockSelector
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer
import tushare as ts
from utils.date_util import is_trading_time

# 全局行情缓存
latest_price_cache = {}

def get_history_func(symbol, tushare_token=None):
    """用Tushare获取历史行情，返回DataFrame"""
    if tushare_token is None:
        raise ValueError("tushare_token未设置")
    pro = ts.pro_api(tushare_token)
    try:
        df = pro.daily(ts_code=symbol, start_date='20240101', end_date='20991231')
        if not df.empty:
            df = df.sort_values('trade_date')
            df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"获取{symbol}历史行情失败: {e}")
        return None

def get_latest_price_func(symbol, xt_trader=None):
    """优先用缓存，无则用xtdata.get_full_tick兜底获取最新价"""
    price = latest_price_cache.get(symbol)
    if price is not None:
        return price
    try:
        from xtquant import xtdata
        tick_info = xtdata.get_full_tick([symbol])
        if symbol in tick_info and 'lastPrice' in tick_info[symbol]:
            price = tick_info[symbol]['lastPrice']
            latest_price_cache[symbol] = price
            return price
    except Exception as e:
        print(f"xtdata获取{symbol}最新价失败: {e}")
    return None

# 策略模板示例
class SimpleMAStrategy:
    def __init__(self, short_window=5, long_window=20):
        self.short_window = short_window
        self.long_window = long_window
        self.prices = {}
    async def on_bar(self, bar, account_id):
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
async def run_multi_strategy_backtest():
    """运行多策略回测"""
    try:
        logger.info("开始多策略回测...")
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
        from modules.strategy_manager.manager import StrategyManager
        from modules.tornadoapp.oms.order_manager import OrderManager
        from modules.tornadoapp.risk.risk_manager import RiskManager
        from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
        from modules.tornadoapp.audit.audit_logger import AuditLogger
        class MockXtTrader:
            async def query_stock_positions(self, account):
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
        strategy_manager.add_account("backtest_account", None)
        for symbol in symbols:
            strategy_manager.add_symbol(symbol)
        strategy_manager.load_strategies_from_config()
        strategy_manager.assign_strategy_to_account("ma_5_20", "backtest_account", ["000001.SZ", "000002.SZ"])
        strategy_manager.assign_strategy_to_account("ma_10_30", "backtest_account", ["000858.SZ", "002415.SZ", "600036.SH"])
        from modules.strategy_manager.backtest_engine import BacktestEngine as StrategyBacktestEngine
        backtest_engine = StrategyBacktestEngine(
            strategy_manager=strategy_manager,
            data=df,
            initial_capital=1000000,
            commission_rate=0.0003,
            slippage=0.001
        )
        results = await backtest_engine.run_backtest(
            start_date=pd.Timestamp('2023-01-01'),
            end_date=pd.Timestamp('2023-03-01')
        )
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
        report = await backtest_engine.generate_report()
        logger.info("回测报告:")
        logger.info(report)
        await backtest_engine.save_results()
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


async def get_config(environment: str = 'SIMULATION'):
    """获取配置信息"""
    try:
        from utils.environment_manager import get_env_manager
        env_manager = get_env_manager()
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

async def run_tornado_server():
    """启动Tornado Web 服务"""
    try:
        logger.info("正在启动 Tornado 服务...")
        import tornado.httpserver
        from modules.tornadoapp.app import app
        from modules.tornadoapp.db.dbUtil import init_beanie
        from modules.data_service.api.tornado_integration import add_data_handlers
        await init_beanie()
        add_data_handlers(app)
        http_server = tornado.httpserver.HTTPServer(app, max_body_size=1024 * 5)
        http_server.listen(8888)
        logger.info("Tornado 服务启动成功，监听端口: 8888")
        # 不要再调用 loop.start() 或 IOLoop.current().start()
    except Exception as e:
        import traceback
        logger.error(f"Tornado 服务启动失败: {e}\n{traceback.format_exc()}")
        raise

async def auto_select_and_buy(xt_trader, acc, order_manager, top_n=10):
    if not is_trading_time():
        logger.info("[自动买入] 当前非交易时间，跳过本次自动买入。")
        return
    try:
        from utils.environment_manager import get_env_manager
        env_manager = get_env_manager()
        toshare_token = env_manager.get_tushare_token()
        db_config = env_manager.get_database_config()
        from user_strategy.simple_select_stock import SimpleStockSelector
        selector = SimpleStockSelector(token=toshare_token, db_config=db_config)
        stock_pool = await selector.get_top_stocks(top_n=top_n)
        if not stock_pool:
            logger.warning("未获取到推荐股票")
            return
        logger.info(f"获取到 {len(stock_pool)} 只推荐股票: {stock_pool}")
        positions = await xt_trader.query_stock_positions(acc)
        held_stocks = {p.stock_code for p in positions} if positions else set()
        new_stocks = [stock for stock in stock_pool if stock not in held_stocks]
        if not new_stocks:
            logger.info("所有推荐股票都已持有")
            return
        logger.info(f"准备买入 {len(new_stocks)} 只新股票: {new_stocks}")
        from modules.data_service.integration import get_data_service_manager
        data_manager = get_data_service_manager()
        for stock in new_stocks:
            try:
                bars = await asyncio.to_thread(data_manager.get_bar_data, stock, '20240101', '20991231', '1min')
                if bars:
                    price = bars[-1].close
                else:
                    price = None
                if price is None:
                    logger.warning(f"无法获取 {stock} 最新价格，使用默认价格")
                    price = 10.0
                quantity = 100
                order = await asyncio.to_thread(order_manager.create_order, stock, "买", price, quantity, acc)
                logger.info(f"自动买入下单: {stock}, 价格: {price}, 订单: {order}")
            except Exception as e:
                logger.error(f"买入 {stock} 失败: {e}")
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
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            download_all_data,
            trigger=CronTrigger(day_of_week="0-4", hour=15, minute=40),
            id="morning_analysis",
            replace_existing=True
        )
        scheduler.start()
        logger.info("数据下载调度器启动成功")
        acc = account
        session_id = int(time.time())
        xt_trader = XtQuantTrader(path, session_id, callback=None)
        risk_manager = RiskManager()
        compliance_manager = ComplianceManager()
        audit_logger = AuditLogger()
        order_manager = OrderManager(xt_trader, risk_manager, compliance_manager, audit_logger)
        callback = MyXtQuantTraderCallback(order_manager)
        xt_trader.callback = callback  # 必须在这里赋值，保证后续异步下单安全
        # 不再需要xt_trader.register_callback(callback)
        subscribe_result = await asyncio.to_thread(xt_trader.subscribe, acc)
        if subscribe_result == -1:
            logger.error("账户订阅失败，请重新打开QMT")
            raise Exception('重新打开qmt')
        logger.info("交易账户连接成功")
        strategy_manager = StrategyManager(
            xt_trader=xt_trader,
            order_manager=order_manager,
            data_service_manager=None,
            base_path="strategy_data"
        )
        strategy_manager.add_account(account, acc)
        strategy_manager.add_symbol("000001.SZ")
        strategy_manager.add_symbol("000002.SZ")
        strategy_manager.add_symbol("000858.SZ")
        strategy_manager.add_symbol("002415.SZ")
        strategy_manager.add_symbol("600036.SH")
        strategy_manager.load_strategies_from_config()
        strategy_manager.assign_strategy_to_account("ma_5_20", account, ["000001.SZ", "000002.SZ"])
        strategy_manager.assign_strategy_to_account("ma_10_30", account, ["000858.SZ", "002415.SZ", "600036.SH"])
        strategy_manager.start_all_strategies()
        add_strategy_handlers(app, strategy_manager)
        logger.info("策略管理API已集成到Tornado")
        async def daily_select_and_buy():
            while True:
                if not is_trading_time():
                    logger.info("[自动买入] 当前非交易时间，等待...")
                    await asyncio.sleep(60)
                    continue
                await auto_select_and_buy(xt_trader, acc, order_manager, top_n=10)
                await asyncio.sleep(86400)
        asyncio.create_task(daily_select_and_buy())
        async def daily_performance_calculation():
            while True:
                try:
                    for strategy_name in strategy_manager.strategies:
                        await asyncio.to_thread(strategy_manager.calculate_performance, strategy_name)
                    logger.info("策略绩效计算完成")
                except Exception as e:
                    logger.error(f"策略绩效计算失败: {e}")
                await asyncio.sleep(3600)
        asyncio.create_task(daily_performance_calculation())
        logger.info("多策略量化交易系统启动完成")
        await asyncio.to_thread(xt_trader.run_forever)
    except Exception as e:
        logger.error(f"多策略量化交易系统启动失败: {e}")
        raise
    finally:
        try:
            scheduler.shutdown()
            logger.info("调度器已关闭")
        except Exception as e:
            logger.error(f"调度器关闭失败: {e}")

async def trader_thread_func(path, account, environment):
    await run_trader_system(path, account, environment)

async def main_async():
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
        await run_multi_strategy_backtest()
    else:
        path, account_id = await get_config(args.env)
        # 初始化QMT交易API实例
        session_id = int(time.time())
        from xtquant.xttrader import XtQuantTrader
        xt_trader = XtQuantTrader(path, session_id)
        await asyncio.to_thread(xt_trader.start)
        await asyncio.to_thread(xt_trader.connect)
        # 获取tushare_token
        from utils.environment_manager import get_env_manager
        env_manager = get_env_manager()
        tushare_token = env_manager.get_tushare_token()
        # 构造StockAccount对象
        account = StockAccount(account_id, 'STOCK')
        # 初始化选股、分析等实例
        stock_selector = StockSelector(tushare_token=tushare_token)
        position_analyzer = PositionAnalyzer(tushare_token)
        technical_analyzer = TechnicalAnalyzer()
        # 初始化order_manager
        from modules.tornadoapp.oms.order_manager import OrderManager
        from modules.tornadoapp.risk.risk_manager import RiskManager
        from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
        from modules.tornadoapp.audit.audit_logger import AuditLogger
        risk_manager = RiskManager()
        compliance_manager = ComplianceManager()
        audit_logger = AuditLogger()
        order_manager = OrderManager(xt_trader, risk_manager, compliance_manager, audit_logger)
        callback = MyXtQuantTraderCallback(order_manager)
        xt_trader.callback = callback
        # 启动自动买卖+持仓监控闭环任务（每60秒自动买卖+分析）
        asyncio.create_task(
            monitor_positions_and_trade(
                stock_selector,
                xt_trader,
                account,
                position_analyzer,
                technical_analyzer,
                lambda symbol: get_history_func(symbol, tushare_token),
                lambda symbol: get_latest_price_func(symbol, xt_trader),
                order_manager,
                interval=60
            )
        )
        asyncio.create_task(trader_thread_func(path, account, args.env))
        await run_tornado_server()
        while True:
            await asyncio.sleep(36000)

if __name__ == "__main__":
    asyncio.run(main_async())

