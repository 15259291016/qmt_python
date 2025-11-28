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

# 配置日志
logger = logging.getLogger(__name__)
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


def judge_market_trend_comprehensive(
    get_history_func,
    position_analyzer: PositionAnalyzer,
    fear_greed_index: float,
    long_term_fear_greed_index: float,
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
                df = get_history_func(idx_code)
                quality = _validate_data_quality(df, min_length=60)
                
                if not quality['valid']:
                    logger.warning(f"[市场趋势] 指数 {idx_code} 数据质量不足: {quality['issues']}")
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
                logger.warning(f"[市场趋势] 处理指数 {idx_code} 失败: {e}")
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
        else:
            factors['ma_system'] = {'score': 0.0, 'error': '所有指数数据不足'}
        
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
        
        # ========== 3. 多周期涨跌幅（权重20%） ==========
        # 使用主要指数（上证）计算多周期涨跌幅
        main_df = None
        for idx_code in index_codes:
            try:
                df = get_history_func(idx_code)
                if _validate_data_quality(df, min_length=120)['valid']:
                    main_df = df
                    break
            except:
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
            else:
                factors['index_return'] = {'score': 0.0, 'error': '无法计算多周期涨跌幅'}
        else:
            factors['index_return'] = {'score': 0.0, 'error': '主要指数数据不足'}
        
        # ========== 4. 成交量+价格方向（权重15%）- 优化版 ==========
        if main_df is not None and len(main_df) >= 20:
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
        else:
            factors['volume'] = {'score': 0.0, 'error': '数据不足'}
        
        # ========== 综合得分 ==========
        total_score = sum(scores) if scores else 0.0
        confidence = min(abs(total_score), 1.0)
        
        # 动态阈值：根据数据质量调整
        data_quality_avg = sum([f.get('quality_score', 1.0) for f in factors.values() 
                               if isinstance(f, dict) and 'quality_score' in f]) / max(1, len([f for f in factors.values() 
                               if isinstance(f, dict) and 'quality_score' in f]))
        
        # 数据质量高时使用标准阈值，质量低时放宽阈值
        threshold = 0.3 if data_quality_avg > 0.8 else 0.25
        
        # 判断趋势
        if total_score > threshold:
            trend = 'bull'  # 牛市
        elif total_score < -threshold:
            trend = 'bear'  # 熊市
        else:
            trend = 'neutral'  # 震荡市
        
        return {
            'trend': trend,
            'confidence': confidence,
            'score': total_score,
            'threshold_used': threshold,
            'data_quality_avg': data_quality_avg,
            'factors': factors,
            'description': {
                'bull': '牛市：市场情绪乐观，多指数上涨，均线多头排列',
                'bear': '熊市：市场情绪悲观，多指数下跌，均线空头排列',
                'neutral': '震荡市：市场方向不明确，多空力量均衡'
            }[trend]
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
    max_stocks: int = 15
):
    """
    多策略持仓监控+自动买卖任务。
    支持多个策略并行运行，每个策略可以管理不同的股票池。
    
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
        max_stocks: 最大持股数量（默认15只，根据恐贪指数动态调整）
    """
    from modules.strategy_manager.manager import StrategyManager
    from modules.strategy_manager.config import STRATEGY_CONFIG
    
    # 初始化策略管理器
    risk_manager = RiskManager()
    compliance_manager = ComplianceManager()
    audit_logger = AuditLogger()
    
    strategy_manager = StrategyManager(
        xt_trader=xt_trader,
        order_manager=order_manager,
        base_path="strategy_data"
    )
    
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
            fear_greed_index = getattr(summary, 'fear_greed_index', 50)
            long_term_fear_greed_index = getattr(summary, 'long_term_fear_greed_index', 50)
            print(f"[恐贪指数] 当日: {fear_greed_index:.1f}，长期: {long_term_fear_greed_index:.1f}")
            
            # 综合判断市场趋势（牛市/熊市/震荡市）- 使用多指数综合判断
            market_trend = judge_market_trend_comprehensive(
                get_history_func=get_history_func,
                position_analyzer=position_analyzer,
                fear_greed_index=fear_greed_index,
                long_term_fear_greed_index=long_term_fear_greed_index,
                index_codes=['000001.SH', '399001.SZ', '399006.SZ', '000905.SH']  # 上证、深证、创业板、中证500
            )
            
            logger.info(f"[市场趋势] {market_trend['trend']} ({market_trend['description']})，"
                       f"置信度={market_trend['confidence']:.2f}，综合得分={market_trend['score']:.2f}")
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
            
            # 选股池自动买入（自适应热点行业）
            # 只在指定时间段执行问财选股：早上9:50-10:00，下午14:20-14:30
            current_time = datetime.now().time()
            # 定义选股时间段列表
            stock_selection_periods = [
                (time(9, 50), time(10, 0)),   # 早上9:50-10:00
                (time(14, 20), time(14, 30))  # 下午14:20-14:30
            ]
            # 检查当前时间是否在任一选股时间段内
            is_stock_selection_time = any(
                period_start <= current_time <= period_end 
                for period_start, period_end in stock_selection_periods
            )
            
            selected = []  # 默认不选股
            if is_stock_selection_time:
                # 确定当前在哪个时间段
                current_period = None
                for period_start, period_end in stock_selection_periods:
                    if period_start <= current_time <= period_end:
                        current_period = f"{period_start.strftime('%H:%M')}-{period_end.strftime('%H:%M')}"
                        break
                
                try:
                    logger.info(f"[选股] 当前时间{current_time.strftime('%H:%M:%S')}在选股时间段内({current_period})，执行问财选股")
                    # selected_codes = stock_selector.select_by_hot_industry()
                    # print(f"热点行业选股结果: {selected_codes}")
                    question_list = []
                    # question_list.append("突破十日均线，散户数量下降")
                    question_list.append("突破十日均线，散户数量下降，龙头股，剔除st")
                    
                    # 使用异步函数获取股票列表（包含详细信息）
                    selected_codes = await async_select_stocks_by_wencai(
                        question_list=question_list,
                        filter_by_retail_investor=True,
                        include_info=True
                    )
                    # selected_codes = stock_selector.select_by_wencai("比亚迪")
                    selected = [{"symbol": code} for code in selected_codes]
                    logger.info(f"[选股] 问财选股完成，共选出{len(selected)}只股票")
                except Exception as e:
                    logger.error(f"[选股] 问财选股失败: {e}，本次不选股", exc_info=True)
                    print(f"[选股] 问财选股失败: {e}，本次不选股")
                    selected = []  # 选股失败时也不选股
            else:
                logger.debug(f"[选股] 当前时间{current_time.strftime('%H:%M:%S')}不在选股时间段内(9:50-10:00)，跳过选股")
            
            held = {p.stock_code for p in valid_positions}
            current_stock_count = len(held)
            
            # 根据恐贪指数动态调整最大持股数量
            # 恐慌市场：降低持股数量，集中资金（减少至70%）
            # 正常市场：标准持股数量
            # 贪婪市场：控制持股数量，预留现金（减少至80%）
            adjusted_max_stocks = max_stocks
            if fear_greed_index < 20:  # 恐慌市场
                adjusted_max_stocks = int(max_stocks * 0.7)  # 降低至70%
                logger.info(f"[资金管理] 恐慌市场（恐贪指数={fear_greed_index:.1f}），降低最大持股数量至{adjusted_max_stocks}只")
            elif fear_greed_index > 80:  # 贪婪市场
                adjusted_max_stocks = int(max_stocks * 0.8)  # 降低至80%，控制风险
                logger.info(f"[资金管理] 贪婪市场（恐贪指数={fear_greed_index:.1f}），控制最大持股数量至{adjusted_max_stocks}只")
            
            logger.info(f"[资金管理] 当前持股数量={current_stock_count}只，最大持股数量={adjusted_max_stocks}只")
            
            # 多策略买入逻辑
            for stock in selected:
                symbol = stock['symbol']
                if symbol["ts_code"] not in held:
                    # 检查是否超过最大持股数量限制
                    if current_stock_count >= adjusted_max_stocks:
                        logger.warning(f"[多策略买入] 已达到最大持股数量限制({adjusted_max_stocks}只)，跳过买入 {symbol.get('ts_code', symbol.get('symbol', 'unknown'))}")
                        print(f"[多策略买入] 已达到最大持股数量限制({adjusted_max_stocks}只)，当前持仓{current_stock_count}只，跳过买入 {symbol.get('ts_code', symbol.get('symbol', 'unknown'))}")
                        continue
                    df = get_history_func(symbol["ts_code"])
                    indicators = technical_analyzer.calculate_indicators(df)
                    current_price = get_latest_price_func(symbol["ts_code"])
                    # 计算合理的买入股数（考虑账户资金、价格、风险控制）
                    min_amount = get_min_buy_amount(
                        symbol=symbol["ts_code"],
                        account=account,
                        xt_trader=xt_trader,
                        current_price=current_price,
                        max_position_ratio=0.1,  # 单只股票最大10%仓位（风险分散原则）
                        min_position_value=10000.0,  # 最小持仓10000元（控制交易成本占比<1%）
                        max_position_value=800000.0  # 最大持仓800000元（单只股票风险上限）
                    )
                    
                    # 根据恐贪指数调整买入策略
                    buy_executed = False
                    if fear_greed_index < 10:
                        print(f"[多策略买入] 极端恐慌({fear_greed_index:.1f})，仅允许极小仓位买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount, account)
                        buy_executed = True
                    elif 10 <= fear_greed_index < 20:
                        print(f"[多策略买入] 恐慌区间({fear_greed_index:.1f})，小仓位买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount, account)
                        buy_executed = True
                    elif fear_greed_index > 90 or long_term_fear_greed_index > 90:
                        print(f"[多策略买入] 极端贪婪({fear_greed_index:.1f})，禁止买入 {symbol}")
                        continue
                    elif 80 < fear_greed_index <= 90 or 80 < long_term_fear_greed_index <= 90:
                        print(f"[多策略买入] 贪婪区间({fear_greed_index:.1f})，小仓位买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount, account)
                        buy_executed = True
                    elif fear_greed_index < 30 and long_term_fear_greed_index < 40:
                        print(f"[多策略买入] 市场恐慌，加大买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount*2, account)
                        buy_executed = True
                    elif technical_analyzer.is_buy_signal(indicators):
                        print(f"[多策略买入] 正常买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount, account)
                        buy_executed = True
                    
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
                    current_price = get_latest_price_func(symbol)
                    if current_price is None or current_price <= 0:
                        logger.warning(f"{symbol}: 无法获取当前价格，跳过卖出检查")
                        continue
                    
                    avg_price = getattr(p, 'avg_price', current_price)  # 成本价
                    total_volume = p.volume  # 总持仓
                    available_volume = getattr(p, 'enable_amount', p.volume)  # 可用持仓（已考虑T+1规则）
                    
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
                    
                    # 1. 止损：亏损超过5%
                    if pnl_pct < -5:
                        sell_signals.append(True)
                        sell_reasons.append(f"止损(亏损{pnl_pct:.2f}%)")
                    
                    # 2. 止盈：根据市场趋势动态调整止盈阈值
                    # 牛市：20%，震荡市：15%，熊市：10%
                    take_profit_threshold = market_trend.get('take_profit_threshold', 15.0)
                    if pnl_pct > take_profit_threshold:
                        sell_signals.append(True)
                        sell_reasons.append(f"止盈(盈利{pnl_pct:.2f}%，阈值{take_profit_threshold}%)")
                    
                    # 3. 均线死叉：MA5下穿MA20
                    if ma5 and ma20 and ma5 < ma20:
                        # 检查是否刚发生死叉（前一个周期MA5 >= MA20）
                        if len(df) >= 2:
                            prev_ma5 = df['close'].rolling(window=5).mean().iloc[-2]
                            prev_ma20 = df['close'].rolling(window=20).mean().iloc[-2]
                            if prev_ma5 >= prev_ma20:
                                sell_signals.append(True)
                                sell_reasons.append("均线死叉(MA5下穿MA20)")
                    
                    # 4. 价格跌破20日均线且偏离超过2%
                    if ma20 and current_price < ma20:
                        price_diff_pct = ((current_price - ma20) / ma20 * 100) if ma20 > 0 else 0
                        if price_diff_pct < -2:  # 低于MA20超过2%
                            sell_signals.append(True)
                            sell_reasons.append(f"跌破MA20(偏离{price_diff_pct:.2f}%)")
                    
                    # 5. RSI超买：RSI > 70
                    if rsi and rsi > 70:
                        sell_signals.append(True)
                        sell_reasons.append(f"RSI超买({rsi:.2f})")
                    
                    # 6. MACD死叉：MACD下穿信号线
                    if macd is not None and macd_signal is not None:
                        # 检查是否刚发生死叉
                        try:
                            prev_macd = indicator_calc.calculate(df.iloc[:-1], 'MACD_DIF')
                            prev_signal = indicator_calc.calculate(df.iloc[:-1], 'MACD_DEA')
                            if isinstance(prev_macd, (int, float)) and isinstance(prev_signal, (int, float)):
                                if macd < macd_signal and prev_macd >= prev_signal:
                                    sell_signals.append(True)
                                    sell_reasons.append("MACD死叉")
                        except:
                            pass
                    
                    # 7. MACD柱状图转负且持续扩大
                    if macd_hist is not None and macd_hist < 0:
                        sell_signals.append(True)
                        sell_reasons.append(f"MACD柱状图转负({macd_hist:.4f})")
                    
                    # 8. 市场情绪：极端贪婪时考虑止盈卖出
                    if fear_greed_index > 80 and pnl_pct > 5:
                        sell_signals.append(True)
                        sell_reasons.append(f"市场贪婪(恐贪指数{fear_greed_index:.1f})且盈利{pnl_pct:.2f}%")
                    
                    # 9. 恐慌市场：非止损情况下不卖出（除非亏损严重）
                    if fear_greed_index < 20:
                        if pnl_pct >= -3:  # 亏损小于3%，过滤掉非止损信号
                            # 只保留止损信号
                            filtered_signals = []
                            filtered_reasons = []
                            for i, reason in enumerate(sell_reasons):
                                if '止损' in reason:
                                    filtered_signals.append(sell_signals[i])
                                    filtered_reasons.append(reason)
                            sell_signals = filtered_signals
                            sell_reasons = filtered_reasons
                            if not sell_signals:
                                sell_reasons.append(f"恐慌市场(恐贪指数{fear_greed_index:.1f})，非止损不卖出")
                    
                    # 综合判断：满足任一卖出条件即可卖出
                    should_sell = any(sell_signals) if sell_signals else False
                    
                    if should_sell:
                        reason_str = "、".join(sell_reasons)
                        logger.info(f"[多策略卖出] {symbol}: 触发卖出信号 - {reason_str}")
                        # 格式化指标值，处理None情况
                        ma5_str = f"{ma5:.2f}" if ma5 is not None else "N/A"
                        ma20_str = f"{ma20:.2f}" if ma20 is not None else "N/A"
                        rsi_str = f"{rsi:.2f}" if rsi is not None else "N/A"
                        logger.info(f"[多策略卖出] {symbol}: 价格={current_price:.2f}, 成本={avg_price:.2f}, 盈亏={pnl_pct:.2f}%, "
                                   f"MA5={ma5_str}, MA20={ma20_str}, "
                                   f"RSI={rsi_str}, 持仓={available_volume}股")
                        print(f"[多策略卖出] {symbol}: {reason_str}")
                        print(f"  价格={current_price:.2f}, 成本={avg_price:.2f}, 盈亏={pnl_pct:.2f}%, "
                              f"MA5={ma5_str}, MA20={ma20_str}, "
                              f"RSI={rsi_str}")
                        
                        # 执行卖出：只卖出可用持仓（已考虑T+1规则）
                        # 注意：available_volume 已经由券商计算，排除了当日买入的股票
                        if available_volume > 0:
                            await order_manager(symbol, "卖", current_price, available_volume, account)
                            logger.info(f"[多策略卖出] {symbol}: 已提交卖出订单，数量={available_volume}股（总持仓{total_volume}股），价格={current_price:.2f}")
                        else:
                            logger.warning(f"[多策略卖出] {symbol}: 无可用持仓（T+1限制），无法卖出")
                            print(f"[T+1限制] {symbol}: 当日买入的股票不能当日卖出，无法执行卖出订单")
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
                logger.warning(f"{symbol}: 可用资金不足，返回最小买入单位 {min_unit}")
                return min_unit
        
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
                logger.warning(f"{symbol}: 可用资金不足，返回最小买入单位 {min_unit}")
                return min_unit
        
        logger.info(f"{symbol}: 计算买入股数 - 可用资金={available_cash:.2f}, 价格={current_price:.2f}, "
                   f"建议股数={shares}, 预计金额={shares * current_price:.2f}")
        
        return shares
        
    except Exception as e:
        logger.error(f"{symbol}: 计算买入股数失败: {e}，返回最小买入单位 {min_unit}", exc_info=True)
        return min_unit
def get_latest_price_func(symbol, xt_trader=None):
    from main import get_latest_price_func as main_get_latest_price_func
    return main_get_latest_price_func(symbol)
