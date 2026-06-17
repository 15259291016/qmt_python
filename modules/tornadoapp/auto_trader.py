import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, time

from xtquant.xttype import StockAccount
from modules.stock_selector.selector import StockSelector
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer
from utils.date_util import is_trading_time
from modules.tornadoapp.risk.risk_manager import RiskManager
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
from modules.tornadoapp.audit.audit_logger import AuditLogger
from .wencai_info import async_select_stocks_by_wencai
from modules.market_timing.config import MARKET_BREADTH_CONFIG, STOCK_RANKING_CONFIG, MARKET_TIMING_CONFIG

try:
    # 统一的交易事件记录（写入 Excel），用于事后复盘
    from .trade_event_recorder import record_trade_event
except Exception:
    # 如果导入失败（例如未安装依赖），提供一个空实现，不影响主流程
    def record_trade_event(*args, **kwargs):  # type: ignore[no-redef]
        return None

# 配置日志
logger = logging.getLogger(__name__)
# 假设你有如下实例
# xt_trader: QMT交易API实例
# account: QMT账户
# latest_price_cache: 实时行情缓存

# 全局行情缓存
latest_price_cache = {}

# 全局：追踪止盈（持仓后的最高价/最高盈利）
# 说明：用于“等到冲高后回撤再卖”的移动止盈逻辑（不等于固定止盈线）。
# key: symbol, value: {"peak_price": float, "peak_pnl_pct": float, "updated_at": datetime}
position_peak_cache: Dict[str, Dict[str, Any]] = {}

# 全局：股票池缓存（跨轮询复用，避免极端行情下反复买入）
_stock_pool_cache: Dict[str, Any] = {
    'date': '',
    'stocks': [],
    'pending_stocks': [],
    'frozen_until': None,
    'freeze_reason': '',
}

# 全局：市场广度触发统计（按交易日）
_breadth_report_cache: Dict[str, Any] = {
    'date': '',
    'trigger_count': 0,
    'trigger_times': [],
    'last_trigger_key': '',
    'first_trigger_time': None,
    'baseline_asset': None,
    'max_asset_after_trigger': None,
    'min_asset_after_trigger': None,
    'last_asset': None,
    'last_report_time': None,
}


def _is_extreme_market(get_history_func, index_code: str = '000001.SH') -> Dict[str, Any]:
    """
    检测当日市场是否处于极端波动状态。
    满足任一条件即为极端行情：
    A. 当日振幅 > 3%
    B. 当日涨跌幅绝对值 > 2%
    C. 当前价距当日最高价回撤 > 1.5%
    """
    try:
        from xtquant import xtdata
        tick_info = xtdata.get_full_tick([index_code])
        tick = tick_info.get(index_code) if tick_info else None
        if tick is None:
            return {'is_extreme': False, 'reason': '无法获取指数tick数据', 'amplitude_pct': 0, 'change_pct': 0, 'drawdown_from_high': 0}

        last_price  = float(tick.get('lastPrice', 0) or 0)
        high_price  = float(tick.get('high', 0) or 0)
        low_price   = float(tick.get('low', 0) or 0)
        prev_close  = float(tick.get('lastClose', 0) or 0)

        if prev_close <= 0 or last_price <= 0:
            return {'is_extreme': False, 'reason': '指数价格数据异常', 'amplitude_pct': 0, 'change_pct': 0, 'drawdown_from_high': 0}

        amplitude_pct = (high_price - low_price) / prev_close * 100 if high_price > low_price else 0.0
        change_pct = (last_price - prev_close) / prev_close * 100
        drawdown_from_high = (last_price - high_price) / high_price * 100 if high_price > 0 else 0.0

        if amplitude_pct > 3.0:
            return {'is_extreme': True, 'reason': f'当日振幅过大（{amplitude_pct:.2f}% > 3.0%），市场剧烈震荡，暂缓买入',
                    'amplitude_pct': amplitude_pct, 'change_pct': change_pct, 'drawdown_from_high': drawdown_from_high}
        if abs(change_pct) > 2.0:
            direction = '快速拉升' if change_pct > 0 else '快速下跌'
            return {'is_extreme': True, 'reason': f'指数{direction}（涨跌幅{change_pct:.2f}%，绝对值 > 2.0%），暂缓买入',
                    'amplitude_pct': amplitude_pct, 'change_pct': change_pct, 'drawdown_from_high': drawdown_from_high}
        if drawdown_from_high < -1.5:
            return {'is_extreme': True, 'reason': f'指数冲高回落（距当日最高价回撤{drawdown_from_high:.2f}% < -1.5%），暂缓买入',
                    'amplitude_pct': amplitude_pct, 'change_pct': change_pct, 'drawdown_from_high': drawdown_from_high}

        return {'is_extreme': False, 'reason': '', 'amplitude_pct': amplitude_pct, 'change_pct': change_pct, 'drawdown_from_high': drawdown_from_high}
    except Exception as e:
        logger.warning(f'[极端行情检测] 检测失败: {e}，默认不冻结')
        return {'is_extreme': False, 'reason': str(e), 'amplitude_pct': 0, 'change_pct': 0, 'drawdown_from_high': 0}


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
        # 止盈止损（实盘严格止损-3%）
        if avg_price and current_price:
            pnl = (current_price - avg_price) / avg_price * 100
            if pnl > 10 or pnl < -3:  # 修复：止损从-5%改为-3%
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

def _validate_data_quality(df, min_length: int = 60) -> Dict[str, Any]:
    """
    验证数据质量
    
    Returns:
        {'valid': bool, 'issues': List[str], 'quality_score': float}
    """
    issues = []
    quality_score = 1.0
    
    if df is None:
        return {'valid': False, 'issues': ['数据为空'], 'quality_score': 0.0}
    
    if len(df) < min_length:
        issues.append(f'数据长度不足：{len(df)} < {min_length}')
        quality_score -= 0.5
    
    # 检查缺失值
    missing_cols = df.isnull().any()
    if missing_cols.any():
        missing_list = missing_cols[missing_cols].index.tolist()
        issues.append(f'存在缺失值：{missing_list}')
        quality_score -= 0.2
    
    # 检查异常值（价格不能为负或0）
    if 'close' in df.columns:
        if (df['close'] <= 0).any():
            issues.append('存在异常价格（<=0）')
            quality_score -= 0.3
    
    # 检查成交量异常
    if 'volume' in df.columns:
        if (df['volume'] < 0).any():
            issues.append('存在异常成交量（<0）')
            quality_score -= 0.2
    
    quality_score = max(0.0, quality_score)
    return {
        'valid': quality_score >= 0.5,
        'issues': issues,
        'quality_score': quality_score
    }


def _calculate_ma_indicators(df, periods: List[int] = [5, 20, 60]) -> Dict[str, Any]:
    """
    计算均线指标（增强版：包含斜率、距离、交叉信号）
    """
    if df is None or len(df) < max(periods):
        return None
    
    indicators = {}
    closes = df['close']
    
    # 计算各周期均线
    for period in periods:
        ma = closes.rolling(window=period).mean()
        indicators[f'ma{period}'] = {
            'value': float(ma.iloc[-1]),
            'slope': float(ma.iloc[-1] - ma.iloc[-2]) if len(ma) >= 2 else 0.0,  # 斜率
            'distance_to_price': float((closes.iloc[-1] - ma.iloc[-1]) / ma.iloc[-1] * 100)  # 乖离率
        }
    
    # 检测均线交叉信号
    ma5 = closes.rolling(window=5).mean()
    ma20 = closes.rolling(window=20).mean()
    ma60 = closes.rolling(window=60).mean()
    
    # 金叉/死叉检测（最近5个交易日）
    cross_signals = []
    for i in range(-5, 0):
        if i == -5:
            continue
        # MA5与MA20交叉
        if ma5.iloc[i-1] <= ma20.iloc[i-1] and ma5.iloc[i] > ma20.iloc[i]:
            cross_signals.append({'type': 'golden_cross_5_20', 'day': i})
        elif ma5.iloc[i-1] >= ma20.iloc[i-1] and ma5.iloc[i] < ma20.iloc[i]:
            cross_signals.append({'type': 'death_cross_5_20', 'day': i})
        
        # MA20与MA60交叉
        if ma20.iloc[i-1] <= ma60.iloc[i-1] and ma20.iloc[i] > ma60.iloc[i]:
            cross_signals.append({'type': 'golden_cross_20_60', 'day': i})
        elif ma20.iloc[i-1] >= ma60.iloc[i-1] and ma20.iloc[i] < ma60.iloc[i]:
            cross_signals.append({'type': 'death_cross_20_60', 'day': i})
    
    indicators['cross_signals'] = cross_signals
    return indicators


def _calculate_multi_period_returns(df) -> Dict[str, float]:
    """计算多周期涨跌幅"""
    if df is None or len(df) < 120:
        return {}
    
    closes = df['close']
    returns = {}
    
    periods = [5, 20, 60, 120]
    for period in periods:
        if len(df) >= period:
            pct = (closes.iloc[-1] / closes.iloc[-period] - 1) * 100
            returns[f'pct_{period}d'] = float(pct)
    
    return returns



def _rank_candidate_stocks(selected: List[Dict[str, Any]], get_history_func, market_trend: Optional[Dict[str, Any]] = None, top_n: Optional[int] = None) -> List[Dict[str, Any]]:
    """对问财候选进行二次打分并返回Top-N"""
    if top_n is None:
        top_n = int(STOCK_RANKING_CONFIG.get('top_n', 3))

    scored = []
    for stock in selected:
        ts_code = stock.get('ts_code')
        if not ts_code:
            continue
        score_info = _score_candidate_stock(ts_code, get_history_func, market_trend=market_trend)
        merged = {**stock, **score_info}
        scored.append(merged)

    scored.sort(key=lambda x: x.get('total_score', 0.0), reverse=True)

    # 过滤最低标准，避免弱票进入
    min_total_score = float(STOCK_RANKING_CONFIG.get('min_total_score', 70.0))
    min_trend_score = float(STOCK_RANKING_CONFIG.get('min_trend_score', 60.0))
    min_volume_score = float(STOCK_RANKING_CONFIG.get('min_volume_score', 50.0))

    filtered = [
        s for s in scored
        if s.get('total_score', 0.0) >= min_total_score
        and s.get('trend_score', 0.0) >= min_trend_score
        and s.get('volume_score', 0.0) >= min_volume_score
    ]
    final_list = filtered[:top_n] if filtered else scored[:top_n]

    if scored:
        logger.info("[候选排序] 二次评分明细（Top10）: " + " | ".join([
            f"{s.get('name', s.get('symbol', 'N/A'))}({s.get('ts_code', s.get('symbol', 'N/A'))})="
            f"{s.get('total_score', 0):.1f}[趋{s.get('trend_score', 0):.0f}/量{s.get('volume_score', 0):.0f}/"
            f"强{s.get('rs_score', 0):.0f}/回{s.get('risk_score', 0):.0f}/流{s.get('liquidity_score', 0):.0f}]"
            for s in scored[:10]
        ]))

    return final_list


def judge_market_trend_comprehensive(
    get_history_func,
    position_analyzer: PositionAnalyzer,
    fear_greed_index: float,
    long_term_fear_greed_index: float,
    market_breadth: Optional[Dict[str, Any]] = None,
    index_codes: Optional[List[str]] = None  # 多指数列表
) -> Dict[str, Any]:
    """
    综合判断市场趋势（牛市/熊市/震荡市）- 增强版
    
    优化点：
    1. 多指数综合判断（上证、深证、创业板、中证500）
    2. 成交量结合价格方向（放量上涨/下跌）
    3. 数据质量验证
    4. 均线系统增强（斜率、距离、交叉信号）
    5. 多时间窗口（5日、20日、60日、120日）
    6. 恐贪指数优化（加权平均、背离检测）
    
    结合多个维度：
    1. 多指数均线系统（权重35%）
    2. 恐贪指数（权重30%）
    3. 多周期涨跌幅（权重20%）
    4. 成交量+价格方向（权重15%）
    5. 市场广度（上涨家数占比，权重20%，用于修正结构性行情）
    
    Args:
        get_history_func: 获取历史数据的函数
        position_analyzer: 持仓分析器
        fear_greed_index: 当日恐贪指数
        long_term_fear_greed_index: 长期恐贪指数
        index_codes: 指数代码列表，默认['000001.SH', '399001.SZ', '399006.SZ', '000905.SH']
                    (上证、深证、创业板、中证500)
    
    Returns:
        {
            'trend': 'bull'/'bear'/'neutral',  # 市场趋势
            'confidence': 0.0-1.0,  # 置信度
            'score': -1.0到1.0,  # 综合得分（正数偏向牛市，负数偏向熊市）
            'factors': {...}  # 各因素得分详情
        }
    """
    if index_codes is None:
        index_codes = ['000001.SH', '399001.SZ', '399006.SZ', '000905.SH']  # 上证、深证、创业板、中证500
    
    factors = {}
    scores = []
    
    try:
        # ========== 1. 多指数均线系统（权重35%） ==========
        index_ma_scores = []
        index_ma_details = {}
        
        for idx_code in index_codes:
            try:
                logger.debug(f"[市场趋势] 开始获取指数 {idx_code} 的历史数据...")
                df = get_history_func(idx_code)
                
                # 检查数据是否为空或None
                if df is None:
                    logger.warning(f"[市场趋势] 指数 {idx_code} 数据获取失败：get_history_func返回None")
                    continue
                
                if df.empty:
                    logger.warning(f"[市场趋势] 指数 {idx_code} 数据获取失败：返回空DataFrame")
                    continue
                
                # 检查必需的列
                required_cols = ['close', 'volume']
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    logger.warning(f"[市场趋势] 指数 {idx_code} 缺少必需列: {missing_cols}，可用列: {df.columns.tolist()}")
                    continue
                
                quality = _validate_data_quality(df, min_length=60)
                
                if not quality['valid']:
                    logger.warning(f"[市场趋势] 指数 {idx_code} 数据质量不足: {quality['issues']}，数据长度: {len(df)}")
                    continue
                
                # 计算增强均线指标
                ma_indicators = _calculate_ma_indicators(df)
                if ma_indicators is None:
                    continue
                
                ma5 = ma_indicators['ma5']['value']
                ma20 = ma_indicators['ma20']['value']
                ma60 = ma_indicators['ma60']['value']
                current_price = df['close'].iloc[-1]
                
                # 均线排列得分
                if ma5 > ma20 > ma60 and current_price > ma5:
                    ma_score = 1.0  # 强烈牛市信号
                elif ma5 < ma20 < ma60 and current_price < ma5:
                    ma_score = -1.0  # 强烈熊市信号
                elif ma5 > ma20 and current_price > ma20:
                    ma_score = 0.5  # 偏多
                elif ma5 < ma20 and current_price < ma20:
                    ma_score = -0.5  # 偏空
                else:
                    ma_score = 0.0  # 震荡
                
                # 考虑均线斜率（趋势强度）
                ma5_slope = ma_indicators['ma5']['slope']
                ma20_slope = ma_indicators['ma20']['slope']
                slope_bonus = 0.0
                if ma_score > 0 and ma5_slope > 0 and ma20_slope > 0:
                    slope_bonus = 0.2  # 上升趋势加强
                elif ma_score < 0 and ma5_slope < 0 and ma20_slope < 0:
                    slope_bonus = -0.2  # 下降趋势加强
                
                # 考虑交叉信号
                cross_bonus = 0.0
                for signal in ma_indicators.get('cross_signals', []):
                    if signal['type'].startswith('golden_cross'):
                        cross_bonus += 0.1
                    elif signal['type'].startswith('death_cross'):
                        cross_bonus -= 0.1
                
                final_score = ma_score + slope_bonus + cross_bonus
                final_score = max(-1.0, min(1.0, final_score))  # 限制在-1到1
                
                index_ma_scores.append(final_score)
                index_ma_details[idx_code] = {
                    'score': final_score,
                    'ma5': ma5,
                    'ma20': ma20,
                    'ma60': ma60,
                    'current_price': current_price,
                    'ma5_slope': ma5_slope,
                    'ma20_slope': ma20_slope,
                    'cross_signals': len(ma_indicators.get('cross_signals', [])),
                    'quality_score': quality['quality_score']
                }
            except Exception as e:
                logger.warning(f"[市场趋势] 处理指数 {idx_code} 失败: {e}", exc_info=True)
                continue
        
        if index_ma_scores:
            # 多指数平均得分（可考虑加权，这里简单平均）
            avg_ma_score = sum(index_ma_scores) / len(index_ma_scores)
            factors['ma_system'] = {
                'score': avg_ma_score,
                'index_count': len(index_ma_scores),
                'index_details': index_ma_details,
                'consensus': 'strong_bull' if avg_ma_score > 0.7 else 'bull' if avg_ma_score > 0.3 else 
                            'strong_bear' if avg_ma_score < -0.7 else 'bear' if avg_ma_score < -0.3 else 'neutral'
            }
            scores.append(avg_ma_score * 0.35)
            logger.debug(f"[市场趋势] 均线系统得分: {avg_ma_score:.3f} (权重35%), 指数数量: {len(index_ma_scores)}")
        else:
            factors['ma_system'] = {'score': 0.0, 'error': '所有指数数据不足'}
            logger.warning(f"[市场趋势] 均线系统: 所有指数数据获取失败，无法计算均线得分")
        
        # ========== 2. 恐贪指数（权重30%）- 优化版 ==========
        # 加权平均：当日0.6，长期0.4（更重视当日情绪）
        weighted_fear_greed = fear_greed_index * 0.6 + long_term_fear_greed_index * 0.4
        
        # 背离检测：当日与长期差异过大
        divergence = abs(fear_greed_index - long_term_fear_greed_index)
        is_divergence = divergence > 20  # 差异超过20点认为有背离
        
        if weighted_fear_greed > 70:
            fg_score = 1.0  # 强烈贪婪
        elif weighted_fear_greed < 30:
            fg_score = -1.0  # 强烈恐慌
        else:
            fg_score = (weighted_fear_greed - 50) / 50  # 归一化到-1到1
        
        # 背离调整：如果出现背离，降低置信度
        if is_divergence:
            if (fear_greed_index > 70 and long_term_fear_greed_index < 50) or \
               (fear_greed_index < 30 and long_term_fear_greed_index > 50):
                fg_score *= 0.7  # 降低得分权重
        
        factors['fear_greed'] = {
            'score': fg_score,
            'daily': fear_greed_index,
            'long_term': long_term_fear_greed_index,
            'weighted_avg': weighted_fear_greed,
            'divergence': divergence,
            'is_divergence': is_divergence
        }
        scores.append(fg_score * 0.3)
        logger.debug(f"[市场趋势] 恐贪指数得分: {fg_score:.3f} (权重30%), 当日={fear_greed_index:.1f}, 长期={long_term_fear_greed_index:.1f}, 加权={weighted_fear_greed:.1f}")
        
        # ========== 3. 多周期涨跌幅（权重20%） ==========
        # 使用主要指数（上证）计算多周期涨跌幅
        main_df = None
        for idx_code in index_codes:
            try:
                df = get_history_func(idx_code)
                
                # 检查数据是否为空或None
                if df is None or df.empty:
                    logger.debug(f"[市场趋势] 指数 {idx_code} 数据获取失败（多周期涨跌幅），尝试下一个指数")
                    continue
                
                # 检查必需的列
                if 'close' not in df.columns:
                    logger.debug(f"[市场趋势] 指数 {idx_code} 缺少close列（多周期涨跌幅），尝试下一个指数")
                    continue
                
                quality = _validate_data_quality(df, min_length=120)
                if quality['valid']:
                    main_df = df
                    logger.debug(f"[市场趋势] 使用指数 {idx_code} 计算多周期涨跌幅，数据长度: {len(df)}")
                    break
                else:
                    logger.debug(f"[市场趋势] 指数 {idx_code} 数据质量不足（多周期涨跌幅）: {quality['issues']}，数据长度: {len(df)}")
            except Exception as e:
                logger.debug(f"[市场趋势] 处理指数 {idx_code} 失败（多周期涨跌幅）: {e}")
                continue
        
        if main_df is not None:
            multi_returns = _calculate_multi_period_returns(main_df)
            
            if multi_returns:
                # 多周期综合得分（加权：短期权重更高）
                period_weights = {'pct_5d': 0.4, 'pct_20d': 0.3, 'pct_60d': 0.2, 'pct_120d': 0.1}
                weighted_return_score = 0.0
                total_weight = 0.0
                
                for period_key, weight in period_weights.items():
                    if period_key in multi_returns:
                        pct = multi_returns[period_key]
                        # 归一化得分
                        if period_key == 'pct_5d':
                            period_score = max(-1.0, min(1.0, pct / 3))  # 5日涨3%为满分
                        elif period_key == 'pct_20d':
                            period_score = max(-1.0, min(1.0, pct / 5))  # 20日涨5%为满分
                        elif period_key == 'pct_60d':
                            period_score = max(-1.0, min(1.0, pct / 10))  # 60日涨10%为满分
                        else:  # pct_120d
                            period_score = max(-1.0, min(1.0, pct / 15))  # 120日涨15%为满分
                        
                        weighted_return_score += period_score * weight
                        total_weight += weight
                
                if total_weight > 0:
                    final_return_score = weighted_return_score / total_weight
                else:
                    final_return_score = 0.0
                
                factors['index_return'] = {
                    'score': final_return_score,
                    'returns': multi_returns,
                    'consistency': 'high' if all(r > 0 for r in multi_returns.values()) or 
                                   all(r < 0 for r in multi_returns.values()) else 'low'
                }
                scores.append(final_return_score * 0.2)
                logger.debug(f"[市场趋势] 多周期涨跌幅得分: {final_return_score:.3f} (权重20%), 涨跌幅: {multi_returns}")
            else:
                factors['index_return'] = {'score': 0.0, 'error': '无法计算多周期涨跌幅'}
                logger.warning(f"[市场趋势] 多周期涨跌幅: 无法计算，multi_returns为空")
        else:
            factors['index_return'] = {'score': 0.0, 'error': '主要指数数据不足'}
            logger.warning(f"[市场趋势] 多周期涨跌幅: 主要指数数据不足，无法获取120日历史数据")
        
        # ========== 4. 成交量+价格方向（权重15%）- 优化版 ==========
        if main_df is not None and len(main_df) >= 20 and 'volume' in main_df.columns:
            # 成交量比率
            vol_ratio = main_df['volume'].iloc[-5:].mean() / main_df['volume'].iloc[-20:-5].mean()
            
            # 价格变化方向（最近5日）
            price_change_5d = (main_df['close'].iloc[-1] / main_df['close'].iloc[-5] - 1) * 100
            
            # 结合成交量和价格方向
            if vol_ratio > 1.2:  # 放量
                if price_change_5d > 2:  # 放量上涨
                    vol_score = 0.8  # 强烈牛市信号
                elif price_change_5d < -2:  # 放量下跌
                    vol_score = -0.8  # 强烈熊市信号
                else:  # 放量但价格变化不大
                    vol_score = 0.2 if price_change_5d > 0 else -0.2
            elif vol_ratio < 0.8:  # 缩量
                if price_change_5d > 1:  # 缩量上涨（可能反弹乏力）
                    vol_score = 0.1
                elif price_change_5d < -1:  # 缩量下跌（可能继续下跌）
                    vol_score = -0.5
                else:  # 缩量震荡
                    vol_score = -0.2
            else:  # 正常量
                vol_score = 0.1 if price_change_5d > 0 else -0.1
            
            factors['volume'] = {
                'score': vol_score,
                'volume_ratio': float(vol_ratio),
                'price_change_5d': float(price_change_5d),
                'signal': '放量上涨' if vol_ratio > 1.2 and price_change_5d > 2 else
                         '放量下跌' if vol_ratio > 1.2 and price_change_5d < -2 else
                         '缩量上涨' if vol_ratio < 0.8 and price_change_5d > 1 else
                         '缩量下跌' if vol_ratio < 0.8 and price_change_5d < -1 else '正常'
            }
            scores.append(vol_score * 0.15)
            logger.debug(f"[市场趋势] 成交量得分: {vol_score:.3f} (权重15%), 量比={vol_ratio:.2f}, 5日涨跌={price_change_5d:.2f}%")
        else:
            factors['volume'] = {'score': 0.0, 'error': '数据不足'}
            logger.warning(f"[市场趋势] 成交量: 数据不足，无法计算成交量指标")

        # ========== 5. 市场广度（权重20%） ==========
        breadth_score = 0.0
        if market_breadth is not None:
            up_ratio = float(market_breadth.get('up_ratio', 0.5) or 0.5)
            limit_spread_ratio = float(market_breadth.get('limit_spread_ratio', 0.0) or 0.0)
            breadth_weight = float(MARKET_BREADTH_CONFIG.get('breadth_weight', 0.20))

            # 上涨占比映射到[-1,1]，并叠加涨停跌停差修正
            up_ratio_component = max(-1.0, min(1.0, (up_ratio - 0.5) / 0.25))
            breadth_score = 0.8 * up_ratio_component + 0.2 * limit_spread_ratio
            breadth_score = max(-1.0, min(1.0, breadth_score))

            factors['market_breadth'] = {
                'score': breadth_score,
                'up_ratio': up_ratio,
                'up_count': int(market_breadth.get('up_count', 0) or 0),
                'down_count': int(market_breadth.get('down_count', 0) or 0),
                'total_count': int(market_breadth.get('total_count', 0) or 0),
                'limit_spread_ratio': limit_spread_ratio,
                'signal': 'broad_bull' if up_ratio >= 0.70 else 'broad_bear' if up_ratio <= 0.35 else 'mixed'
            }
            scores.append(breadth_score * breadth_weight)
            logger.info(
                f"[市场趋势] 市场广度得分: {breadth_score:.3f} (权重{breadth_weight:.2f}), "
                f"上涨占比={up_ratio:.2%}, 上涨家数={market_breadth.get('up_count', 0)}, "
                f"下跌家数={market_breadth.get('down_count', 0)}"
            )
        else:
            factors['market_breadth'] = {'score': 0.0, 'error': '广度数据不可用'}
            logger.warning("[市场趋势] 市场广度: 数据不可用，跳过广度修正")
        
        # ========== 综合得分 ==========
        # 如果所有因子都失败，至少使用恐贪指数作为降级方案
        if not scores and 'fear_greed' in factors:
            fear_greed_data = factors['fear_greed']
            if isinstance(fear_greed_data, dict) and 'score' in fear_greed_data:
                fg_score = fear_greed_data['score']
                scores.append(fg_score * 0.5)  # 降低权重，因为只有单一因子
                logger.warning(f"[市场趋势] 所有技术指标因子失败，仅使用恐贪指数作为降级方案: {fg_score:.3f}")
        
        total_score = sum(scores) if scores else 0.0
        confidence = min(abs(total_score), 1.0)
        
        # 如果得分来源单一（只有恐贪指数），降低置信度
        if len(scores) == 1:
            confidence *= 0.6  # 单一因子置信度降低
            logger.warning(f"[市场趋势] 仅有一个因子可用，置信度降低至 {confidence:.2f}")
        
        # 动态阈值：根据数据质量调整
        data_quality_avg = sum([f.get('quality_score', 1.0) for f in factors.values() 
                               if isinstance(f, dict) and 'quality_score' in f]) / max(1, len([f for f in factors.values() 
                               if isinstance(f, dict) and 'quality_score' in f]))
        
        # 数据质量高时使用标准阈值，质量低时放宽阈值
        # 如果数据质量很低，进一步放宽阈值，避免误判
        if data_quality_avg < 0.3:
            threshold = 0.15  # 数据质量很低时，使用更宽松的阈值
        elif data_quality_avg < 0.6:
            threshold = 0.2
        else:
            threshold = 0.3 if data_quality_avg > 0.8 else 0.25
        
        # 调试日志：输出各因子得分详情
        logger.debug(f"[市场趋势] 各因子得分详情:")
        logger.debug(f"  - scores列表: {scores}")
        logger.debug(f"  - scores数量: {len(scores)}")
        logger.debug(f"  - 总得分: {total_score}")
        logger.debug(f"  - 各因子详情: {factors}")
        logger.debug(f"  - 数据质量平均分: {data_quality_avg}")
        logger.debug(f"  - 使用的阈值: {threshold}")
        
        # 统计失败的因子数量
        failed_factors = [name for name, data in factors.items() 
                         if isinstance(data, dict) and 'error' in data]
        successful_factors = [name for name, data in factors.items() 
                             if isinstance(data, dict) and 'score' in data and 'error' not in data]
        
        # 如果得分接近0，输出警告
        if abs(total_score) < 0.01:
            logger.warning(f"[市场趋势] 综合得分接近0 ({total_score:.4f})，可能原因：")
            logger.warning(f"  - 成功的因子: {successful_factors} ({len(successful_factors)}个)")
            logger.warning(f"  - 失败的因子: {failed_factors} ({len(failed_factors)}个)")
            logger.warning(f"  - 各因子得分列表: {scores}")
            if not scores:
                logger.warning(f"  - scores列表为空，所有因子可能都失败了")
            else:
                for i, score in enumerate(scores):
                    logger.warning(f"  - 因子{i+1}得分: {score}")
            # 检查各因子是否有错误
            for factor_name in failed_factors:
                factor_data = factors[factor_name]
                logger.warning(f"  - {factor_name}因子错误: {factor_data.get('error', '未知错误')}")
        
        # 如果失败因子过多，给出建议
        if len(failed_factors) >= 2:
            logger.warning(f"[市场趋势] 警告：{len(failed_factors)}个因子失败，市场趋势判断可能不准确")
            logger.warning(f"  建议：检查Tushare Token和数据源连接")
        
        # 判断趋势
        if total_score > threshold:
            trend = 'bull'  # 牛市
        elif total_score < -threshold:
            trend = 'bear'  # 熊市
        else:
            trend = 'neutral'  # 震荡市

        # 置信度过低时降级为 neutral：
        # 置信度 < 0.35 说明各因子数据不足或分歧较大，
        # 此时不应该用低置信度的 bear 判断来禁止买入，应保守地视为震荡市。
        if confidence < 0.35 and trend == 'bear':
            logger.warning(
                f"[市场趋势] 置信度过低({confidence:.2f} < 0.35)，bear 判断不可靠，"
                f"降级为 neutral（得分={total_score:.3f}），避免错误禁止买入"
            )
            trend = 'neutral'
        
        # 生成描述信息（根据数据质量调整）
        base_descriptions = {
            'bull': '牛市：市场情绪乐观，多指数上涨，均线多头排列',
            'bear': '熊市：市场情绪悲观，多指数下跌，均线空头排列',
            'neutral': '震荡市：市场方向不明确，多空力量均衡'
        }
        
        description = base_descriptions[trend]
        if len(failed_factors) >= 2:
            description += f"（数据不足：{len(failed_factors)}个因子失败，判断准确性较低）"
        elif len(successful_factors) < 2:
            description += f"（数据部分可用：仅{len(successful_factors)}个因子成功）"
        
        return {
            'trend': trend,
            'confidence': confidence,
            'score': total_score,
            'threshold_used': threshold,
            'data_quality_avg': data_quality_avg,
            'factors': factors,
            'scores_detail': scores,  # 添加详细得分列表
            'successful_factors': successful_factors,
            'failed_factors': failed_factors,
            'description': description
        }
    except Exception as e:
        logger.error(f"判断市场趋势失败: {e}", exc_info=True)
        return {
            'trend': 'neutral',
            'confidence': 0.0,
            'score': 0.0,
            'factors': {},
            'error': str(e)
        }

# 添加多策略自动交易函数
async def monitor_positions_and_trade_multi_strategy(
    stock_selector: StockSelector,
    xt_trader,
    account: StockAccount,
    position_analyzer: PositionAnalyzer,
    technical_analyzer: TechnicalAnalyzer,
    get_history_func,
    get_latest_price_func,
    order_manager,
    interval: int = 60,
    max_stocks: int = None,  # 改为None，由DynamicPositionManager自动计算
    enable_market_timing: bool = True,  # 是否启用市场择时（默认启用）
    get_optimized_buy_price_func=None,  # 可选：优化挂单价函数，None时直接用最新价
    environment: str = 'SIMULATION',  # 运行环境：SIMULATION=模拟盘，PRODUCTION=实盘
    order_manager_instance=None,  # OrderManager实例，用于极端行情撤单等操作
):
    """
    多策略持仓监控+自动买卖任务（支持市场择时）。
    支持多个策略并行运行，每个策略可以管理不同的股票池。
    
    新增功能：
    - 市场择时：根据上证指数实时判断买入时机，只在市场出现买入信号时才执行选股买入
    - 卖出仍然实时监控（风险控制优先）
    
    Args:
        stock_selector: 选股器
        xt_trader: 交易接口
        account: 账户对象
        position_analyzer: 持仓分析器
        technical_analyzer: 技术分析器
        get_history_func: 获取历史数据函数
        get_latest_price_func: 获取最新价格函数
        order_manager: 订单管理器
        interval: 监控间隔（秒）
        max_stocks: 最大持股数量（默认None，由DynamicPositionManager根据资金体量自动计算）
        enable_market_timing: 是否启用市场择时（默认True）
    """
    from modules.strategy_manager.manager import StrategyManager
    from modules.strategy_manager.config import STRATEGY_CONFIG
    from modules.tornadoapp.position_manager import DynamicPositionManager
    # 修复：MarketTimingEngine 类不存在，暂时禁用市场择时功能
    # from modules.market_timing import MarketTimingEngine
    
    # 声明使用全局缓存（跨轮询复用）
    global _stock_pool_cache, _breadth_report_cache

    # 初始化策略管理器
    risk_manager = RiskManager()
    compliance_manager = ComplianceManager()
    audit_logger = AuditLogger()
    
    strategy_manager = StrategyManager(
        xt_trader=xt_trader,
        order_manager=order_manager,
        base_path="strategy_data"
    )
    
    # 初始化动态持仓管理器
    position_manager = DynamicPositionManager(xt_trader, account)
    logger.info("[资金管理] 动态持仓管理器已初始化")
    
    # 初始化市场择时引擎
    # 修复：MarketTimingEngine 类不存在，暂时禁用市场择时功能
    market_timing_engine = None
    if enable_market_timing:
        logger.warning("[市场择时] MarketTimingEngine 类不存在，已自动禁用市场择时功能，使用固定时间买入")
        enable_market_timing = False  # 强制禁用
    
        logger.info("[市场择时] 市场择时引擎已禁用，使用固定时间买入")
    
    # 添加账户
    strategy_manager.add_account("main_account", account)
    
    # 加载策略配置
    strategy_manager.load_strategies_from_config(STRATEGY_CONFIG)
    
    # 智能策略分配函数
    def assign_strategies_to_stocks(
        held_symbols: List[str], 
        fear_greed_index: float
    ) -> Dict[str, List[str]]:
        """
        根据市场情绪（恐贪指数）智能分配策略到持仓股票
        
        该函数根据恐贪指数（0-100）将持仓股票分配到不同的交易策略：
        - 恐慌市场（<20）: 使用保守策略组合，降低风险
        - 贪婪市场（>80）: 使用增强策略组合，追求更高收益
        - 正常市场（20-80）: 使用平衡策略组合，分散风险
        
        Args:
            held_symbols: 持仓股票代码列表，例如：['000001.SZ', '000002.SZ']
            fear_greed_index: 恐贪指数，范围0-100
                - 0-20: 恐慌市场
                - 20-80: 正常市场
                - 80-100: 贪婪市场
        
        Returns:
            Dict[str, List[str]]: 策略分配字典，键为策略名称，值为分配给该策略的股票代码列表
                例如：{
                    "byd_conservative": ["000001.SZ"],
                    "ma_15_60": ["000002.SZ"]
                }
        
        Example:
            >>> stocks = ['000001.SZ', '000002.SZ', '000003.SZ']
            >>> # 恐慌市场
            >>> result = assign_strategies_to_stocks(stocks, 15)
            >>> # 返回: {"byd_conservative": ["000001.SZ"], "ma_15_60": ["000002.SZ"]}
            >>> 
            >>> # 正常市场
            >>> result = assign_strategies_to_stocks(stocks, 50)
            >>> # 返回: {"ma_5_20": ["000001.SZ"], "ma_10_30": ["000002.SZ"], "byd_strategy": ["000003.SZ"]}
        """
        # 参数验证
        if not held_symbols:
            logger.debug("持仓股票列表为空，返回空分配")
            return {}
        
        if not isinstance(held_symbols, list):
            logger.warning(f"held_symbols 应为列表类型，当前类型: {type(held_symbols)}")
            return {}
        
        # 验证恐贪指数范围
        if fear_greed_index < 0 or fear_greed_index > 100:
            logger.warning(f"恐贪指数超出正常范围(0-100): {fear_greed_index}，使用默认值50")
            fear_greed_index = 50
        
        # 去重并过滤空值
        held_symbols = list(dict.fromkeys([s for s in held_symbols if s and isinstance(s, str)]))
        
        if not held_symbols:
            logger.debug("过滤后持仓股票列表为空")
            return {}
        
        stock_count = len(held_symbols)
        logger.info(f"开始策略分配: 股票数量={stock_count}, 恐贪指数={fear_greed_index:.1f}")
        
        # 根据恐贪指数调整策略分配
        if fear_greed_index < 20:  # 恐慌市场
            # 恐慌时使用保守策略：降低风险，使用长期均线和保守策略
            # byd_conservative: 保守比亚迪策略（止损2%，止盈10%）
            # ma_15_60: 15/60日均线策略（长期均线，更稳健）
            mid_point = stock_count // 2
            assignment = {
                "byd_conservative": held_symbols[:mid_point],
                "ma_15_60": held_symbols[mid_point:]
            }
            logger.info(f"[恐慌市场] 分配策略: byd_conservative({len(assignment['byd_conservative'])}只), "
                       f"ma_15_60({len(assignment['ma_15_60'])}只)")
            
        elif fear_greed_index > 80:  # 贪婪市场
            # 贪婪时使用增强策略：追求更高收益，使用短期均线和增强策略
            # byd_enhanced: 增强比亚迪策略（止损3%，止盈20%）
            # ma_5_20: 5/20日均线策略（短期均线，更敏感）
            mid_point = stock_count // 2
            assignment = {
                "byd_enhanced": held_symbols[:mid_point],
                "ma_5_20": held_symbols[mid_point:]
            }
            logger.info(f"[贪婪市场] 分配策略: byd_enhanced({len(assignment['byd_enhanced'])}只), "
                       f"ma_5_20({len(assignment['ma_5_20'])}只)")
            
        else:  # 正常市场 (20 <= fear_greed_index <= 80)
            # 正常市场使用平衡策略：分散风险，使用多种策略组合
            # ma_5_20: 短期均线策略（5/20日均线）
            # ma_10_30: 中期均线策略（10/30日均线）
            # byd_strategy: 标准比亚迪策略（止损5%，止盈15%）
            third_point = stock_count // 3
            two_thirds_point = 2 * stock_count // 3
            
            assignment = {
                "ma_5_20": held_symbols[:third_point],
                "ma_10_30": held_symbols[third_point:two_thirds_point],
                "byd_strategy": held_symbols[two_thirds_point:]
            }
            logger.info(f"[正常市场] 分配策略: ma_5_20({len(assignment['ma_5_20'])}只), "
                       f"ma_10_30({len(assignment['ma_10_30'])}只), "
                       f"byd_strategy({len(assignment['byd_strategy'])}只)")
        
        # 过滤空列表，只返回有股票的策略
        assignment = {k: v for k, v in assignment.items() if v}
        
        # 验证分配结果：确保所有股票都被分配
        assigned_stocks = set()
        for stocks in assignment.values():
            assigned_stocks.update(stocks)
        
        if len(assigned_stocks) != stock_count:
            missing = set(held_symbols) - assigned_stocks
            logger.warning(f"部分股票未被分配: {missing}")
            # 将未分配的股票添加到第一个策略
            if assignment:
                first_strategy = list(assignment.keys())[0]
                assignment[first_strategy].extend(missing)
                logger.info(f"将未分配股票添加到策略 {first_strategy}: {missing}")
        
        logger.info(f"策略分配完成: {len(assignment)}个策略，共{stock_count}只股票")
        return assignment
    
    # 启动所有策略
    strategy_manager.start_all_strategies()
    
    last_status = None
    while True:
        trading = is_trading_time()
        if not trading:
            if last_status and last_status != 'not_trading':
                print("[多策略自动交易] 当前非交易时间，等待...")
                last_status = 'not_trading'
            await asyncio.sleep(30)
            continue
        
        last_status = 'trading'
        try:
            # 获取最新持仓分析
            positions = xt_trader.query_stock_positions(account)
            # 过滤有效持仓：必须有stock_code和volume属性，且持仓数量大于0（剔除已卖出的股票）
            valid_positions = [
                p for p in positions 
                if hasattr(p, 'stock_code') 
                and hasattr(p, 'volume') 
                and p.volume > 0  # 剔除已卖出的股票（volume为0）
            ]
            
            # 持仓分析
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
            fear_greed_index = getattr(summary, 'fear_greed_index', None)
            long_term_fear_greed_index = getattr(summary, 'long_term_fear_greed_index', None)
            
            # 如果恐贪指数为None，使用默认值50，但记录警告
            if fear_greed_index is None:
                fear_greed_index = 50
                logger.warning(f"[恐贪指数] 当日恐贪指数为None，使用默认值50（可能数据获取失败）")
            if long_term_fear_greed_index is None:
                long_term_fear_greed_index = fear_greed_index if fear_greed_index is not None else 50
                logger.warning(f"[恐贪指数] 长期恐贪指数为None，使用当日值或默认值50")
            
            print(f"[恐贪指数] 当日: {fear_greed_index:.1f}，长期: {long_term_fear_greed_index:.1f}")
            
            # 综合判断市场趋势（牛市/熊市/震荡市）- 使用多指数综合判断
            market_breadth = position_analyzer.get_market_breadth_snapshot()
            market_trend = judge_market_trend_comprehensive(
                get_history_func=get_history_func,
                position_analyzer=position_analyzer,
                fear_greed_index=fear_greed_index,
                long_term_fear_greed_index=long_term_fear_greed_index,
                market_breadth=market_breadth,
                index_codes=['000001.SH', '399001.SZ', '399006.SZ', '000905.SH']  # 上证、深证、创业板、中证500
            )
            
            logger.info(f"[市场趋势] {market_trend['trend']} ({market_trend['description']})，"
                       f"置信度={market_trend['confidence']:.2f}，综合得分={market_trend['score']:.2f}")
            
            # 输出详细的因子得分信息
            if 'factors' in market_trend:
                factors_info = []
                for name, data in market_trend['factors'].items():
                    if isinstance(data, dict):
                        score = data.get('score', 0.0)
                        if 'error' in data:
                            factors_info.append(f"{name}: 错误({data['error']})")
                        else:
                            factors_info.append(f"{name}: {score:.3f}")
                if factors_info:
                    logger.info(f"[市场趋势] 各因子得分: {', '.join(factors_info)}")
                    print(f"[市场趋势] 各因子得分: {', '.join(factors_info)}")
            
            # 如果有错误，输出错误信息
            if 'error' in market_trend:
                logger.error(f"[市场趋势] 判断失败: {market_trend['error']}")
                print(f"[市场趋势] 判断失败: {market_trend['error']}")
            
            print(f"[市场趋势] {market_trend['trend']}，置信度={market_trend['confidence']:.2f}，得分={market_trend['score']:.2f}")
            
            # 根据市场趋势动态调整止盈阈值
            if market_trend['trend'] == 'bull':
                # 牛市：提高止盈阈值，让利润奔跑
                take_profit_threshold = 20.0  # 从15%提高到20%
                logger.info(f"[策略调整] 牛市环境，提高止盈阈值至{take_profit_threshold}%")
            elif market_trend['trend'] == 'bear':
                # 熊市：降低止盈阈值，及时落袋为安
                take_profit_threshold = 10.0  # 从15%降低到10%
                logger.info(f"[策略调整] 熊市环境，降低止盈阈值至{take_profit_threshold}%")
            else:
                # 震荡市：使用基础阈值
                take_profit_threshold = 15.0
                logger.info(f"[策略调整] 震荡市环境，使用基础止盈阈值{take_profit_threshold}%")
            
            # 将止盈阈值保存到market_trend中，供卖出逻辑使用
            market_trend['take_profit_threshold'] = take_profit_threshold
            
            # 智能策略分配：只包含实际持有的股票（已剔除已卖出的股票）
            held_symbols = [p.stock_code for p in valid_positions if p.volume > 0]
            strategy_assignments = assign_strategies_to_stocks(held_symbols, fear_greed_index)
            
            # 更新策略分配
            for strategy_name, symbols in strategy_assignments.items():
                if symbols:
                    strategy_manager.assign_strategy_to_account(strategy_name, "main_account", symbols)
                    print(f"[策略分配] {strategy_name} -> {symbols}")
            
            # 获取策略状态
            strategy_status = strategy_manager.get_strategy_status()
            # print(f"[策略状态] {strategy_status}")
            
            # 选股池自动买入（固定时间段精准买入）
            current_time = datetime.now().time()

            # 模拟盘与实盘使用相同的精准买入时间段
            is_simulation = (environment == 'SIMULATION')
            stock_selection_periods = [
                (time(9, 50), time(10, 15)),    # 上午：9:50-10:05（15分钟，开盘后观察期）
                (time(13, 40), time(13, 50)),  # 下午：13:40-13:50（10分钟，下午中段）
                (time(14, 20), time(14, 30))   # 尾盘：14:20-14:30（10分钟，尾盘前调仓）
            ]
            logger.debug(f"[买入时间] {'模拟盘' if is_simulation else '实盘'}模式，使用精准时间段买入")

            # 市场不好（熊市）且置信度较高时，过滤掉上午时间段，只保留下午时间段
            # 逻辑：只有明确的熊市信号（置信度>=0.35）才禁止上午买入，避免误判错过反弹
            # 震荡市（neutral）不限制上午买入，因为方向不明时更应该把握反弹机会
            market_confidence = market_trend.get('confidence', 0.0)
            breadth_info = market_trend.get('factors', {}).get('market_breadth', {})
            breadth_up_ratio = float(breadth_info.get('up_ratio', 0.0) or 0.0)
            morning_buy_override_up_ratio = float(MARKET_BREADTH_CONFIG.get('morning_buy_override_up_ratio', 0.70))
            breadth_override = (
                isinstance(breadth_info, dict)
                and 'error' not in breadth_info
                and breadth_up_ratio >= morning_buy_override_up_ratio
            )

            market_is_bad = (
                market_trend.get('trend') == 'bear'
                and market_confidence >= 0.35
                and not breadth_override
            )
            if market_is_bad:
                active_periods = [
                    p for p in stock_selection_periods
                    if p[0] >= time(13, 0)  # 只保留下午时间段
                ]
                if current_time < time(13, 0):
                    logger.info(
                        f"[市场择时] 明确熊市（得分={market_trend.get('score', 0):.2f}，置信度={market_confidence:.2f}），"
                        f"上午不买股票，等待下午13:40后再评估"
                    )
                    print(f"[市场择时] 明确熊市（置信度={market_confidence:.2f}），上午跳过买入，下午13:40后再评估")
            else:
                active_periods = stock_selection_periods
                if breadth_override and market_trend.get('trend') == 'bear':
                    logger.info(
                        f"[市场择时] 熊市信号但广度强（上涨占比={breadth_up_ratio:.2%}>="
                        f"{morning_buy_override_up_ratio:.0%}），放开上午买入窗口"
                    )
                    print(
                        f"[市场择时] 熊市但市场广度强（上涨占比={breadth_up_ratio:.2%}，"
                        f"阈值={morning_buy_override_up_ratio:.0%}），上午允许试仓"
                    )

                    # 记录“广度覆盖触发”统计（按分钟去重，防止60秒轮询重复计数）
                    trigger_key = datetime.now().strftime('%H:%M')
                    if _breadth_report_cache.get('last_trigger_key') != trigger_key:
                        _breadth_report_cache['last_trigger_key'] = trigger_key
                        _breadth_report_cache['trigger_count'] += 1
                        _breadth_report_cache['trigger_times'].append(datetime.now().strftime('%H:%M:%S'))
                        if _breadth_report_cache['first_trigger_time'] is None:
                            _breadth_report_cache['first_trigger_time'] = datetime.now().strftime('%H:%M:%S')

                        # 触发时记录资产基线（用于计算触发后收益和回撤）
                        try:
                            asset_snapshot = xt_trader.query_stock_asset(account)
                            baseline_asset = float(
                                getattr(asset_snapshot, 'total_asset', 0) or
                                getattr(asset_snapshot, 'totalAsset', 0) or
                                (getattr(asset_snapshot, 'cash', 0) or 0)
                            )
                            if baseline_asset > 0 and _breadth_report_cache['baseline_asset'] is None:
                                _breadth_report_cache['baseline_asset'] = baseline_asset
                                _breadth_report_cache['max_asset_after_trigger'] = baseline_asset
                                _breadth_report_cache['min_asset_after_trigger'] = baseline_asset
                                _breadth_report_cache['last_asset'] = baseline_asset
                                logger.info(
                                    f"[市场广度报告] 首次触发基线资产={baseline_asset:.2f}元，"
                                    f"触发时间={_breadth_report_cache['first_trigger_time']}"
                                )
                        except Exception as _asset_err:
                            logger.warning(f"[市场广度报告] 获取触发基线资产失败: {_asset_err}")
                elif market_trend.get('trend') == 'neutral':
                    logger.info(
                        f"[市场择时] 震荡市/低置信度（得分={market_trend.get('score', 0):.2f}，置信度={market_confidence:.2f}），"
                        f"不限制上午买入，正常执行选股"
                    )

            # 检查当前时间是否在有效时间段内
            is_stock_selection_time = any(
                period_start <= current_time <= period_end
                for period_start, period_end in active_periods
            )
            
            # ========== 买入时间判断 + 极端行情检测 ==========
            today_str = datetime.now().strftime('%Y-%m-%d')

            # 实时更新“广度覆盖触发”后的资产轨迹（用于收益/回撤统计）
            if _breadth_report_cache.get('baseline_asset') is not None:
                try:
                    asset_snapshot = xt_trader.query_stock_asset(account)
                    current_total_asset = float(
                        getattr(asset_snapshot, 'total_asset', 0) or
                        getattr(asset_snapshot, 'totalAsset', 0) or
                        (getattr(asset_snapshot, 'cash', 0) or 0)
                    )
                    if current_total_asset > 0:
                        _breadth_report_cache['last_asset'] = current_total_asset
                        prev_max = _breadth_report_cache.get('max_asset_after_trigger')
                        prev_min = _breadth_report_cache.get('min_asset_after_trigger')
                        _breadth_report_cache['max_asset_after_trigger'] = max(prev_max, current_total_asset) if prev_max is not None else current_total_asset
                        _breadth_report_cache['min_asset_after_trigger'] = min(prev_min, current_total_asset) if prev_min is not None else current_total_asset
                except Exception as _asset_track_err:
                    logger.debug(f"[市场广度报告] 更新资产轨迹失败: {_asset_track_err}")

            # 每日重置缓存
            if _stock_pool_cache['date'] != today_str:
                _stock_pool_cache['date'] = today_str
                _stock_pool_cache['stocks'] = []
                _stock_pool_cache['pending_stocks'] = []
                _stock_pool_cache['frozen_until'] = None
                _stock_pool_cache['freeze_reason'] = ''
                logger.info(f'[股票池缓存] 新的交易日({today_str})，已重置股票池缓存')

            # 每日重置“市场广度触发报告”缓存
            if _breadth_report_cache['date'] != today_str:
                _breadth_report_cache['date'] = today_str
                _breadth_report_cache['trigger_count'] = 0
                _breadth_report_cache['trigger_times'] = []
                _breadth_report_cache['last_trigger_key'] = ''
                _breadth_report_cache['first_trigger_time'] = None
                _breadth_report_cache['baseline_asset'] = None
                _breadth_report_cache['max_asset_after_trigger'] = None
                _breadth_report_cache['min_asset_after_trigger'] = None
                _breadth_report_cache['last_asset'] = None
                _breadth_report_cache['last_report_time'] = None
                logger.info(f'[市场广度报告] 新的交易日({today_str})，已重置广度触发统计')

            # 检测极端行情（每次循环都检测，实时感知市场状态）
            extreme_info = _is_extreme_market(get_history_func)
            now_dt = datetime.now()

            if extreme_info['is_extreme']:
                # 仅在当前未处于冻结期时才设置新的冻结时间，避免冻结时间被反复刷新延长
                already_frozen = (
                    _stock_pool_cache['frozen_until'] is not None
                    and now_dt < _stock_pool_cache['frozen_until']
                )
                if not already_frozen:
                    from datetime import timedelta
                    freeze_end = now_dt + timedelta(minutes=15)
                    _stock_pool_cache['frozen_until'] = freeze_end
                    _stock_pool_cache['freeze_reason'] = extreme_info['reason']
                    logger.warning(
                        f"[极端行情] 检测到极端行情，暂停买入15分钟（至{freeze_end.strftime('%H:%M:%S')}）。"
                        f"原因: {extreme_info['reason']} "
                        f"| 振幅={extreme_info['amplitude_pct']:.2f}% "
                        f"| 涨跌幅={extreme_info['change_pct']:.2f}% "
                        f"| 距高点回撤={extreme_info['drawdown_from_high']:.2f}%"
                    )
                    print(
                        f"[极端行情] {extreme_info['reason']}\n"
                        f"  振幅={extreme_info['amplitude_pct']:.2f}%  "
                        f"涨跌幅={extreme_info['change_pct']:.2f}%  "
                        f"距高点回撤={extreme_info['drawdown_from_high']:.2f}%\n"
                        f"  已选股票进入待买队列，冻结至 {freeze_end.strftime('%H:%M:%S')} 后重新评估"
                    )
                    # 撤销所有未成交的买入订单
                    if order_manager_instance is not None:
                        try:
                            cancelled = order_manager_instance.cancel_all_open_buy_orders(user="extreme_market")
                            if cancelled > 0:
                                logger.warning(f"[极端行情撤单] 已撤销{cancelled}笔未成交买入订单")
                                print(f"[极端行情撤单] 已撤销{cancelled}笔未成交买入订单")
                            else:
                                logger.info("[极端行情撤单] 当前无未成交买入订单需要撤销")
                        except Exception as _cancel_err:
                            logger.error(f"[极端行情撤单] 撤单失败: {_cancel_err}", exc_info=True)
                    else:
                        logger.warning("[极端行情撤单] order_manager_instance未传入，跳过撤单")

            # 判断当前是否处于冻结期
            is_frozen = (
                _stock_pool_cache['frozen_until'] is not None
                and now_dt < _stock_pool_cache['frozen_until']
            )
            if is_frozen:
                remaining = int((_stock_pool_cache['frozen_until'] - now_dt).total_seconds() / 60)
                logger.info(
                    f"[极端行情] 仍在冻结期，距解冻还有约{remaining}分钟。"
                    f"原因: {_stock_pool_cache['freeze_reason']}"
                )
                print(f"[极端行情] 买入已冻结，距解冻还有约{remaining}分钟")
            else:
                if _stock_pool_cache['frozen_until'] is not None:
                    logger.info(f'[极端行情] 冻结期结束，恢复买入评估')
                    _stock_pool_cache['frozen_until'] = None
                    _stock_pool_cache['freeze_reason'] = ''

            # 先计算当前仓位容量：无可用仓位时，不查询问财（限流）
            held = {p.stock_code for p in valid_positions}
            current_stock_count = len(held)
            position_params = position_manager.get_position_params(fear_greed_index)
            adjusted_max_stocks = position_params['max_stocks']

            # 买入容量检查：持股数量 + 现金双重限制
            has_slot_capacity = current_stock_count < adjusted_max_stocks
            min_position_value = float(position_params.get('min_position_value', 10000.0))
            available_cash_for_buy = 0.0
            try:
                asset_snapshot = xt_trader.query_stock_asset(account)
                available_cash_for_buy = float(
                    getattr(asset_snapshot, 'cash', 0)
                    or getattr(asset_snapshot, 'available_cash', 0)
                    or 0
                )
            except Exception as _asset_err:
                logger.warning(f"[资金管理] 获取可用资金失败，保守处理为无买入容量: {_asset_err}")
            has_cash_capacity = available_cash_for_buy >= min_position_value

            has_buy_capacity = has_slot_capacity and has_cash_capacity
            should_execute_buy = is_stock_selection_time and not is_frozen

            if should_execute_buy and has_buy_capacity:
                logger.info(
                    f"[固定时间买入] 当前时间{current_time.strftime('%H:%M:%S')}在买入时间段内且无冻结，"
                    f"有买入容量（持股{current_stock_count}/{adjusted_max_stocks}，可用资金={available_cash_for_buy:.2f}）"
                )
            elif should_execute_buy and not has_slot_capacity:
                logger.info(
                    f"[固定时间买入] 当前持股已满({current_stock_count}/{adjusted_max_stocks})，"
                    f"跳过问财查询以减少请求频率"
                )
            elif should_execute_buy and has_slot_capacity and not has_cash_capacity:
                logger.info(
                    f"[固定时间买入] 可用资金不足（可用={available_cash_for_buy:.2f} < 最小建仓={min_position_value:.2f}），"
                    f"跳过问财查询以减少无效请求"
                )
            elif is_frozen:
                logger.info(f"[固定时间买入] 当前时间{current_time.strftime('%H:%M:%S')}在买入时间段内，但处于极端行情冻结期，跳过选股")
            else:
                logger.debug(f"[固定时间买入] 当前时间{current_time.strftime('%H:%M:%S')}不在买入时间段内，跳过选股")

            # ========== 执行选股和买入 ==========
            selected = []  # 默认不选股
            if should_execute_buy and is_stock_selection_time and has_buy_capacity:
                # 确定当前在哪个时间段
                current_period = None
                for period_start, period_end in stock_selection_periods:
                    if period_start <= current_time <= period_end:
                        current_period = f"{period_start.strftime('%H:%M')}-{period_end.strftime('%H:%M')}"
                        break

                try:
                    # 每次都调用问财查询最新股票
                    # 但将结果合并到缓存股票池中（去重），避免遗漏之前选出但未买入的票
                    logger.info(f"[选股] 当前时间{current_time.strftime('%H:%M:%S')}在选股时间段内({current_period})，执行问财选股")
                    question_list = []
                    question_list.append("最近热点题材，突破十日均线，散户数量小于-100，剔除st，剔除退市警告股")

                    fresh_selected = await async_select_stocks_by_wencai(
                        question_list=question_list,
                        filter_by_retail_investor=True,
                        include_info=True
                    )
                    logger.info(f"[选股] 问财选股完成，本次新选出{len(fresh_selected)}只股票")

                    # 合并到缓存池（去重）：保留历史未买入的票 + 本次新选的票
                    cached_stocks = _stock_pool_cache.get('stocks', [])
                    cached_codes = {s.get('ts_code') for s in cached_stocks}
                    new_stocks = [s for s in fresh_selected if s.get('ts_code') not in cached_codes]
                    merged = cached_stocks + new_stocks
                    _stock_pool_cache['stocks'] = merged
                    _stock_pool_cache['date'] = today_str
                    _stock_pool_cache['last_period'] = current_period
                    selected = merged
                    if new_stocks:
                        logger.info(f"[股票池缓存] 新增{len(new_stocks)}只股票，缓存池共{len(merged)}只")
                    else:
                        logger.info(f"[股票池缓存] 本次无新增股票，缓存池共{len(merged)}只")

                    # 合并待买队列（上次因极端行情暂缓的股票）
                    pending = _stock_pool_cache.get('pending_stocks', [])
                    if pending:
                        # 去重合并
                        existing_codes = {s.get('ts_code') for s in selected}
                        new_pending = [s for s in pending if s.get('ts_code') not in existing_codes]
                        selected = selected + new_pending
                        _stock_pool_cache['pending_stocks'] = []
                        logger.info(f"[股票池缓存] 合并{len(new_pending)}只待买股票，当前候选总数{len(selected)}只")
                        print(f"[股票池缓存] 合并{len(new_pending)}只因极端行情暂缓的股票，一并尝试买入")

                    # 二次评分排序：候选池 -> Top-N（由配置文件控制）
                    ranked_selected = _rank_candidate_stocks(selected, get_history_func, market_trend=market_trend)
                    selected = ranked_selected

                    # 打印选股结果
                    print(f"\n{'='*60}")
                    print(f"[问财选股结果] 时间: {current_time.strftime('%H:%M:%S')}, 时间段: {current_period}")
                    print(f"[问财选股结果] 二次评分后保留{len(selected)}只候选股票")
                    if selected:
                        for i, stock in enumerate(selected, 1):
                            ts_code = stock.get('ts_code', 'N/A')
                            name = stock.get('name', 'N/A')
                            total_score = stock.get('total_score', 0.0)
                            trend_score = stock.get('trend_score', 0.0)
                            volume_score = stock.get('volume_score', 0.0)
                            rs_score = stock.get('rs_score', 0.0)
                            breakout_boost = stock.get('breakout_boost', 0.0)
                            market_aggressiveness = stock.get('market_aggressiveness', 1.0)
                            market_trend_label = stock.get('market_trend', 'neutral')
                            print(
                                f"  {i}. {name}({ts_code}) 总分={total_score:.1f} "
                                f"[趋{trend_score:.0f}/量{volume_score:.0f}/强{rs_score:.0f}/启{breakout_boost:.0f}/"
                                f"市{market_trend_label}:{market_aggressiveness:.2f}]"
                            )
                    else:
                        print(f"[问财选股结果] 未选出任何股票")
                    print(f"{'='*60}\n")

                except Exception as e:
                    logger.error(f"[选股] 问财选股失败: {e}，本次不选股", exc_info=True)
                    print(f"[问财选股结果] 选股失败: {e}")
                    selected = []
            elif is_frozen and is_stock_selection_time:
                # 处于冻结期但在时间段内：把已选票存入待买队列，等解冻后消化
                if _stock_pool_cache.get('stocks'):
                    pending_codes = {s.get('ts_code') for s in _stock_pool_cache.get('pending_stocks', [])}
                    new_pending = [s for s in _stock_pool_cache['stocks'] if s.get('ts_code') not in pending_codes]
                    _stock_pool_cache['pending_stocks'].extend(new_pending)
                    logger.info(f"[股票池缓存] 极端行情冻结中，{len(new_pending)}只股票进入待买队列，等待解冻后消化")
                    print(f"[股票池缓存] 极端行情冻结中，{len(new_pending)}只股票进入待买队列")
                selected = []
            else:
                logger.debug(f"[固定时间买入] 当前时间{current_time.strftime('%H:%M:%S')}不在买入时间段内，跳过选股")
                selected = []

            logger.info(f"[资金管理] 当前持股数量={current_stock_count}只，最大持股数量={adjusted_max_stocks}只")
            
            # ========== 打印买入前的状态信息 ==========
            if selected:
                print(f"\n[买入检查] 当前持股: {current_stock_count}只, 最大持股: {adjusted_max_stocks}只")
                print(f"[买入检查] 恐贪指数: 当日={fear_greed_index:.1f}, 长期={long_term_fear_greed_index:.1f}")
                print(f"[买入检查] 开始检查 {len(selected)} 只候选股票的买入条件...\n")
            
            # 多策略买入逻辑
            for stock in selected:
                # 修复：stock 已经是字典，包含 ts_code, symbol, name 等字段
                ts_code = stock.get('ts_code')
                stock_name = stock.get('name', 'unknown')
                
                if not ts_code:
                    logger.warning(f"[多策略买入] 股票信息缺少ts_code字段，跳过: {stock}")
                    continue
                
                if ts_code not in held:
                    # 检查是否超过最大持股数量限制
                    if current_stock_count >= adjusted_max_stocks:
                        logger.warning(f"[多策略买入] 已达到最大持股数量限制({adjusted_max_stocks}只)，跳过买入 {stock_name}({ts_code})")
                        print(f"[多策略买入] 已达到最大持股数量限制({adjusted_max_stocks}只)，当前持仓{current_stock_count}只，跳过买入 {stock_name}({ts_code})")
                        continue
                    
                    df = get_history_func(ts_code)
                    indicators = technical_analyzer.calculate_indicators(df)
                    current_price = get_latest_price_func(ts_code)
                    
                    # 检查价格是否有效
                    if current_price is None or current_price <= 0:
                        logger.error(f"[多策略买入] {stock_name}({ts_code}): 无法获取有效价格，当前价格={current_price}，跳过买入")
                        print(f"[多策略买入] {stock_name}({ts_code}): 无法获取有效价格，当前价格={current_price}，跳过买入")
                        continue
                    
                    # 根据分时K线判断是否处于局部高点，避免买在山峰
                    # 返回 None 表示当前在高点，暂不买入；返回 float 则为优化挂单价
                    try:
                        if get_optimized_buy_price_func is not None:
                            buy_price = get_optimized_buy_price_func(ts_code, current_price, market_trend.get('trend', 'neutral'))
                        else:
                            buy_price = current_price
                    except Exception:
                        buy_price = current_price

                    # 高点判断：返回 None 时跳过本次买入，等待回调
                    if buy_price is None:
                        logger.info(f"[多策略买入] {stock_name}({ts_code}): 当前处于分时高点，跳过买入，等待回调")
                        continue
                    
                    logger.info(f"[多策略买入] {stock_name}({ts_code}): 最新价={current_price:.2f}, 优化挂单价={buy_price:.2f}")
                    
                    # 使用动态持仓管理器计算买入股数（根据账户资金体量自动调整）
                    # 注意：买入数量以 current_price 计算（反映真实成本），挂单用 buy_price
                    min_amount = position_manager.calculate_buy_amount(
                        symbol=ts_code,
                        current_price=current_price,
                        params=position_params  # 使用已获取的参数，避免重复查询
                    )
                    
                    # 检查买入数量是否有效（避免买入过小的持仓）
                    if min_amount <= 0:
                        logger.warning(f"[多策略买入] {stock_name}({ts_code}): 计算买入数量为0，跳过买入")
                        continue
                    
                    # 根据恐贪指数和技术指标综合判断买入策略
                    buy_executed = False
                    
                    # 极端贪婪：禁止买入
                    if fear_greed_index > 90 or long_term_fear_greed_index > 90:
                        print(f"[多策略买入] {stock_name}({ts_code}): 极端贪婪({fear_greed_index:.1f})，禁止买入")
                        continue
                    
                    # 极端恐慌：仅允许极小仓位买入
                    elif fear_greed_index < 10:
                        print(f"[多策略买入] {stock_name}({ts_code}): 极端恐慌({fear_greed_index:.1f})，仅允许极小仓位买入")
                        await order_manager(
                            ts_code,
                            "买",
                            buy_price,
                            min_amount,
                            account,
                            min_order_value=position_params.get("min_position_value", 10000.0),
                        )
                        buy_executed = True
                    
                    # 恐慌区间：小仓位买入
                    elif 10 <= fear_greed_index < 20:
                        print(f"[多策略买入] {stock_name}({ts_code}): 恐慌区间({fear_greed_index:.1f})，小仓位买入")
                        await order_manager(
                            ts_code,
                            "买",
                            buy_price,
                            min_amount,
                            account,
                            min_order_value=position_params.get("min_position_value", 10000.0),
                        )
                        buy_executed = True
                    
                    # 贪婪区间：小仓位买入
                    elif 80 < fear_greed_index <= 90 or 80 < long_term_fear_greed_index <= 90:
                        print(f"[多策略买入] {stock_name}({ts_code}): 贪婪区间({fear_greed_index:.1f})，小仓位买入")
                        await order_manager(
                            ts_code,
                            "买",
                            buy_price,
                            min_amount,
                            account,
                            min_order_value=position_params.get("min_position_value", 10000.0),
                        )
                        buy_executed = True
                    
                    # 市场恐慌：加大买入
                    elif fear_greed_index < 30 and long_term_fear_greed_index < 40:
                        print(f"[多策略买入] {stock_name}({ts_code}): 市场恐慌({fear_greed_index:.1f})，加大买入")
                        await order_manager(
                            ts_code,
                            "买",
                            buy_price,
                            min_amount * 2,
                            account,
                            min_order_value=position_params.get("min_position_value", 10000.0),
                        )
                        buy_executed = True
                    
                    # 正常市场：问财已筛选过（突破均线、散户减少、龙头股），直接买入
                    # 不再用 MA5 > MA20 二次过滤：问财选股本身就是买入信号，
                    # MA5/MA20 金叉是滞后指标，开盘初期往往还没形成，会错过大量机会
                    elif 20 <= fear_greed_index <= 80:
                        print(f"[多策略买入] {stock_name}({ts_code}): 正常市场({fear_greed_index:.1f})，问财已选股，直接买入")
                        await order_manager(
                            ts_code,
                            "买",
                            buy_price,
                            min_amount,
                            account,
                            min_order_value=position_params.get("min_position_value", 10000.0),
                        )
                        buy_executed = True
                    
                    else:
                        # 走到这里说明恐贪指数不在任何已知区间（理论上不应发生）
                        print(f"[多策略买入] {stock_name}({ts_code}): 恐贪指数={fear_greed_index:.1f}，未匹配任何买入条件，跳过")
                        logger.warning(f"[多策略买入] {stock_name}({ts_code}): 恐贪指数={fear_greed_index:.1f}，未匹配任何买入分支，跳过")
                        continue
                    
                    # 如果执行了买入，更新当前持股数量
                    if buy_executed:
                        current_stock_count += 1
                        logger.info(f"[资金管理] 买入后持股数量更新为{current_stock_count}只（最大{adjusted_max_stocks}只）")
                        # 如果已达到上限，提前退出循环
                        if current_stock_count >= adjusted_max_stocks:
                            logger.info(f"[资金管理] 已达到最大持股数量限制({adjusted_max_stocks}只)，停止买入新股票")
                            break
            
            # 多策略卖出逻辑：综合考虑止损止盈、技术指标、市场情绪等因素
            logger.info(f"开始检查持仓卖出信号，持仓数量: {len(valid_positions)}")
            for p in valid_positions:
                symbol = p.stock_code
                try:
                    # 获取历史数据
                    df = get_history_func(symbol)
                    if df is None or len(df) < 20:
                        logger.warning(f"{symbol}: 历史数据不足，无法计算技术指标，跳过卖出检查")
                        continue
                    
                    # 计算技术指标
                    indicators = technical_analyzer.calculate_indicators(df)
                    if not indicators:
                        logger.warning(f"{symbol}: 无法计算技术指标，跳过卖出检查")
                        continue
                    
                    # 获取当前价格和持仓信息
                    # 卖出/风控链路：强制刷新最新价，避免缓存导致盈亏不实时
                    current_price = get_latest_price_func(symbol, force_refresh=True)
                    if current_price is None or current_price <= 0:
                        logger.warning(f"{symbol}: 无法获取当前价格，跳过卖出检查")
                        continue
                    
                    avg_price = getattr(p, 'avg_price', current_price)  # 成本价
                    total_volume = p.volume  # 总持仓
                    # 获取可用持仓（优先使用enable_amount，如果不存在则使用volume，但需要验证）
                    # 修复说明：增强T+1检查，无法确定可用持仓时直接跳过，防止违规交易
                    available_volume = getattr(p, 'enable_amount', None)
                    if available_volume is None:
                        # 如果enable_amount不存在，尝试其他可能的属性名
                        available_volume = getattr(p, 'm_nCanUseVolume', None)
                    
                    # 如果仍然无法获取可用持仓，保守处理：直接跳过
                    if available_volume is None:
                        logger.warning(f"{symbol}: 无法获取可用持仓数量（enable_amount和m_nCanUseVolume都为None），跳过卖出检查（防止T+1违规）")
                        print(f"[T+1安全] {symbol}: 无法确定可用持仓，跳过卖出（总持仓={total_volume}股）")
                        continue
                    
                    # 确保available_volume是整数且合理
                    try:
                        available_volume = int(available_volume)
                    except (ValueError, TypeError):
                        logger.error(f"{symbol}: 可用持仓数量格式错误: {available_volume}，跳过卖出检查")
                        continue
                    
                    # 验证数量合理性（防止异常大的数量）
                    if available_volume > total_volume * 2:
                        logger.error(f"{symbol}: 可用持仓数量异常: {available_volume} > 总持仓{total_volume}*2，跳过卖出检查")
                        continue
                    
                    # T+1规则检查：当日买入的股票不能当日卖出
                    if available_volume <= 0:
                        logger.info(f"{symbol}: 无可用持仓（T+1限制：当日买入的股票不能当日卖出），总持仓={total_volume}股，可用持仓=0股，跳过卖出检查")
                        print(f"[T+1限制] {symbol}: 当日买入的股票不能当日卖出，总持仓={total_volume}股，可用持仓=0股")
                        continue
                    
                    # 如果可用持仓小于总持仓，说明有部分持仓是当日买入的
                    if available_volume < total_volume:
                        locked_volume = total_volume - available_volume
                        logger.info(f"{symbol}: 部分持仓受T+1限制，总持仓={total_volume}股，可用持仓={available_volume}股，锁定持仓={locked_volume}股（当日买入）")
                        print(f"[T+1限制] {symbol}: 部分持仓受T+1限制，只能卖出{available_volume}股（总持仓{total_volume}股，当日买入{locked_volume}股）")
                    
                    # 计算盈亏比例
                    pnl_pct = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0

                    # ====== 追踪止盈：记录持仓以来最高价/最高盈利，并在回撤时卖出 ======
                    # 注意：追踪止盈信号必须在 sell_signals/sell_reasons 初始化之后再 append，
                    # 否则会被后面的 sell_signals = [] 清空导致永远不生效。
                    trailing_activate_pct = float(position_params.get("trailing_take_profit_activate_pct", 3.0))
                    trailing_drawdown_pct = float(position_params.get("trailing_take_profit_drawdown_pct", 1.2))
                    trailing_drawdown_pct = max(0.2, trailing_drawdown_pct)  # 防呆：至少0.2%

                    peak = position_peak_cache.get(symbol)
                    if peak is None:
                        peak = {
                            "peak_price": float(current_price),
                            "peak_pnl_pct": float(pnl_pct),
                            "updated_at": datetime.now(),
                        }
                        position_peak_cache[symbol] = peak
                    else:
                        # 更新最高价/最高盈利
                        if current_price > float(peak.get("peak_price", 0) or 0):
                            peak["peak_price"] = float(current_price)
                            peak["updated_at"] = datetime.now()
                        if pnl_pct > float(peak.get("peak_pnl_pct", -999) or -999):
                            peak["peak_pnl_pct"] = float(pnl_pct)

                    peak_price = float(peak.get("peak_price", current_price) or current_price)
                    peak_pnl_pct = float(peak.get("peak_pnl_pct", pnl_pct) or pnl_pct)
                    drawdown_from_peak_pct = (
                        ((current_price - peak_price) / peak_price * 100) if peak_price > 0 else 0.0
                    )

                    # 2. 止盈：根据市场趋势动态调整止盈阈值，结合均线关系决定卖出时机
                    # 牛市：20%，震荡市：15%，熊市：10%
                    take_profit_threshold = market_trend.get('take_profit_threshold', 15.0)

                    trailing_take_profit_hit = (
                        peak_pnl_pct >= trailing_activate_pct
                        and drawdown_from_peak_pct <= -trailing_drawdown_pct
                    )
                    # 未达到止盈线时，采用“峰值回撤止损”：从最高点回撤超过3%即止损
                    peak_drawdown_stop_hit = (
                        peak_pnl_pct < take_profit_threshold
                        and peak_price > 0
                        and drawdown_from_peak_pct <= -3.0
                    )
                    
                    # 使用 IndicatorCalculator 计算更多技术指标
                    from utils.indicator_calculator import IndicatorCalculator
                    indicator_calc = IndicatorCalculator()
                    
                    # 计算RSI、MACD等指标
                    try:
                        rsi = indicator_calc.calculate(df, 'RSI')
                        macd_result = indicator_calc.calculate(df, 'MACD')
                        macd = macd_result['macd'] if isinstance(macd_result, dict) else None
                        macd_signal = macd_result['signal'] if isinstance(macd_result, dict) else None
                        macd_hist = macd_result['histogram'] if isinstance(macd_result, dict) else None
                    except Exception as e:
                        logger.debug(f"{symbol}: 计算技术指标失败: {e}，使用基础指标")
                        rsi = None
                        macd = None
                        macd_signal = None
                        macd_hist = None
                    
                    # 获取均线指标
                    ma5 = indicators.get('ma5')
                    ma20 = indicators.get('ma20')
                    
                    # 综合卖出信号判断
                    sell_signals = []
                    sell_reasons = []
                    
                    # 标志位：是否处于"止盈持有"状态（达到止盈但趋势强劲，选择继续持有）
                    is_profit_holding = False

                    # 0. 追踪止盈（移动止盈）：从峰值回撤触发
                    if trailing_take_profit_hit:
                        sell_signals.append(True)
                        sell_reasons.append(
                            f"追踪止盈(峰值盈利{peak_pnl_pct:.2f}%/峰值价{peak_price:.2f}，"
                            f"当前价{current_price:.2f}，回撤{drawdown_from_peak_pct:.2f}%≤-{trailing_drawdown_pct:.2f}%)"
                        )
                        logger.info(
                            f"{symbol}: 触发追踪止盈：peak_pnl={peak_pnl_pct:.2f}%, "
                            f"peak_price={peak_price:.2f}, current={current_price:.2f}, "
                            f"drawdown={drawdown_from_peak_pct:.2f}%"
                        )
                    elif peak_drawdown_stop_hit:
                        sell_signals.append(True)
                        sell_reasons.append(
                            f"峰值回撤止损(未达止盈线{take_profit_threshold:.2f}%，"
                            f"峰值价{peak_price:.2f}，当前价{current_price:.2f}，回撤{drawdown_from_peak_pct:.2f}%≤-3.00%)"
                        )
                        logger.warning(
                            f"{symbol}: 触发峰值回撤止损：peak_pnl={peak_pnl_pct:.2f}%, "
                            f"peak_price={peak_price:.2f}, current={current_price:.2f}, "
                            f"drawdown={drawdown_from_peak_pct:.2f}%"
                        )
                    
                    # 1. 止损：亏损超过3%（实盘严格止损，防止大幅亏损）
                    # 修复说明：原来-5%太松，改为-3%更安全
                    if pnl_pct < -3:
                        sell_signals.append(True)
                        sell_reasons.append(f"严格止损(亏损{pnl_pct:.2f}%)")
                        logger.warning(f"{symbol}: 触发严格止损，亏损{pnl_pct:.2f}%，立即卖出")

                    # 可视化日志：止盈检查（防止用户误以为只有止损逻辑）
                    if pnl_pct > 0:
                        print(
                            f"[止盈检查] {symbol}: 当前盈利{pnl_pct:.2f}% / 止盈线{take_profit_threshold:.2f}% "
                            f"(牛20/震15/熊10动态)，MA5={ma5 if ma5 is not None else 'N/A'}，"
                            f"MA20={ma20 if ma20 is not None else 'N/A'}"
                        )

                    if pnl_pct > take_profit_threshold:
                        # 达到止盈阈值后，根据均线关系和趋势强度决定是否卖出
                        if ma5 and ma20:
                            # 情况1：均线死叉或即将死叉（MA5接近MA20且下降），立即止盈
                            if ma5 < ma20:
                                sell_signals.append(True)
                                sell_reasons.append(f"止盈+均线死叉(盈利{pnl_pct:.2f}%，MA5<MA20)")
                                logger.info(f"{symbol}: 达到止盈且均线死叉，立即卖出")
                            # 情况2：价格跌破MA5，趋势转弱，立即止盈
                            elif current_price < ma5:
                                sell_signals.append(True)
                                sell_reasons.append(f"止盈+价格跌破MA5(盈利{pnl_pct:.2f}%，价格{current_price:.2f}<MA5{ma5:.2f})")
                                logger.info(f"{symbol}: 达到止盈且价格跌破MA5，立即卖出")
                            # 情况3：盈利超过阈值1.5倍（如震荡市22.5%），无论均线如何都止盈（防止回撤）
                            elif pnl_pct > take_profit_threshold * 1.5:
                                sell_signals.append(True)
                                sell_reasons.append(f"超额止盈(盈利{pnl_pct:.2f}%，超过阈值{take_profit_threshold}%的1.5倍)")
                                logger.info(f"{symbol}: 盈利超过{take_profit_threshold * 1.5:.1f}%，无论趋势如何都止盈")
                            # 情况4：MA5接近MA20（距离<1%），趋势即将转弱，提前止盈
                            elif ma20 > 0 and abs(ma5 - ma20) / ma20 < 0.01:
                                sell_signals.append(True)
                                sell_reasons.append(f"止盈+均线收敛(盈利{pnl_pct:.2f}%，MA5与MA20距离<1%)")
                                logger.info(f"{symbol}: 达到止盈且均线收敛，提前止盈")
                            else:
                                # 情况5：达到止盈但趋势仍强劲（MA5>MA20且价格>MA5），继续持有让利润奔跑
                                is_profit_holding = True  # 设置标志位
                                logger.info(f"{symbol}: 达到止盈({pnl_pct:.2f}%)但趋势强劲(MA5={ma5:.2f}>MA20={ma20:.2f}，价格={current_price:.2f}>MA5)，继续持有")
                                print(f"[止盈持有] {symbol}: 盈利{pnl_pct:.2f}%已达止盈线，但趋势强劲，继续持有等待更高收益")
                        else:
                            # 无法获取均线数据，采用保守策略：直接止盈
                            sell_signals.append(True)
                            sell_reasons.append(f"止盈(盈利{pnl_pct:.2f}%，无均线数据)")
                            logger.warning(f"{symbol}: 达到止盈但无均线数据，保守止盈")
                    
                    # 技术指标卖出：防抖参数（避免小幅盈利被噪声“抖出去”）
                    # 约束规则：只有当浮盈 ≥ technical_sell_min_profit_pct（默认 8%）时，
                    # 才允许技术指标（MACD 死叉、均线死叉、跌破 MA20、RSI 超买等）触发卖出。
                    # 这样可以避免在刚刚上涨 1~2% 时因为 MACD 死叉等“低位信号”被提前洗出去。
                    technical_sell_min_profit_pct = float(position_params.get('technical_sell_min_profit_pct', 8.0))
                    macd_hist_confirm_bars = int(position_params.get('macd_hist_confirm_bars', 2))
                    macd_hist_confirm_bars = max(1, macd_hist_confirm_bars)

                    # 3. 均线死叉：MA5下穿MA20（仅在盈利且达到最小盈利阈值时检查，亏损时只允许止损）
                    # 修复：亏损时不允许技术指标卖出，避免过早卖出
                    if pnl_pct >= technical_sell_min_profit_pct and not is_profit_holding and pnl_pct <= take_profit_threshold:
                        if ma5 and ma20 and ma5 < ma20:
                            # 检查是否刚发生死叉（前一个周期MA5 >= MA20）
                            if len(df) >= 2:
                                prev_ma5 = df['close'].rolling(window=5).mean().iloc[-2]
                                prev_ma20 = df['close'].rolling(window=20).mean().iloc[-2]
                                if prev_ma5 >= prev_ma20:
                                    sell_signals.append(True)
                                    sell_reasons.append(f"均线死叉(MA5下穿MA20，盈利{pnl_pct:.2f}%)")
                                    logger.info(f"{symbol}: 盈利时均线死叉，触发卖出")
                    
                    # 4. 价格跌破20日均线且偏离超过2%（仅在盈利且达到最小盈利阈值时检查，亏损时只允许止损）
                    # 修复：亏损时不允许技术指标卖出，避免过早卖出
                    if pnl_pct >= technical_sell_min_profit_pct and not is_profit_holding and pnl_pct <= take_profit_threshold:
                        if ma20 and current_price < ma20:
                            price_diff_pct = ((current_price - ma20) / ma20 * 100) if ma20 > 0 else 0
                            if price_diff_pct < -2:  # 低于MA20超过2%
                                sell_signals.append(True)
                                sell_reasons.append(f"跌破MA20(偏离{price_diff_pct:.2f}%，盈利{pnl_pct:.2f}%)")
                                logger.info(f"{symbol}: 盈利时跌破MA20，触发卖出")
                    
                    # 5. RSI超买：RSI > 70（仅在盈利且达到最小盈利阈值时检查，亏损时不允许RSI卖出）
                    # 修复：亏损时不允许RSI卖出，避免过早卖出
                    if pnl_pct >= technical_sell_min_profit_pct and rsi and rsi > 70:
                        if is_profit_holding:
                            # 止盈持有状态下，RSI超买作为强制止盈信号
                            sell_signals.append(True)
                            sell_reasons.append(f"止盈持有+RSI超买({rsi:.2f})，强制止盈")
                            logger.info(f"{symbol}: 止盈持有状态下RSI超买，强制止盈")
                        else:
                            sell_signals.append(True)
                            sell_reasons.append(f"RSI超买({rsi:.2f}，盈利{pnl_pct:.2f}%)")
                            logger.info(f"{symbol}: 盈利时RSI超买，触发卖出")
                    
                    # 6. MACD死叉：MACD下穿信号线（仅在盈利且达到最小盈利阈值时检查，亏损时不允许MACD卖出）
                    # 修复：亏损时不允许MACD卖出，避免过早卖出
                    if pnl_pct >= technical_sell_min_profit_pct and macd is not None and macd_signal is not None:
                        # 检查是否刚发生死叉
                        try:
                            prev_macd = indicator_calc.calculate(df.iloc[:-1], 'MACD_DIF')
                            prev_signal = indicator_calc.calculate(df.iloc[:-1], 'MACD_DEA')
                            if isinstance(prev_macd, (int, float)) and isinstance(prev_signal, (int, float)):
                                if macd < macd_signal and prev_macd >= prev_signal:
                                    if is_profit_holding:
                                        # 止盈持有状态下，MACD死叉作为趋势转弱信号
                                        sell_signals.append(True)
                                        sell_reasons.append(f"止盈持有+MACD死叉，趋势转弱")
                                        logger.info(f"{symbol}: 止盈持有状态下MACD死叉，趋势转弱，止盈离场")
                                    else:
                                        sell_signals.append(True)
                                        sell_reasons.append(f"MACD死叉(盈利{pnl_pct:.2f}%)")
                                        logger.info(f"{symbol}: 盈利时MACD死叉，触发卖出")
                        except:
                            pass
                    
                    # 7. MACD柱状图转负（仅在盈利且达到最小盈利阈值时检查，亏损时不允许MACD卖出）
                    # 修复：亏损时不允许MACD卖出，避免过早卖出
                    if pnl_pct >= technical_sell_min_profit_pct and not is_profit_holding and macd_hist is not None:
                        # 连续确认：默认需要最近N根K线柱状图均为负，降低单根噪声触发
                        should_macd_hist_sell = macd_hist < 0
                        if should_macd_hist_sell and macd_hist_confirm_bars >= 2:
                            try:
                                confirm_ok = True
                                tmp_df = df.copy()
                                # 逐根回溯确认（最多确认N根）
                                for _ in range(macd_hist_confirm_bars - 1):
                                    if len(tmp_df) < 2:
                                        confirm_ok = False
                                        break
                                    tmp_df = tmp_df.iloc[:-1]
                                    tmp_res = indicator_calc.calculate(tmp_df, 'MACD')
                                    tmp_hist = tmp_res.get('histogram') if isinstance(tmp_res, dict) else None
                                    if tmp_hist is None or tmp_hist >= 0:
                                        confirm_ok = False
                                        break
                                should_macd_hist_sell = confirm_ok
                            except Exception as e:
                                logger.debug(f"{symbol}: MACD柱状图连续确认失败: {e}，退化为单根判断")
                                should_macd_hist_sell = (macd_hist < 0)

                        if should_macd_hist_sell:
                            sell_signals.append(True)
                            sell_reasons.append(
                                f"MACD柱状图连续{macd_hist_confirm_bars}根转负({macd_hist:.4f}，盈利{pnl_pct:.2f}%)"
                            )
                            logger.info(f"{symbol}: 盈利且满足最小盈利阈值时MACD柱状图转负(连续确认)，触发卖出")
                        else:
                            logger.info(
                                f"{symbol}: MACD柱状图转负但未满足连续确认({macd_hist_confirm_bars}根)，暂不卖出"
                            )

                    # 额外可读日志：盈利太小不参与技术卖出（避免用户误解“止盈/止损没生效”）
                    if 0 < pnl_pct < technical_sell_min_profit_pct and not is_profit_holding:
                        logger.info(
                            f"{symbol}: 当前盈利{pnl_pct:.2f}% < 技术卖出最小盈利阈值{technical_sell_min_profit_pct:.2f}%，"
                            f"忽略技术指标卖出（避免抖动）"
                        )
                    
                    # 8. 市场情绪：极端贪婪时考虑止盈卖出（止盈持有状态下也检查）
                    # 修复：亏损时不允许市场情绪卖出，避免过早卖出（已有pnl_pct > 5限制，确保只在盈利时触发）
                    if pnl_pct > 0 and fear_greed_index > 80 and pnl_pct > 5:
                        if is_profit_holding:
                            sell_signals.append(True)
                            sell_reasons.append(f"止盈持有+市场极端贪婪(恐贪指数{fear_greed_index:.1f})，强制止盈")
                            logger.info(f"{symbol}: 止盈持有状态下市场极端贪婪，强制止盈")
                        else:
                            sell_signals.append(True)
                            sell_reasons.append(f"市场贪婪(恐贪指数{fear_greed_index:.1f})且盈利{pnl_pct:.2f}%")
                    
                    # 9. 亏损保护：亏损时（pnl_pct < 0）只允许止损卖出，禁止所有技术指标卖出
                    # 修复：确保亏损时只保留真正的止损信号（pnl_pct < -3），过滤掉所有其他信号
                    # 这是最后一道防线，防止任何技术指标在亏损时触发卖出
                    if pnl_pct < 0:
                        # 只保留真正的止损信号（亏损超过-3%）
                        filtered_signals = []
                        filtered_reasons = []
                        for i, reason in enumerate(sell_reasons):
                            # 只保留包含"严格止损"的信号（这是唯一在亏损时应该保留的信号）
                            if '严格止损' in reason:
                                filtered_signals.append(sell_signals[i])
                                filtered_reasons.append(reason)
                            else:
                                # 过滤掉所有非止损信号（包括技术指标信号）
                                logger.warning(
                                    f"{symbol}: 亏损{pnl_pct:.2f}%时过滤掉非止损信号: {reason}（亏损时只允许止损卖出）"
                                )
                                print(f"[亏损保护] {symbol}: 亏损{pnl_pct:.2f}%时过滤掉非止损信号: {reason}")
                        
                        sell_signals = filtered_signals
                        sell_reasons = filtered_reasons
                        
                        # 如果亏损超过-3%但没有止损信号，强制添加止损信号（安全保护）
                        if pnl_pct < -3 and not sell_signals:
                            sell_signals.append(True)
                            sell_reasons.append(f"严格止损(亏损{pnl_pct:.2f}%)")
                            logger.warning(f"{symbol}: 亏损{pnl_pct:.2f}%但无止损信号，强制添加止损信号")
                        elif not sell_signals:
                            logger.info(f"{symbol}: 亏损{pnl_pct:.2f}%但未达止损线(-3%)，暂不卖出")
                            print(f"[亏损保护] {symbol}: 亏损{pnl_pct:.2f}%未达止损线(-3%)，暂不卖出")
                    
                    # 综合判断：满足任一卖出条件即可卖出
                    should_sell = any(sell_signals) if sell_signals else False
                    
                    # 调试信息：打印所有卖出信号（无论是否卖出）
                    if sell_signals:
                        logger.debug(f"[卖出检查] {symbol}: 当前盈亏={pnl_pct:.2f}%, 卖出信号数量={len(sell_signals)}")
                        logger.debug(f"[卖出检查] {symbol}: 卖出原因列表={sell_reasons}")
                        if pnl_pct < 0:
                            logger.debug(f"[卖出检查] {symbol}: 当前处于亏损状态，只允许止损卖出（止损线=-3%）")
                    
                    if should_sell:
                        reason_str = "、".join(sell_reasons)
                        # 格式化指标值，处理None情况
                        ma5_str = f"{ma5:.2f}" if ma5 is not None else "N/A"
                        ma20_str = f"{ma20:.2f}" if ma20 is not None else "N/A"
                        rsi_str = f"{rsi:.2f}" if rsi is not None else "N/A"
                        
                        # 增强日志输出：明确显示卖出类型（止损/止盈/技术指标）
                        sell_type = "止损" if pnl_pct < -3 else "止盈" if pnl_pct > take_profit_threshold else "技术指标"
                        logger.info(f"[多策略卖出] {symbol}: 触发卖出信号 - {reason_str}")
                        logger.info(f"[多策略卖出] {symbol}: 卖出类型={sell_type}, 价格={current_price:.2f}, 成本={avg_price:.2f}, 盈亏={pnl_pct:.2f}%, "
                                   f"MA5={ma5_str}, MA20={ma20_str}, "
                                   f"RSI={rsi_str}, 持仓={available_volume}股")
                        
                        # 增强控制台输出：明确显示卖出原因和盈亏情况
                        print(f"\n{'='*60}")
                        print(f"[多策略卖出] {symbol}: {reason_str}")
                        print(f"[多策略卖出] 卖出类型: {sell_type}")
                        print(f"[多策略卖出] 价格={current_price:.2f}, 成本={avg_price:.2f}, 盈亏={pnl_pct:.2f}%")
                        print(f"[多策略卖出] 技术指标: MA5={ma5_str}, MA20={ma20_str}, RSI={rsi_str}")
                        print(f"[多策略卖出] 可用持仓={available_volume}股, 总持仓={total_volume}股")
                        print(f"{'='*60}\n")
                        
                        # 执行卖出：只卖出可用持仓（已考虑T+1规则）
                        # 注意：available_volume 已经由券商计算，排除了当日买入的股票
                        if available_volume > 0:
                            # A股交易规则：最小委托单位100股（科创板200股），必须是整数倍
                            # 科创板单笔最大委托：1000手（100000股）；普通A股：9000手（900000股）
                            if symbol.startswith('688'):
                                min_unit = 200
                                MAX_SELL_QUANTITY = 100000  # 科创板单笔最大1000手
                            else:
                                min_unit = 100
                                MAX_SELL_QUANTITY = 900000  # 普通A股单笔最大9000手

                            if available_volume < min_unit:
                                logger.warning(
                                    f"[多策略卖出] {symbol}: 可用持仓{available_volume}股不足100股，无法卖出（A股最小委托单位100股）"
                                )
                                print(
                                    f"[多策略卖出] {symbol}: 可用持仓{available_volume}股不足100股，无法卖出"
                                )
                                # 记录卖出失败事件（可用股数不足 100 股）
                                try:
                                    record_trade_event(
                                        event_type="卖出失败",
                                        symbol=symbol,
                                        side="卖",
                                        reason=(
                                            f"可用持仓{available_volume}股不足100股，"
                                            "无法卖出（A股最小委托单位100股）"
                                        ),
                                        pnl_pct=pnl_pct,
                                        extra={
                                            "可用持仓": int(available_volume),
                                            "总持仓": int(total_volume),
                                        },
                                    )
                                except Exception:
                                    pass
                            else:
                                # 计算需要分几批卖出
                                total_to_sell = (min(available_volume, available_volume) // min_unit) * min_unit
                                batches = []
                                remaining = total_to_sell
                                while remaining > 0:
                                    batch = min(remaining, MAX_SELL_QUANTITY)
                                    batch = (batch // min_unit) * min_unit
                                    if batch < min_unit:
                                        break
                                    batches.append(batch)
                                    remaining -= batch

                                batch_count = len(batches)
                                if batch_count > 1:
                                    logger.info(
                                        f"[多策略卖出] {symbol}: 可用持仓{available_volume}股超过单批最大{MAX_SELL_QUANTITY}股（10000手），"
                                        f"分{batch_count}批卖出，每批最多{MAX_SELL_QUANTITY}股"
                                    )
                                    print(
                                        f"[多策略卖出] {symbol}: 持仓{available_volume}股，分{batch_count}批卖出，每批最多10000手"
                                    )

                                # 记录卖出下单事件
                                try:
                                    record_trade_event(
                                        event_type="卖出下单",
                                        symbol=symbol,
                                        side="卖",
                                        reason=reason_str,
                                        pnl_pct=pnl_pct,
                                        extra={
                                            "卖出类型": sell_type,
                                            "卖出总数量": int(total_to_sell),
                                            "分批数量": batch_count,
                                            "可用持仓": int(available_volume),
                                            "总持仓": int(total_volume),
                                            "卖出价格": float(current_price),
                                        },
                                    )
                                except Exception:
                                    pass

                                # 逐批下单
                                for i, batch_qty in enumerate(batches, 1):
                                    if batch_count > 1:
                                        logger.info(
                                            f"[多策略卖出] {symbol}: 第{i}/{batch_count}批，卖出{batch_qty}股"
                                        )
                                    await order_manager(symbol, "卖", current_price, batch_qty, account)

                                sell_quantity = total_to_sell  # 供后续日志使用
                                logger.info(
                                    f"[多策略卖出] {symbol}: 已提交卖出订单，数量={sell_quantity}股（可用{available_volume}股，总持仓{total_volume}股），价格={current_price:.2f}"
                                )
                        else:
                            logger.warning(
                                f"[多策略卖出] {symbol}: 无可用持仓（T+1限制），无法卖出"
                            )
                            print(
                                f"[T+1限制] {symbol}: 当日买入的股票不能当日卖出，无法执行卖出订单"
                            )
                            # 记录 T+1 限制导致的卖出失败
                            try:
                                record_trade_event(
                                    event_type="卖出失败",
                                    symbol=symbol,
                                    side="卖",
                                    reason="T+1限制：当日买入的股票不能当日卖出，无法执行卖出订单",
                                    pnl_pct=pnl_pct,
                                    extra={
                                        "可用持仓": int(available_volume),
                                        "总持仓": int(total_volume),
                                    },
                                )
                            except Exception:
                                pass
                    else:
                        # 记录持有原因
                        hold_reasons = []
                        if pnl_pct >= -5 and pnl_pct <= 15:
                            hold_reasons.append(f"盈亏正常({pnl_pct:.2f}%)")
                        if ma5 and ma20 and ma5 >= ma20:
                            hold_reasons.append("均线多头排列")
                        if rsi and rsi <= 70:
                            hold_reasons.append(f"RSI未超买({rsi:.2f})")
                        if fear_greed_index < 20 and pnl_pct < -3:
                            hold_reasons.append(f"恐慌市场但亏损未达止损线")
                        
                        if hold_reasons:
                            logger.debug(f"[多策略卖出] {symbol}: 继续持有 - {'、'.join(hold_reasons)}")
                        
                except Exception as e:
                    logger.error(f"[多策略卖出] {symbol}: 卖出检查失败: {e}", exc_info=True)
                    print(f"[多策略卖出] {symbol}: 卖出检查失败: {e}")
            
            # 收盘后输出一次“市场广度覆盖触发”日报（14:55后，每日仅一次）
            report_time = datetime.now().time()
            if report_time >= time(14, 55) and _breadth_report_cache.get('last_report_time') != today_str:
                trigger_count = int(_breadth_report_cache.get('trigger_count', 0) or 0)
                baseline_asset = _breadth_report_cache.get('baseline_asset')
                last_asset = _breadth_report_cache.get('last_asset')
                max_asset = _breadth_report_cache.get('max_asset_after_trigger')
                min_asset = _breadth_report_cache.get('min_asset_after_trigger')

                if trigger_count > 0 and baseline_asset and last_asset:
                    pnl_pct_after_trigger = (last_asset - baseline_asset) / baseline_asset * 100
                    max_pnl_pct = (max_asset - baseline_asset) / baseline_asset * 100 if max_asset else 0.0
                    max_drawdown_pct = (min_asset - baseline_asset) / baseline_asset * 100 if min_asset else 0.0

                    logger.info(
                        f"[市场广度日报] 日期={today_str}, 触发次数={trigger_count}, "
                        f"首次触发={_breadth_report_cache.get('first_trigger_time')}, "
                        f"触发后收益={pnl_pct_after_trigger:.2f}%, "
                        f"触发后峰值收益={max_pnl_pct:.2f}%, "
                        f"触发后最大回撤={max_drawdown_pct:.2f}%"
                    )
                    logger.info(
                        f"[市场广度日报] 触发时刻列表: {_breadth_report_cache.get('trigger_times', [])}"
                    )
                    print(
                        f"[市场广度日报] 触发{trigger_count}次，触发后收益{pnl_pct_after_trigger:.2f}%，"
                        f"峰值{max_pnl_pct:.2f}%，最大回撤{max_drawdown_pct:.2f}%"
                    )
                else:
                    logger.info(f"[市场广度日报] 日期={today_str}, 当日未触发广度覆盖或基线资产不可用")

                _breadth_report_cache['last_report_time'] = today_str

            # 持仓分析结果打印
            # print("[多策略持仓监控] 最新持仓分析:", analysis)
            
        except Exception as e:
            print(f"[多策略持仓监控] 自动买卖/分析失败: {e}")
        
        await asyncio.sleep(interval)

# 保留原有的单策略函数作为备用
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
    持仓持续监控+自动买卖任务（单策略版本）。
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
            await asyncio.sleep(30)  # 非交易时段加长等待，减少刷屏
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
                # 获取可用持仓数量（统一处理）
                available_volume = getattr(p, 'm_nCanUseVolume', None)
                if available_volume is None:
                    available_volume = getattr(p, 'enable_amount', None)
                if available_volume is None:
                    available_volume = p.volume
                
                # 确保是整数且合理
                try:
                    available_volume = int(available_volume)
                except (ValueError, TypeError):
                    logger.error(f"[卖出] {symbol}: 可用持仓数量格式错误: {available_volume}，跳过")
                    continue
                
                # 验证数量合理性
                if available_volume > p.volume * 2:
                    logger.error(f"[卖出] {symbol}: 可用持仓数量异常: {available_volume} > 总持仓{p.volume}*2，跳过")
                    continue
                
                # T+1规则检查
                if available_volume <= 0:
                    logger.info(f"[卖出] {symbol}: 无可用持仓（T+1限制），总持仓={p.volume}股，跳过")
                    continue
                
                # A股交易规则：最小委托单位100股，必须是100的整数倍
                # 卖出限制：一笔最大100万股
                min_unit = 100
                MAX_SELL_QUANTITY = 1000000
                sell_quantity = min(available_volume, MAX_SELL_QUANTITY)
                sell_quantity = (sell_quantity // min_unit) * min_unit
                
                if sell_quantity < min_unit:
                    logger.warning(f"[卖出] {symbol}: 可用持仓{available_volume}股不足100股，无法卖出")
                    continue
                
                # 恐慌区间仅允许止损卖出（修复：止损从-5%改为-3%）
                if 10 <= fear_greed_index < 20:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        pnl = (current_price - p.avg_price) / p.avg_price * 100
                        if pnl < -3:  # 修复：严格止损-3%
                            await order_manager(symbol, "卖", current_price, sell_quantity, account)
                            print(f"[卖出决策] 恐慌区间({fear_greed_index:.1f})，仅允许止损卖出 {symbol} 价格: {current_price}, 数量: {sell_quantity}股")
                        else:
                            print(f"[卖出决策] 恐慌区间({fear_greed_index:.1f})，非止损不卖出 {symbol}")
                    continue
                # 极端贪婪下允许加大卖出
                if fear_greed_index > 90 or long_term_fear_greed_index > 90:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        await order_manager(symbol, "卖", current_price, sell_quantity, account)
                        print(f"[卖出决策] 极端贪婪({fear_greed_index:.1f})，加大卖出 {symbol} 价格: {current_price}, 数量: {sell_quantity}股，建议锁定收益。")
                    continue
                # 80-90区间正常卖出
                if 80 < fear_greed_index <= 90 or 80 < long_term_fear_greed_index <= 90:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        await order_manager(symbol, "卖", current_price, sell_quantity, account)
                        print(f"[卖出决策] 贪婪区间({fear_greed_index:.1f})，正常卖出 {symbol} 价格: {current_price}, 数量: {sell_quantity}股")
                    continue
                # 其它情况正常卖出
                if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                    await order_manager(symbol, "卖", current_price, sell_quantity, account)
                    print(f"[自动卖出] {symbol} 价格: {current_price}, 数量: {sell_quantity}股")
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
                    # 计算合理的买入股数（考虑账户资金、价格、风险控制）
                    min_amount = get_min_buy_amount(
                        symbol=symbol,
                        account=account,
                        xt_trader=xt_trader,
                        current_price=current_price,
                        max_position_ratio=0.1,  # 单只股票最大10%仓位（风险分散原则）
                        min_position_value=10000.0,  # 最小持仓10000元（控制交易成本占比<1%）
                        max_position_value=800000.0  # 最大持仓80000元（单只股票风险上限）
                    )
                    # 检查买入数量是否有效（避免买入过小的持仓）
                    if min_amount <= 0:
                        logger.warning(f"[买入决策] {symbol}: 计算买入数量为0，跳过买入")
                        continue
                    
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

def get_min_buy_amount(
    symbol: str,
    account: Optional[StockAccount] = None,
    xt_trader=None,
    current_price: Optional[float] = None,
    max_position_ratio: float = 0.1,
    min_position_value: float = 10000.0,
    max_position_value: float = 80000.0
) -> int:
    """
    计算合理的买入股数（基于量化交易最佳实践）
    
    根据以下因素计算：
    1. 交易所最小买入单位（100股或200股）
    2. 账户可用资金
    3. 股票当前价格
    4. 单只股票最大仓位比例（默认10%，符合风险分散原则）
    5. 最小/最大持仓金额限制（基于交易成本和风险控制）
    
    策略研究说明：
    - 最小持仓10000元：确保交易成本占比<1%（佣金0.03%+印花税0.1%+过户费0.001%）
      避免小额交易导致成本侵蚀收益，提高资金利用效率
    - 最大持仓80000元：单只股票风险上限，即使账户资金较大也限制单股风险
      结合10%仓位比例，可同时持有10-12只股票，实现良好分散化
    - 10%仓位比例：基于现代投资组合理论，单只股票不超过总资金10%
      既能获得分散化收益，又能控制单股风险敞口
    
    Args:
        symbol: 股票代码，例如 '000001.SZ'
        account: 股票账户对象（可选）
        xt_trader: 交易接口对象（可选，用于查询账户资金）
        current_price: 股票当前价格（可选，如果不提供则返回最小买入单位）
        max_position_ratio: 单只股票最大仓位比例（默认0.1，即10%，风险分散原则）
        min_position_value: 最小持仓金额（默认10000元，控制交易成本占比<1%）
        max_position_value: 最大持仓金额（默认80000元，单只股票风险上限）
        
    Returns:
        int: 建议买入股数（已调整为最小买入单位的整数倍）
        
    Example:
        >>> # 仅获取最小买入单位
        >>> amount = get_min_buy_amount('000001.SZ')
        >>> # 返回: 100
        >>> 
        >>> # 根据账户资金和价格计算
        >>> amount = get_min_buy_amount('000001.SZ', account, xt_trader, current_price=10.5)
        >>> # 返回: 根据账户资金计算的合理股数（10000-80000元范围内）
    """
    # 1. 确定最小买入单位（交易所规则）
    min_unit = 100  # 默认100股
    if symbol.endswith('.BJ'):
        min_unit = 100
    elif symbol.startswith('688'):  # 科创板
        min_unit = 200
    elif symbol.startswith('300'):  # 创业板
        min_unit = 100
    elif symbol.startswith('60') or symbol.startswith('00'):  # 主板
        min_unit = 100
    
    # 如果没有提供价格或账户信息，直接返回最小买入单位
    if current_price is None or current_price <= 0:
        return min_unit
    
    # 如果没有提供账户信息，返回最小买入单位
    if account is None or xt_trader is None:
        logger.debug(f"{symbol}: 未提供账户信息，返回最小买入单位 {min_unit}")
        return min_unit
    
    try:
        # 2. 查询账户可用资金
        asset = xt_trader.query_stock_asset(account)
        available_cash = getattr(asset, 'cash', 0) or getattr(asset, 'available_cash', 0)
        
        if available_cash <= 0:
            logger.warning(f"{symbol}: 账户可用资金为0或无法获取，返回最小买入单位 {min_unit}")
            return min_unit
        
        # 3. 计算基于资金限制的最大可买金额
        # 考虑单只股票最大仓位比例
        max_buy_value_by_ratio = available_cash * max_position_ratio
        
        # 考虑最大持仓金额限制
        max_buy_value = min(max_buy_value_by_ratio, max_position_value)
        
        # 确保不低于最小持仓金额
        if max_buy_value < min_position_value:
            logger.debug(f"{symbol}: 计算出的最大买入金额({max_buy_value:.2f})小于最小持仓金额({min_position_value:.2f})")
            # 如果可用资金足够，使用最小持仓金额
            if available_cash >= min_position_value:
                max_buy_value = min_position_value
            else:
                # 修复：可用资金不足时，不买入（返回0），而不是返回最小单位
                # 避免出现低于最小持仓金额的持仓（如400元）
                logger.warning(f"{symbol}: 可用资金{available_cash:.2f}元不足最小持仓金额{min_position_value:.2f}元，不买入")
                return 0  # 返回0表示不买入
        
        # 4. 计算可买股数（考虑手续费，假设0.03%）
        commission_rate = 0.0003
        # 买入金额 = 股数 * 价格 * (1 + 手续费率)
        # 股数 = 买入金额 / (价格 * (1 + 手续费率))
        max_shares = int(max_buy_value / (current_price * (1 + commission_rate)))
        
        # 5. 调整为最小买入单位的整数倍
        shares = (max_shares // min_unit) * min_unit
        
        # 6. 确保不低于最小买入单位
        if shares < min_unit:
            shares = min_unit
        
        # 7. 验证最终金额不超过可用资金
        final_cost = shares * current_price * (1 + commission_rate)
        if final_cost > available_cash:
            # 如果超出，减少到可用资金范围内
            max_affordable_shares = int(available_cash / (current_price * (1 + commission_rate)))
            shares = (max_affordable_shares // min_unit) * min_unit
            if shares < min_unit:
                logger.warning(f"{symbol}: 可用资金{available_cash:.2f}元不足，无法买入最小单位{min_unit}股")
                return 0  # 修复：返回0表示不买入，而不是返回最小单位
        
        # 8. 最终验证：确保买入金额不低于最小持仓金额
        final_value = shares * current_price
        if final_value < min_position_value:
            logger.warning(f"{symbol}: 最终买入金额{final_value:.2f}元低于最小持仓金额{min_position_value:.2f}元，不买入")
            return 0  # 返回0表示不买入
        
        logger.info(f"{symbol}: 计算买入股数 - 可用资金={available_cash:.2f}, 价格={current_price:.2f}, "
                   f"建议股数={shares}, 预计金额={shares * current_price:.2f}")
        
        return shares
        
    except Exception as e:
        logger.error(f"{symbol}: 计算买入股数失败: {e}，返回最小买入单位 {min_unit}", exc_info=True)
        return min_unit
def get_latest_price_func(symbol, xt_trader=None, **kwargs):
    """代理到 main.get_latest_price_func，允许透传 force_refresh/max_age_sec 等参数"""
    from main import get_latest_price_func as main_get_latest_price_func
    return main_get_latest_price_func(symbol, xt_trader, **kwargs)

