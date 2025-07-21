import asyncio

from xtquant.xttype import StockAccount
from modules.stock_selector.selector import StockSelector
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer
from utils.date_util import is_trading_time

# 假设你有如下实例
# xt_trader: QMT交易API实例
# account: QMT账户
# latest_price_cache: 实时行情缓存

# 全局行情缓存
latest_price_cache = {}

class TechnicalAnalyzer:
    """技术指标分析器（示例，可扩展）"""
    def calculate_indicators(self, df):
        # 这里只做简单均线示例
        if df is None or len(df) < 20:
            return None
        ma5 = df['close'].rolling(window=5).mean().iloc[-1]
        ma20 = df['close'].rolling(window=20).mean().iloc[-1]
        last_close = df['close'].iloc[-1]
        return {"ma5": ma5, "ma20": ma20, "close": last_close}

    def is_tradable(self, indicators):
        # 示例：MA5上穿MA20
        if not indicators:
            return False
        return indicators["ma5"] > indicators["ma20"]

    def is_buy_signal(self, indicators):
        # MA5上穿MA20
        return indicators and indicators["ma5"] > indicators["ma20"]

    def is_sell_signal(self, indicators, avg_price=None, current_price=None):
        # MA5下穿MA20
        if indicators and indicators["ma5"] < indicators["ma20"]:
            return True
        # 止盈止损
        if avg_price and current_price:
            pnl = (current_price - avg_price) / avg_price * 100
            if pnl > 10 or pnl < -5:
                return True
        return False

async def auto_select_analyze_trade_monitor(
    stock_selector: StockSelector,
    xt_trader,
    account,
    position_analyzer: PositionAnalyzer,
    technical_analyzer: TechnicalAnalyzer,
    get_history_func,
    get_latest_price_func,
    interval: int = 3600
):
    """
    自动选股-分析-下单-持仓监控主流程
    get_history_func(symbol) -> DataFrame
    get_latest_price_func(symbol) -> float
    """
    while True:
        if not is_trading_time():
            print("[自动交易] 当前非交易时间，等待...")
            await asyncio.sleep(60)
            continue
        # 1. 选股（可用pywencai或本地因子）
        selected = stock_selector.select_by_wencai("市盈率小于10且银行行业，最新涨跌幅大于0，前10名")
        # 或 selected = stock_selector.select(...)
        print(f"选股结果: {selected}")

        # 2. QMT分析选出的股票（如技术指标、风控等）
        tradable_stocks = []
        for stock in selected:
            symbol = stock['symbol']
            df = await asyncio.to_thread(get_history_func, symbol)
            indicators = technical_analyzer.calculate_indicators(df)
            if technical_analyzer.is_tradable(indicators):
                tradable_stocks.append(symbol)

        # 3. 查询当前持仓
        positions = await asyncio.to_thread(xt_trader.query_stock_positions, account)
        held = {p.stock_code for p in positions}

        # 4. 自动下单买入
        for symbol in tradable_stocks:
            if symbol not in held:
                price = get_latest_price_func(symbol)
                if price is None:
                    print(f"无法获取{symbol}最新价，跳过下单")
                    continue
                await asyncio.to_thread(xt_trader.create_order, symbol, "买", price, 100, account)
                print(f"自动下单: {symbol} 价格: {price}")

        # 5. 持续监控持仓
        positions = await asyncio.to_thread(xt_trader.query_stock_positions, account)
        analysis = position_analyzer.analyze_positions([
            {
                "symbol": p.stock_code,
                "volume": p.volume,
                "available_volume": getattr(p, 'enable_amount', p.volume),
                "avg_price": p.avg_price,
                "current_price": get_latest_price_func(p.stock_code)
            }
            for p in positions
        ])
        print("持仓分析结果:", analysis)

        await asyncio.sleep(interval) 

async def monitor_positions_continuously(
    xt_trader,
    account,
    position_analyzer: PositionAnalyzer,
    get_latest_price_func,
    interval: int = 60
):
    """
    持仓持续监控任务，每interval秒分析一次持仓。
    """
    while True:
        try:
            positions = await asyncio.to_thread(xt_trader.query_stock_positions, account)
            analysis = position_analyzer.analyze_positions([
                {
                    "symbol": p.stock_code,
                    "volume": p.volume,
                    "available_volume": getattr(p, 'enable_amount', p.volume),
                    "avg_price": p.avg_price,
                    "current_price": get_latest_price_func(p.stock_code)
                }
                for p in positions
            ])
            print("[持仓监控] 最新持仓分析:", analysis)
            # 你可以在这里写入数据库、推送API、报警等
        except Exception as e:
            print(f"[持仓监控] 持仓分析失败: {e}")
        await asyncio.sleep(interval) 

async def monitor_positions_and_trade(
    stock_selector: StockSelector,
    xt_trader,
    account: StockAccount,
    position_analyzer: PositionAnalyzer,
    technical_analyzer: TechnicalAnalyzer,
    get_history_func,
    get_latest_price_func,
    order_manager,
    interval: int = 60
):
    """
    持仓持续监控+自动买卖任务。
    - 买入信号：MA5上穿MA20且未持有
    - 卖出信号：MA5下穿MA20或止盈>10%或止损<-5%
    """
    while True:
        if not is_trading_time():
            print("[自动交易] 当前非交易时间，等待...")
            await asyncio.sleep(60)
            continue
        try:
            positions = await asyncio.to_thread(xt_trader.query_stock_positions, account)
            valid_positions = [p for p in positions if hasattr(p, 'stock_code') and hasattr(p, 'volume')]
            held = {p.stock_code for p in valid_positions}
            # 2. 自动卖出
            for p in valid_positions:
                symbol = p.stock_code
                df = await asyncio.to_thread(get_history_func, symbol)
                indicators = technical_analyzer.calculate_indicators(df)
                current_price = get_latest_price_func(symbol)
                if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                    await asyncio.to_thread(order_manager.create_order, symbol, "卖", current_price, p.volume, account)
                    print(f"[自动卖出] {symbol} 价格: {current_price}")
            # 3. 选股池自动买入
            selected = stock_selector.select_by_wencai("市盈率小于10且银行行业，最新涨跌幅大于0，前10名")
            for stock in selected:
                symbol = stock['symbol']
                if symbol not in held:
                    df = await asyncio.to_thread(get_history_func, symbol)
                    indicators = technical_analyzer.calculate_indicators(df)
                    current_price = get_latest_price_func(symbol)
                    if technical_analyzer.is_buy_signal(indicators):
                        await asyncio.to_thread(order_manager.create_order, symbol, "买", current_price, 100, account)
                        print(f"[自动买入] {symbol} 价格: {current_price}")
            positions = await asyncio.to_thread(xt_trader.query_stock_positions, account)
            valid_positions = [p for p in positions if hasattr(p, 'stock_code') and hasattr(p, 'volume')]
            analysis = position_analyzer.analyze_positions([
                {
                    "symbol": p.stock_code,
                    "volume": p.volume,
                    "available_volume": getattr(p, 'enable_amount', p.volume),
                    "avg_price": p.avg_price,
                    "current_price": get_latest_price_func(p.stock_code)
                }
                for p in valid_positions
            ])
            print("[持仓监控] 最新持仓分析:", analysis)
        except Exception as e:
            print(f"[持仓监控] 自动买卖/分析失败: {e}")
        await asyncio.sleep(interval) 

def get_latest_price_func(symbol, xt_trader=None):
    from main import get_latest_price_func as main_get_latest_price_func
    return main_get_latest_price_func(symbol)