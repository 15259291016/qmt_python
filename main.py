# coding=utf-8
import asyncio
import logging
import pandas as pd
import threading
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import tushare as ts
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from modules.tornadoapp.db.dbUtil import init_beanie
from utils.data import download_all_data
from utils.date_util import is_trading_time
from xtquant.xttrader import XtQuantTrader
from utils.environment_manager import get_env_manager
from modules.stock_selector.selector import StockSelector
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer
from modules.tornadoapp.auto_trader import TechnicalAnalyzer

from modules.tornadoapp.oms.order_manager import OrderManager
from modules.tornadoapp.risk.risk_manager import RiskManager
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
from modules.tornadoapp.audit.audit_logger import AuditLogger
# 只保留实际用到的依赖

# 全局行情缓存
latest_price_cache = {}

# 全局历史数据缓存（带过期时间）
history_data_cache = {}
CACHE_EXPIRE_SECONDS = 600  # 缓存10分钟过期（从5分钟增加到10分钟，减少API调用）

# 市场趋势缓存（更长的过期时间）
market_trend_cache = {}
MARKET_TREND_CACHE_EXPIRE_SECONDS = 1800  # 市场趋势缓存30分钟过期

# 全局调度器实例
scheduler = BackgroundScheduler()

# 全局依赖对象（初始化为None，main_async中赋值）
stock_selector = None
position_analyzer = None
technical_analyzer = None
order_manager = None
order_callback_handler = None
callback = None
tushare_token = None
xt_trader = None
account = None

def setup_scheduler():
    scheduler.add_job(
        download_all_data,
        trigger=CronTrigger(day_of_week="0-4", hour=15, minute=40),
        id="morning_analysis",
        replace_existing=True
    )
    # 只添加任务，不再start调度器

def get_history_func(symbol, tushare_token=None):
    """用Tushare获取历史行情，返回DataFrame
    
    自动识别股票和指数，使用相应的API：
    - 股票：使用 daily API
    - 指数：使用 index_daily API
    
    优化策略：
    1. 只在交易时段（9:30-11:30, 13:00-15:00）调用Tushare API
    2. 缓存10分钟（从5分钟增加），减少重复查询
    3. 市场指数使用30分钟长缓存（趋势变化慢）
    4. 避免超出20000次/天的API限制
    """
    import logging
    from datetime import datetime, time, timedelta
    logger = logging.getLogger(__name__)
    
    # 判断是否为市场指数（趋势指标，可以用更长的缓存）
    # 注意：这里的指数列表必须与 auto_trader.py 中 judge_market_trend_comprehensive 函数使用的指数列表一致
    # 确保所有用于市场趋势判断的指数都使用长缓存（30分钟），避免频繁调用API
    market_indices = ['000001.SH', '399001.SZ', '399006.SZ', '000905.SH']  # 上证、深证、创业板、中证500
    is_market_index = symbol in market_indices
    
    # 1. 检查缓存（市场指数使用长缓存）
    if is_market_index:
        cache_key = f"market_{symbol}_{tushare_token}"
        cache_dict = market_trend_cache
        cache_expire = MARKET_TREND_CACHE_EXPIRE_SECONDS
    else:
        cache_key = f"{symbol}_{tushare_token}"
        cache_dict = history_data_cache
        cache_expire = CACHE_EXPIRE_SECONDS
    
    if cache_key in cache_dict:
        cached_data, cache_time = cache_dict[cache_key]
        # 检查缓存是否过期
        if (datetime.now() - cache_time).total_seconds() < cache_expire:
            logger.debug(f"[缓存命中] 使用缓存数据: {symbol}，缓存时间: {cache_time.strftime('%H:%M:%S')}，类型: {'市场指数' if is_market_index else '股票'}")
            return cached_data
        else:
            logger.debug(f"[缓存过期] 缓存已过期: {symbol}，过期时间: {(datetime.now() - cache_time).total_seconds():.0f}秒")
    
    # 2. 检查是否在交易时段（9:30-11:30, 13:00-15:00）
    current_time = datetime.now().time()
    trading_periods = [
        (time(9, 30), time(11, 30)),   # 上午交易时段
        (time(13, 0), time(15, 0))     # 下午交易时段
    ]
    
    is_in_trading_period = any(
        period_start <= current_time <= period_end 
        for period_start, period_end in trading_periods
    )
    
    if not is_in_trading_period:
        logger.debug(f"[API限流] 当前时间{current_time.strftime('%H:%M:%S')}不在交易时段，跳过Tushare API调用: {symbol}")
        # 如果有过期缓存，返回过期缓存（降级方案）
        if cache_key in cache_dict:
            cached_data, cache_time = cache_dict[cache_key]
            logger.info(f"[降级方案] 使用过期缓存数据: {symbol}，缓存时间: {cache_time.strftime('%H:%M:%S')}")
            return cached_data
        return None
    
    if tushare_token is None:
        logger.error(f"获取{symbol}历史行情失败: tushare_token未设置")
        return None
    
    pro = ts.pro_api(tushare_token)
    
    # 判断是股票还是指数
    # 常见指数代码：000001.SH(上证), 399001.SZ(深证), 399006.SZ(创业板), 000905.SH(中证500)
    # 指数代码特征：以399开头或000001/000905等特定代码
    is_index = (
        symbol.startswith('399') or  # 深证指数（399001, 399006等）
        symbol in ['000001.SH', '000905.SH', '000300.SH', '000016.SH', '000852.SH'] or  # 上证指数
        symbol.endswith('.SH') and symbol.startswith('000')  # 其他上证指数
    )
    
    try:
        # 计算合理的日期范围（至少获取250个交易日，约1年）
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=400)).strftime('%Y%m%d')  # 多取一些确保有足够数据
        
        logger.debug(f"[API调用] 获取{symbol}历史行情 ({'指数' if is_index else '股票'}): {start_date} 至 {end_date}")
        
        # 根据类型选择API
        if is_index:
            df = pro.index_daily(ts_code=symbol, start_date=start_date, end_date=end_date)
        else:
            df = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
        
        if df is None or df.empty:
            # 如果第一次尝试失败，可能是判断错误，尝试另一个API
            if is_index:
                logger.debug(f"指数API失败，尝试股票API: {symbol}")
                df = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            else:
                logger.debug(f"股票API失败，尝试指数API: {symbol}")
                df = pro.index_daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            
            if df is None or df.empty:
                logger.warning(f"获取{symbol}历史行情失败: Tushare返回空数据，代码: {symbol}")
                return None
        
        # 检查必需的列
        required_cols = ['trade_date', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"获取{symbol}历史行情失败: 缺少必需列 {missing_cols}，可用列: {df.columns.tolist()}")
            return None
        
        df = df.sort_values('trade_date')
        df['close'] = df['close'].astype(float)
        
        # 如果有volume列，也转换为float
        if 'volume' in df.columns:
            df['volume'] = df['volume'].astype(float)
        elif 'vol' in df.columns:
            # Tushare可能返回vol而不是volume
            df['volume'] = df['vol'].astype(float)
        
        # 3. 缓存数据（根据类型选择缓存字典）
        cache_dict[cache_key] = (df, datetime.now())
        logger.debug(f"[缓存更新] 成功获取并缓存{symbol}历史行情: {len(df)}条记录，日期范围: {df['trade_date'].min()} 至 {df['trade_date'].max()}，缓存时长: {cache_expire}秒")
        
        return df
    except Exception as e:
        logger.error(f"获取{symbol}历史行情失败: {e}", exc_info=True)
        # 如果API调用失败，尝试返回过期缓存（降级方案）
        if cache_key in cache_dict:
            cached_data, cache_time = cache_dict[cache_key]
            logger.warning(f"[降级方案] API调用失败，使用过期缓存数据: {symbol}，缓存时间: {cache_time.strftime('%H:%M:%S')}")
            return cached_data
        return None

def get_latest_price_func(
    symbol: str,
    xt_trader=None,
    *,
    force_refresh: bool = False,
    max_age_sec: float = 2.0,
):
    """获取最新价（实盘尽量实时）

    设计说明：
    - 之前逻辑是“缓存优先且永不过期”，会导致价格长期不刷新，进而盈亏百分比看起来不实时。
    - 现在改为带TTL缓存：默认缓存最多保留 max_age_sec 秒；超过则重新拉取 tick。
    - 对风控/卖出检查可传 force_refresh=True 强制走 tick。
    """
    try:
        now_ts = datetime.now().timestamp()
        cached = latest_price_cache.get(symbol)
        if not force_refresh and cached is not None:
            # 兼容旧格式：可能缓存的是 float，也可能是 (price, ts)
            if isinstance(cached, tuple) and len(cached) == 2:
                cached_price, cached_ts = cached
                if cached_price is not None and (now_ts - float(cached_ts)) <= float(max_age_sec):
                    return float(cached_price)
            else:
                # 旧缓存没有时间戳：不再无限期使用，视为过期，走实时tick刷新
                pass

        from xtquant import xtdata
        tick_info = xtdata.get_full_tick([symbol])
        if symbol in tick_info and 'lastPrice' in tick_info[symbol]:
            price = tick_info[symbol]['lastPrice']
            # 缓存为 (price, ts)
            latest_price_cache[symbol] = (price, now_ts)
            return price
    except Exception as e:
        print(f"xtdata获取{symbol}最新价失败: {e}")
        # 降级：tick失败时，如果有缓存（哪怕过期）也尽量返回，避免None导致策略整段跳过
        cached = latest_price_cache.get(symbol)
        if cached is None:
            return None
        if isinstance(cached, tuple) and len(cached) == 2:
            return cached[0]
        return cached

    return None


def get_optimized_buy_price(symbol: str, last_price: float, market_trend: str = 'neutral') -> float | None:
    """
    根据分时K线和VWAP判断当前是否处于局部高点，避免买在山峰。

    逻辑改为“分级处理”而不是一刀切：
    - bull：适度放宽乖离限制，允许强势突破但避免过热
    - neutral：保持中性阈值
    - bear：收紧乖离限制，尽量避免追高

    处理方式：
    - 轻微乖离：降低挂单价，不直接拦截
    - 中度乖离：继续压价，但允许试仓
    - 严重乖离/冲高回落：直接跳过买入

    Returns:
        float: 优化挂单价（低于现价，不在严重高点时）
        None:  当前处于严重高点，跳过买入，等待回调
    """
    try:
        from xtquant import xtdata
        import math

        # ========== 1. 获取分时1分钟K线（最近30根）及tick ==========
        bars = xtdata.get_market_data(
            field_list=['close', 'high', 'low', 'volume', 'amount'],
            stock_list=[symbol],
            period='1m',
            count=30,
        )

        closes = []
        bar_volumes = []
        bar_amounts = []
        if bars and 'close' in bars and symbol in bars['close']:
            raw_close  = bars['close'][symbol]
            raw_volume = bars.get('volume', {}).get(symbol, [])
            raw_amount = bars.get('amount', {}).get(symbol, [])
            for i, v in enumerate(raw_close):
                if v is not None and float(v) > 0:
                    closes.append(float(v))
                    vol = float(raw_volume[i]) if i < len(raw_volume) and raw_volume[i] else 0
                    amt = float(raw_amount[i]) if i < len(raw_amount) and raw_amount[i] else 0
                    bar_volumes.append(vol)
                    bar_amounts.append(amt)

        # 数据不足时降级：只用tick判断
        if len(closes) < 6:
            logger.debug(f"[分时高点] {symbol}: 分时K线不足（{len(closes)}根），跳过高点判断")
            closes = []

        # ========== 2. 计算VWAP（成交量加权均价） ==========
        # 优先用tick的全天累计VWAP（更准确），降级用分时K线VWAP
        tick_info = xtdata.get_full_tick([symbol])
        tick = tick_info.get(symbol) if tick_info else None

        bid1 = last_price
        tick_vwap = None
        if tick:
            bid_prices = tick.get('bidPrice', [])
            if bid_prices and float(bid_prices[0]) > 0:
                bid1 = float(bid_prices[0])
            t_amount = float(tick.get('amount', 0) or 0)   # 单位：元
            t_volume = float(tick.get('volume', 0) or 0)   # 单位：手（xtquant tick的volume为手）
            # xtquant get_full_tick 的 volume 单位是手（100股），amount 单位是元
            # VWAP = amount / (volume * 100)，换算为元/股
            t_volume_shares = t_volume * 100
            if t_volume_shares > 0 and t_amount > 0:
                tick_vwap = t_amount / t_volume_shares

        bar_vwap = None
        if closes and sum(bar_volumes) > 0:
            total_amt = sum(bar_amounts)
            total_vol = sum(bar_volumes)
            if total_vol > 0 and total_amt > 0:
                bar_vwap = total_amt / total_vol

        # 最终VWAP：优先tick全天VWAP，降级K线VWAP，兜底用现价
        vwap = tick_vwap or bar_vwap or last_price

        # ========== 3. 四重高点判断 ==========
        is_peak = False
        peak_reason = ""

        # 动态乖离阈值：按市场状态调整
        trend_cfg = MARKET_TIMING_CONFIG.get('market_aggressiveness', {})
        market_trend_label = (market_trend or 'neutral').lower()
        if market_trend_label == 'bull':
            vwap_threshold = 2.0
            deviation_threshold = 2.5
            rise_threshold = 1.6
        elif market_trend_label == 'bear':
            vwap_threshold = 0.8
            deviation_threshold = 1.0
            rise_threshold = 0.8
        else:
            vwap_threshold = 1.2
            deviation_threshold = 1.5
            rise_threshold = 1.0

        # 条件A：当前价显著高于VWAP（偏离当日成交重心）
        vwap_dev_pct = (last_price - vwap) / vwap * 100 if vwap > 0 else 0
        light_vwap_overshoot = vwap_dev_pct > vwap_threshold and vwap_dev_pct <= vwap_threshold + 0.8
        severe_vwap_overshoot = vwap_dev_pct > vwap_threshold + 0.8
        if severe_vwap_overshoot:
            is_peak = True
            peak_reason = (
                f"价格显著高于VWAP（当前{last_price:.2f} vs VWAP{vwap:.2f}，"
                f"乖离{vwap_dev_pct:.2f}%，阈值{vwap_threshold}%）"
            )

        if not is_peak and closes:
            # 取最近20根和最近5根
            recent20 = closes[-20:] if len(closes) >= 20 else closes
            recent5  = closes[-5:]  if len(closes) >= 5  else closes

            avg20  = sum(recent20) / len(recent20)   # 近20根均价
            high20 = max(recent20)                   # 近20根最高价

            # 当前价相对近20根均价的乖离率
            deviation_pct = (last_price - avg20) / avg20 * 100

            # 近5根K线的涨幅（从5根前到现在）
            rise_5bar_pct = (last_price - recent5[0]) / recent5[0] * 100 if recent5[0] > 0 else 0

            # 条件B：乖离率过大（当前价显著高于近期均价）
            if deviation_pct > deviation_threshold + (0.8 if market_trend_label == 'bull' else 0.5):
                is_peak = True
                peak_reason = (
                    f"价格乖离均价过大（当前{last_price:.2f} vs 近20根均价{avg20:.2f}，"
                    f"乖离{deviation_pct:.2f}%，阈值{deviation_threshold}%）"
                )

            # 条件C：近5根快速拉升且价格高于均价（正处于拉升中的高点）
            if not is_peak and rise_5bar_pct > rise_threshold and last_price > avg20:
                # bull 市场允许更强势的突破，但 bear/neutral 更严格
                if not (market_trend_label == 'bull' and rise_5bar_pct <= rise_threshold + 1.2 and deviation_pct <= deviation_threshold + 1.0):
                    is_peak = True
                    peak_reason = (
                        f"近5根K线快速拉升（涨幅{rise_5bar_pct:.2f}%，阈值{rise_threshold}%），"
                        f"且价格{last_price:.2f}高于近期均价{avg20:.2f}"
                    )

            # 条件D：V形拉升顶部（创近20根新高，且5根前价格低于均价）
            price_5bar_ago = recent5[0] if recent5 else last_price
            was_below_avg = price_5bar_ago < avg20  # 5根前处于均价以下
            is_new_high = last_price >= high20 * 0.998  # 接近或创近期新高（0.2%容差）
            if not is_peak and is_new_high and was_below_avg:
                # bull 市场放宽，neutral/bear 保守
                if market_trend_label == 'bull' and deviation_pct <= deviation_threshold + 1.0 and rise_5bar_pct <= rise_threshold + 1.0:
                    pass
                else:
                    is_peak = True
                    peak_reason = (
                        f"V形拉升顶部（5根前价格{price_5bar_ago:.2f}<均价{avg20:.2f}，"
                        f"当前{last_price:.2f}接近近20根最高价{high20:.2f}）"
                    )

        if is_peak:
            logger.warning(f"[分时高点] {symbol}: 暂不买入，等待回调。原因: {peak_reason}")
            print(f"[分时高点] {symbol}: 当前价={last_price:.2f}，处于分时高点，暂不买入。\n  原因: {peak_reason}")
            return None

        # 轻微乖离：不拦截，只压价
        if light_vwap_overshoot:
            logger.info(
                f"[分时高点] {symbol}: 轻微高于VWAP({vwap_dev_pct:.2f}% > {vwap_threshold:.2f}%)，"
                f"不拦截买入，仅降低挂单价"
            )

        # ========== 4. 不在高点：根据VWAP位置计算优化挂单价 ==========
        is_below_vwap = last_price < vwap

        # 综合买一价和VWAP，取较低者
        base_price = bid1 if bid1 <= vwap else (bid1 + vwap) / 2

        if is_below_vwap:
            # 处于低位（价格低于VWAP）：折扣更小，减少错过机会（最大 -0.3%）
            min_price = round(last_price * 0.997, 2)
            position_label = "低位"
        else:
            # 中位（未触发高点但价格高于VWAP）：给更大折扣（最大 -0.5%）
            min_price = round(last_price * 0.995, 2)
            position_label = "中位"

        optimized = max(min_price, min(base_price, last_price))
        optimized = math.floor(optimized * 100) / 100
        if optimized < min_price:
            optimized = min_price

        logger.info(
            f"[优化挂单价] {symbol}: 最新价={last_price:.2f}, VWAP={vwap:.2f}(乖离{vwap_dev_pct:.2f}%), "
            f"买一={bid1:.2f}, 位置={position_label}, 挂单价={optimized:.2f} ({(optimized/last_price-1)*100:.2f}%)"
        )
        return optimized

    except Exception as e:
        logger.warning(f"[优化挂单价] {symbol}: 计算失败({e})，使用最新价 {last_price:.2f}")
        return last_price


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
    """旧的独立买入口：默认关闭，避免绕过主交易风控链路。"""
    logger.warning("[自动买入] auto_select_and_buy 已禁用，请使用主交易风控链路进行买入")
    return

async def run_trader_system(path, account, environment='SIMULATION'):
    """多策略量化交易系统"""
    try:
        from utils.environment_manager import get_env_manager
        env_manager = get_env_manager()
        logger.info(f"正在启动多策略量化交易系统 ({environment})...")
        logger.info(f"环境信息: {env_manager.get_environment_name()}")
        logger.info(f"QMT路径: {path}")
        logger.info(f"账户: {account}")
        logger.info("数据下载调度器任务已添加")
        
        # 使用全局的 xt_trader 实例，而不是重新创建
        global xt_trader, order_manager, order_callback_handler, callback
        if xt_trader is None:
            logger.error("xt_trader 未初始化")
            raise Exception("xt_trader 未初始化")
        
        logger.info("使用全局 xt_trader 实例")
        # 启动自动买卖+持仓监控闭环任务（每60秒自动买卖+分析）
        async def create_and_record_order(symbol, side, price, quantity, account, user="system", **kwargs):
            # 透传 min_order_value/check_cash 等参数，便于策略层做资金与最低金额的强约束
            params = {
                "symbol": symbol,
                "side": side,
                "price": price,
                "quantity": quantity,
                "account": account,
                "user": user,
                **kwargs,
            }
            order = order_manager.create_order(**params)
            if order:
                order_callback_handler.record_order_params(order.order_id, params)
            return order
        from modules.tornadoapp.auto_trader import monitor_positions_and_trade_multi_strategy
        asyncio.create_task(
            monitor_positions_and_trade_multi_strategy(
                stock_selector,
                xt_trader,
                account,
                position_analyzer,
                technical_analyzer,
                lambda symbol: get_history_func(symbol, tushare_token),
                # 透传关键字参数：支持 force_refresh/max_age_sec，用于实盘风控/卖出检查强制刷新行情
                lambda symbol, **kwargs: get_latest_price_func(symbol, xt_trader, **kwargs),
                create_and_record_order,  # 直接传递async下单函数
                interval=60,  # 保持60秒间隔，不影响交易响应速度
                max_stocks=None,  # 由DynamicPositionManager根据资金体量自动计算
                get_optimized_buy_price_func=get_optimized_buy_price,  # 分时优化挂单价
                environment=environment,  # 传入运行环境，模拟盘全天可买入
                order_manager_instance=order_manager,  # 传入OrderManager实例，用于极端行情撤单
            )
        )

        # await run_tornado_server()
        # 保活由main_async统一管理
    except Exception as e:
        logger.error(f"多策略量化交易系统启动失败: {e}")
        raise

async def trader_thread_func(path, account, environment):
    await run_trader_system(path, account, environment)



async def main_async():
    """主函数：启动多策略量化交易平台"""
    # 默认使用模拟环境
    environment = 'SIMULATION'
    # environment = 'PRODUCTION'
    logger.info(f"程序启动中... 环境: {environment}")
    global stock_selector, position_analyzer, technical_analyzer, order_manager, order_callback_handler, callback, tushare_token, xt_trader, account
    # --- 启动全局调度器（只启动一次） ---
    setup_scheduler()  # 只添加任务
    scheduler.start()
    logger.info("APScheduler全局调度器已启动")
    # --- 初始化数据库 ---
    await init_beanie()
    logger.info("数据库初始化完成")
    # --- 启动自动化任务 ---
    await run_tornado_server()
    # --- 初始化XtQuantTrader ---
    path, account_id = await get_config(environment)
    account = StockAccount(account_id, 'STOCK')
    session_id = 123456
    from utils.callback import OrderCallbackHandler, MyXtQuantTraderCallback
    risk_manager = RiskManager()
    compliance_manager = ComplianceManager()
    audit_logger = AuditLogger()
    
    # 初始化全局 xt_trader 实例
    xt_trader = XtQuantTrader(path, session_id)
    # 10万以下的小额卖单：不启用“超时撤单重卖”，避免出现“两笔委托”带来的额外手续费
    order_manager = OrderManager(
        xt_trader,
        risk_manager,
        compliance_manager,
        audit_logger,
        sell_resell_min_value=100000.0,
    )
    order_callback_handler = OrderCallbackHandler(order_manager)
    callback = MyXtQuantTraderCallback(order_manager, order_callback_handler)
    xt_trader.register_callback(callback)
    
    # 启动交易连接
    xt_trader.start()
    res = xt_trader.connect()
    if res != 0:
        import sys
        sys.exit("链接失败")
    subscribe_result = xt_trader.subscribe(account=account,)
    if subscribe_result != 0:
        print("账号订阅失败")
    
    # 初始化其他组件
    env_manager = get_env_manager()
    tushare_token = env_manager.get_tushare_token()
    stock_selector = StockSelector(tushare_token=tushare_token)
    position_analyzer = PositionAnalyzer(tushare_token)
    technical_analyzer = TechnicalAnalyzer()
    
    # 只启动一次交易系统（包含自动交易任务）
    asyncio.create_task(trader_thread_func(path, account, environment))
    
    # 启动QMT交易连接的消息循环（在独立线程中）
    def run_xt_trader_forever():
        try:
            logger.info("QMT交易连接消息循环启动中...")
            xt_trader.run_forever()
        except KeyboardInterrupt:
            logger.info("QMT交易连接被用户中断")
        except Exception as e:
            logger.error(f"QMT交易连接异常: {e}")
            import traceback
            traceback.print_exc()
    
    xt_thread = threading.Thread(target=run_xt_trader_forever, daemon=True, name="QMT-Trader-Thread")
    xt_thread.start()
    logger.info("QMT交易连接消息循环已启动")
    
    # 优雅保活，主事件循环不退出
    try:
        await asyncio.Event().wait()
    finally:
        try:
            if scheduler.running:
                scheduler.shutdown()
                logger.info("调度器已关闭")
        except Exception as e:
            logger.error(f"调度器关闭失败: {e}")

if __name__ == "__main__":
    asyncio.run(main_async())

