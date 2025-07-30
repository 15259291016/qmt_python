import asyncio

from xtquant.xttype import StockAccount
from modules.stock_selector.selector import StockSelector
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer
from utils.date_util import is_trading_time
import time

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
        # 1. 选股（自适应热点行业多因子选股）
        try:
            selected_codes = stock_selector.select_by_hot_industry()
            print(f"热点行业选股结果: {selected_codes}")
            # 兼容原有格式，转为dict列表
            selected = [{"symbol": code} for code in selected_codes]
        except Exception as e:
            print(f"[选股] 热点行业选股失败: {e}，回退到原有条件选股")
            selected = stock_selector.select_by_wencai("市盈率小于10且银行行业，最新涨跌幅大于0，前10名")
        print(f"选股结果: {selected}")

        # 2. QMT分析选出的股票（如技术指标、风控等）
        tradable_stocks = []
        for stock in selected:
            symbol = stock['symbol']
            df = get_history_func(symbol)
            indicators = technical_analyzer.calculate_indicators(df)
            if technical_analyzer.is_tradable(indicators):
                tradable_stocks.append(symbol)

        # 3. 查询当前持仓
        positions = xt_trader.query_stock_positions(account)
        held = {p.stock_code for p in positions}

        # 4. 自动下单买入
        for symbol in tradable_stocks:
            if symbol not in held:
                price = get_latest_price_func(symbol)
                if price is None:
                    print(f"无法获取{symbol}最新价，跳过下单")
                    continue
                await xt_trader.order_manager(symbol, "买", price, 100, account)
                print(f"自动下单: {symbol} 价格: {price}")

        # 5. 持续监控持仓
        positions = xt_trader.query_stock_positions(account)
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
            positions = xt_trader.query_stock_positions(account)
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
    - 集成恐贪指数决策（极端行情优化）
    """
    last_status = None  # 记录上一次交易状态，防止刷屏
    while True:
        trading = is_trading_time()
        if not trading:
            if last_status and last_status != 'not_trading':
                print("[自动交易] 当前非交易时间，等待...")
                last_status = 'not_trading'
            time.sleep(30)  # 非交易时段加长等待，减少刷屏
            continue
        last_status = 'trading'
        try:
            positions = xt_trader.query_stock_positions(account)
            valid_positions = [p for p in positions if hasattr(p, 'stock_code') and hasattr(p, 'volume')]
            held = {p.stock_code for p in valid_positions}
            # 获取持仓分析，提取恐贪指数
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
            summary = analysis.summary
            fear_greed_index = getattr(summary, 'fear_greed_index', 50)
            long_term_fear_greed_index = getattr(summary, 'long_term_fear_greed_index', 50)
            print(f"[恐贪指数] 当日: {fear_greed_index:.1f}，长期: {long_term_fear_greed_index:.1f}")
            # 2. 自动卖出
            for p in valid_positions:
                symbol = p.stock_code
                df = get_history_func(symbol)
                indicators = technical_analyzer.calculate_indicators(df)
                current_price = get_latest_price_func(symbol)
                # 极端恐慌下禁止卖出
                if fear_greed_index < 10:
                    print(f"[卖出决策] 极端恐慌({fear_greed_index:.1f})，禁止卖出 {symbol}，建议耐心等待情绪修复。")
                    continue
                # 恐慌区间仅允许止损卖出
                if 10 <= fear_greed_index < 20:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        pnl = (current_price - p.avg_price) / p.avg_price * 100
                        if pnl < -5:
                            await order_manager(symbol, "卖", current_price, p.m_nCanUseVolume, account)
                            print(f"[卖出决策] 恐慌区间({fear_greed_index:.1f})，仅允许止损卖出 {symbol} 价格: {current_price}")
                        else:
                            print(f"[卖出决策] 恐慌区间({fear_greed_index:.1f})，非止损不卖出 {symbol}")
                    continue
                # 极端贪婪下允许加大卖出
                if fear_greed_index > 90 or long_term_fear_greed_index > 90:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        await order_manager(symbol, "卖", current_price, p.m_nCanUseVolume, account)
                        print(f"[卖出决策] 极端贪婪({fear_greed_index:.1f})，加大卖出 {symbol} 价格: {current_price}，建议锁定收益。")
                    continue
                # 80-90区间正常卖出
                if 80 < fear_greed_index <= 90 or 80 < long_term_fear_greed_index <= 90:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        await order_manager(symbol, "卖", current_price, p.m_nCanUseVolume, account)
                        print(f"[卖出决策] 贪婪区间({fear_greed_index:.1f})，正常卖出 {symbol} 价格: {current_price}")
                    continue
                # 其它情况正常卖出
                if p.m_nCanUseVolume != 0 and technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                    await order_manager(symbol, "卖", current_price, p.m_nCanUseVolume, account)
                    print(f"[自动卖出] {symbol} 价格: {current_price}")
            # 3. 选股池自动买入（自适应热点行业）
            try:
                selected_codes = stock_selector.select_by_hot_industry()
                print(f"热点行业选股结果: {selected_codes}")
                selected = [{"symbol": code} for code in selected_codes]
            except Exception as e:
                print(f"[选股] 热点行业选股失败: {e}，回退到原有条件选股")
                selected = stock_selector.select_by_wencai("银行行业，市盈率TTM小于10，市净率小于1.2，净利润同比增长率大于5%，近3个月涨幅大于0，波动率小于5%，按净利润同比增长率降序排列，前10名")
            for stock in selected:
                symbol = stock['symbol']
                if symbol not in held:
                    df = get_history_func(symbol)
                    indicators = technical_analyzer.calculate_indicators(df)
                    current_price = get_latest_price_func(symbol)
                    min_amount = get_min_buy_amount(symbol)
                    # 极端恐慌下仅允许极小仓位买入
                    if fear_greed_index < 10:
                        print(f"[买入决策] 极端恐慌({fear_greed_index:.1f})，仅允许极小仓位买入 {symbol}，建议谨慎抄底。买入{min_amount}股")
                        await order_manager(symbol, "买", current_price, min_amount, account)
                        continue
                    # 恐慌区间允许小仓位买入
                    if 10 <= fear_greed_index < 20:
                        print(f"[买入决策] 恐慌区间({fear_greed_index:.1f})，仅允许小仓位买入 {symbol}，建议分批建仓。买入{min_amount*0.5//min_amount*min_amount if min_amount*0.5>=min_amount else min_amount}股")
                        await order_manager(symbol, "买", current_price, min_amount, account)
                        continue
                    # 极端贪婪下禁止买入
                    if fear_greed_index > 90 or long_term_fear_greed_index > 90:
                        print(f"[买入决策] 极端贪婪({fear_greed_index:.1f})，禁止买入 {symbol}，建议耐心等待回调。")
                        continue
                    # 贪婪区间仅允许小仓位买入
                    if 80 < fear_greed_index <= 90 or 80 < long_term_fear_greed_index <= 90:
                        print(f"[买入决策] 贪婪区间({fear_greed_index:.1f})，仅允许小仓位买入 {symbol}，建议谨慎追高。买入{min_amount}股")
                        await order_manager(symbol, "买", current_price, min_amount, account)
                        continue
                    # 恐慌区间加大买入
                    if fear_greed_index < 30 and long_term_fear_greed_index < 40:
                        print(f"[买入决策] 市场恐慌(当日{fear_greed_index:.1f}/长期{long_term_fear_greed_index:.1f})，允许加大买入 {symbol}。买入{min_amount*2}股")
                        await order_manager(symbol, "买", current_price, min_amount*2, account)
                        print(f"[自动买入-加大] {symbol} 价格: {current_price}")
                        continue
                    # 其它情况正常买入
                    if technical_analyzer.is_buy_signal(indicators):
                        print(f"[买入决策] 正常买入 {symbol}，买入{min_amount}股")
                        await order_manager(symbol, "买", current_price, min_amount, account)
                        print(f"[自动买入] {symbol} 价格: {current_price}")
            # 持仓分析结果打印
            print("[持仓监控] 最新持仓分析:", analysis)
        except Exception as e:
            print(f"[持仓监控] 自动买卖/分析失败: {e}")
        await asyncio.sleep(interval)  # 交易时段内保持原有间隔

def get_min_buy_amount(symbol: str) -> int:
    """
    根据股票代码判断最小买入股数：
    - 科创板688xxx.SH：200股起
    - 创业板300xxx.SZ：100股起
    - 北交所.BJ：100股起
    - 主板60xxxx.SH/00xxxx.SZ：100股起
    """
    if symbol.endswith('.BJ'):
        return 100
    if symbol.startswith('688'):
        return 200
    if symbol.startswith('300'):
        return 100
    if symbol.startswith('60') or symbol.startswith('00'):
        return 100
    return 100

def get_latest_price_func(symbol, xt_trader=None):
    from main import get_latest_price_func as main_get_latest_price_func
    return main_get_latest_price_func(symbol)