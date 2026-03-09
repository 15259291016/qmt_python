# coding=utf-8
"""
市场择时引擎 - 根据上证指数实时判断买点
"""
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, time
import pandas as pd

logger = logging.getLogger(__name__)


class MarketTimingEngine:
    """
    市场择时引擎：根据上证指数等市场指标实时判断买入时机
    
    择时策略：
    1. 均线系统：MA5上穿MA20（金叉）
    2. RSI指标：RSI < 30（超卖）或 30 < RSI < 50（偏弱但未超卖）
    3. MACD指标：MACD金叉或柱状图转正
    4. 成交量：放量上涨（量价配合）
    5. 价格位置：价格站上MA5或接近MA20
    6. 市场情绪：恐贪指数 < 50（市场恐慌或中性）
    
    买入信号触发条件（满足任一即可）：
    - 强买入：均线金叉 + RSI超卖 + MACD金叉 + 放量
    - 中等买入：均线金叉 + RSI偏弱 + 价格站上MA5
    - 弱买入：RSI超卖 + 市场恐慌（恐贪指数<30）
    """
    
    def __init__(
        self,
        index_code: str = '000001.SH',  # 上证指数
        check_interval: int = 30,  # 检查间隔（秒）
        min_buy_interval: int = 300,  # 最小买入间隔（秒），防止频繁交易
    ):
        """
        初始化市场择时引擎
        
        Args:
            index_code: 市场指数代码（默认上证指数）
            check_interval: 市场检查间隔（秒）
            min_buy_interval: 最小买入间隔（秒），防止频繁交易
        """
        self.index_code = index_code
        self.check_interval = check_interval
        self.min_buy_interval = min_buy_interval
        
        # 记录上次买入信号时间
        self.last_buy_signal_time = None
        
        # 记录历史信号（用于趋势判断）
        self.signal_history = []
        self.max_history_length = 20  # 保留最近20次信号
        
        logger.info(f"[市场择时] 初始化完成 - 指数={index_code}, 检查间隔={check_interval}秒, 最小买入间隔={min_buy_interval}秒")
    
    def check_market_timing(
        self,
        get_history_func: Callable,
        fear_greed_index: float,
        technical_analyzer
    ) -> Dict[str, Any]:
        """
        检查市场择时信号
        
        Args:
            get_history_func: 获取历史数据的函数
            fear_greed_index: 恐贪指数
            technical_analyzer: 技术分析器
            
        Returns:
            {
                'should_buy': bool,  # 是否应该买入
                'signal_strength': str,  # 信号强度：'strong'/'medium'/'weak'/'none'
                'confidence': float,  # 置信度 0.0-1.0
                'reasons': List[str],  # 买入理由
                'indicators': Dict,  # 技术指标详情
                'next_check_time': datetime  # 下次检查时间
            }
        """
        try:
            # 1. 检查是否在交易时间
            current_time = datetime.now()
            if not self._is_trading_time(current_time.time()):
                return {
                    'should_buy': False,
                    'signal_strength': 'none',
                    'confidence': 0.0,
                    'reasons': ['非交易时间'],
                    'indicators': {},
                    'next_check_time': current_time
                }
            
            # 2. 检查是否满足最小买入间隔
            if self.last_buy_signal_time:
                time_since_last_buy = (current_time - self.last_buy_signal_time).total_seconds()
                if time_since_last_buy < self.min_buy_interval:
                    remaining = self.min_buy_interval - time_since_last_buy
                    logger.debug(f"[市场择时] 距离上次买入信号仅{time_since_last_buy:.0f}秒，需等待{remaining:.0f}秒")
                    return {
                        'should_buy': False,
                        'signal_strength': 'none',
                        'confidence': 0.0,
                        'reasons': [f'距离上次买入信号过近（{time_since_last_buy:.0f}秒）'],
                        'indicators': {},
                        'next_check_time': current_time
                    }
            
            # 3. 获取市场指数历史数据
            df = get_history_func(self.index_code)
            if df is None or len(df) < 60:
                logger.warning(f"[市场择时] 指数{self.index_code}数据不足，无法判断择时")
                return {
                    'should_buy': False,
                    'signal_strength': 'none',
                    'confidence': 0.0,
                    'reasons': ['市场数据不足'],
                    'indicators': {},
                    'next_check_time': current_time
                }
            
            # 验证数据质量
            if 'close' not in df.columns:
                logger.error(f"[市场择时] 指数{self.index_code}数据缺少close列")
                return {
                    'should_buy': False,
                    'signal_strength': 'none',
                    'confidence': 0.0,
                    'reasons': ['数据格式错误'],
                    'indicators': {},
                    'next_check_time': current_time
                }
            
            # 4. 计算技术指标
            indicators = self._calculate_indicators(df, technical_analyzer)
            if not indicators:
                logger.warning(f"[市场择时] 无法计算技术指标")
                return {
                    'should_buy': False,
                    'signal_strength': 'none',
                    'confidence': 0.0,
                    'reasons': ['技术指标计算失败'],
                    'indicators': {},
                    'next_check_time': current_time
                }
            
            # 5. 判断买入信号
            signal_result = self._judge_buy_signal(indicators, fear_greed_index)
            
            # 6. 记录信号历史
            self.signal_history.append({
                'time': current_time,
                'signal_strength': signal_result['signal_strength'],
                'confidence': signal_result['confidence']
            })
            if len(self.signal_history) > self.max_history_length:
                self.signal_history.pop(0)
            
            # 7. 如果产生买入信号，更新最后买入时间
            if signal_result['should_buy']:
                self.last_buy_signal_time = current_time
                logger.info(f"[市场择时] 产生买入信号 - 强度={signal_result['signal_strength']}, "
                           f"置信度={signal_result['confidence']:.2f}, 理由={signal_result['reasons']}")
            
            signal_result['indicators'] = indicators
            signal_result['next_check_time'] = current_time
            
            return signal_result
            
        except Exception as e:
            logger.error(f"[市场择时] 检查市场择时失败: {e}", exc_info=True)
            return {
                'should_buy': False,
                'signal_strength': 'none',
                'confidence': 0.0,
                'reasons': [f'择时检查异常: {str(e)}'],
                'indicators': {},
                'next_check_time': datetime.now()
            }
    
    def _calculate_indicators(self, df: pd.DataFrame, technical_analyzer=None) -> Optional[Dict[str, Any]]:
        """
        计算技术指标
        
        Args:
            df: 历史数据DataFrame
            technical_analyzer: 技术分析器（可选，当前未使用）
            
        Returns:
            技术指标字典，失败返回None
        """
        try:
            from utils.indicator_calculator import IndicatorCalculator
            
            indicator_calc = IndicatorCalculator()
            
            # 基础指标
            ma5 = df['close'].rolling(window=5).mean().iloc[-1]
            ma20 = df['close'].rolling(window=20).mean().iloc[-1]
            ma60 = df['close'].rolling(window=60).mean().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # 前一日均线（用于判断金叉/死叉）
            prev_ma5 = df['close'].rolling(window=5).mean().iloc[-2] if len(df) >= 2 else ma5
            prev_ma20 = df['close'].rolling(window=20).mean().iloc[-2] if len(df) >= 2 else ma20
            
            # RSI指标
            try:
                rsi = indicator_calc.calculate(df, 'RSI')
                rsi = float(rsi) if rsi is not None else None
            except Exception as e:
                logger.debug(f"[市场择时] RSI计算失败: {e}")
                rsi = None
            
            # MACD指标
            try:
                macd_result = indicator_calc.calculate(df, 'MACD')
                if isinstance(macd_result, dict):
                    macd = macd_result.get('macd')
                    macd_signal = macd_result.get('signal')
                    macd_hist = macd_result.get('histogram')
                else:
                    macd = macd_signal = macd_hist = None
            except Exception as e:
                logger.debug(f"[市场择时] MACD计算失败: {e}")
                macd = macd_signal = macd_hist = None
            
            # 成交量指标
            if 'volume' in df.columns and len(df) >= 20:
                vol_ma5 = df['volume'].iloc[-5:].mean()
                vol_ma20 = df['volume'].iloc[-20:].mean()
                vol_ratio = vol_ma5 / vol_ma20 if vol_ma20 > 0 else 1.0
            else:
                vol_ratio = 1.0
            
            # 价格变化
            price_change_5d = ((current_price / df['close'].iloc[-5] - 1) * 100) if len(df) >= 5 else 0
            
            return {
                'ma5': float(ma5),
                'ma20': float(ma20),
                'ma60': float(ma60),
                'prev_ma5': float(prev_ma5),
                'prev_ma20': float(prev_ma20),
                'current_price': float(current_price),
                'rsi': rsi,
                'macd': macd,
                'macd_signal': macd_signal,
                'macd_hist': macd_hist,
                'vol_ratio': float(vol_ratio),
                'price_change_5d': float(price_change_5d)
            }
            
        except Exception as e:
            logger.error(f"[市场择时] 计算技术指标失败: {e}", exc_info=True)
            return None
    
    def _judge_buy_signal(self, indicators: Dict[str, Any], fear_greed_index: float) -> Dict[str, Any]:
        """
        判断买入信号（优化版：更容易在低点买入）
        
        Returns:
            {
                'should_buy': bool,
                'signal_strength': str,  # 'strong'/'medium'/'weak'/'none'
                'confidence': float,
                'reasons': List[str]
            }
        """
        reasons = []
        score = 0.0  # 综合得分
        
        ma5 = indicators['ma5']
        ma20 = indicators['ma20']
        ma60 = indicators['ma60']
        prev_ma5 = indicators['prev_ma5']
        prev_ma20 = indicators['prev_ma20']
        current_price = indicators['current_price']
        rsi = indicators.get('rsi')
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        macd_hist = indicators.get('macd_hist')
        vol_ratio = indicators['vol_ratio']
        price_change_5d = indicators['price_change_5d']
        
        # ========== 1. 均线系统（权重25%，降低权重让其他因素更重要） ==========
        # 金叉：MA5上穿MA20
        if prev_ma5 <= prev_ma20 and ma5 > ma20:
            score += 0.25
            reasons.append("均线金叉(MA5上穿MA20)")
            logger.info(f"[市场择时] 检测到均线金叉：MA5={ma5:.2f}, MA20={ma20:.2f}")
        # 多头排列：MA5 > MA20 > MA60
        elif ma5 > ma20 > ma60:
            score += 0.18
            reasons.append("均线多头排列")
        # 价格站上MA5
        elif current_price > ma5 and ma5 > ma20:
            score += 0.12
            reasons.append("价格站上MA5")
        # 价格接近MA20（±2%）
        elif ma20 > 0 and abs(current_price - ma20) / ma20 < 0.02:
            score += 0.08
            reasons.append("价格接近MA20支撑")
        # 新增：价格跌破MA20但接近MA60（可能是低点）
        elif current_price < ma20 and ma60 > 0 and abs(current_price - ma60) / ma60 < 0.03:
            score += 0.1
            reasons.append("价格接近MA60支撑（潜在低点）")
        
        # ========== 2. RSI指标（权重30%，提高权重让超卖更容易触发） ==========
        if rsi is not None:
            if rsi < 25:
                # 极度超卖，大幅加分（限制在30%权重内）
                score += 0.30
                reasons.append(f"RSI极度超卖({rsi:.1f})")
                logger.info(f"[市场择时] RSI极度超卖：{rsi:.1f}，强烈买入信号")
            elif rsi < 30:
                score += 0.25
                reasons.append(f"RSI超卖({rsi:.1f})")
                logger.info(f"[市场择时] RSI超卖：{rsi:.1f}")
            elif 30 <= rsi < 35:
                score += 0.18
                reasons.append(f"RSI偏弱({rsi:.1f})")
            elif 35 <= rsi < 45:
                score += 0.10
                reasons.append(f"RSI中性偏弱({rsi:.1f})")
        
        # ========== 3. 价格跌幅触发（新增，权重20%） ==========
        if price_change_5d < -3:
            # 5日跌幅超过3%，可能是低点
            if price_change_5d < -8:
                score += 0.20
                reasons.append(f"大幅下跌({price_change_5d:.1f}%，可能是低点)")
                logger.info(f"[市场择时] 检测到大幅下跌：{price_change_5d:.1f}%")
            elif price_change_5d < -5:
                score += 0.15
                reasons.append(f"明显下跌({price_change_5d:.1f}%)")
            else:
                score += 0.10
                reasons.append(f"小幅下跌({price_change_5d:.1f}%)")
        elif -1 <= price_change_5d <= 1:
            # 止跌企稳（横盘），也是潜在买点
            score += 0.05
            reasons.append(f"止跌企稳({price_change_5d:.1f}%)")
        
        # ========== 4. MACD指标（权重15%，降低权重） ==========
        if macd is not None and macd_signal is not None:
            # MACD金叉
            if macd > macd_signal:
                score += 0.12
                reasons.append("MACD金叉")
            # MACD柱状图转正
            if macd_hist is not None and macd_hist > 0:
                score += 0.03
                reasons.append("MACD柱状图转正")
        
        # ========== 5. 成交量（权重10%，降低权重） ==========
        if vol_ratio > 1.2:
            if price_change_5d > 0:
                score += 0.1
                reasons.append(f"放量上涨(量比{vol_ratio:.2f})")
            elif price_change_5d < -3:
                # 放量下跌可能是恐慌性抛售，反而是买入机会
                score += 0.08
                reasons.append(f"放量下跌(量比{vol_ratio:.2f}，可能是恐慌性抛售)")
            else:
                score += 0.03
                reasons.append(f"放量(量比{vol_ratio:.2f})")
        
        # ========== 6. 市场情绪（权重15%，提高权重） ==========
        if fear_greed_index < 20:
            # 极度恐慌，大幅加分（限制在15%权重内）
            score += 0.15
            reasons.append(f"市场极度恐慌(恐贪指数{fear_greed_index:.1f}，抄底机会)")
            logger.info(f"[市场择时] 市场极度恐慌：{fear_greed_index:.1f}")
        elif fear_greed_index < 30:
            score += 0.12
            reasons.append(f"市场恐慌(恐贪指数{fear_greed_index:.1f})")
        elif fear_greed_index < 40:
            score += 0.08
            reasons.append(f"市场偏弱(恐贪指数{fear_greed_index:.1f})")
        elif fear_greed_index < 50:
            score += 0.04
            reasons.append(f"市场中性偏弱(恐贪指数{fear_greed_index:.1f})")
        
        # ========== 判断信号强度（实盘优化：降低阈值，避免错过低点） ==========
        # 实盘优化：适度降低阈值，在明确低点时买入
        if score >= 0.55:
            signal_strength = 'strong'
            should_buy = True
        elif score >= 0.35:
            signal_strength = 'medium'
            should_buy = True
        elif score >= 0.18:  # 实盘优化：0.18（比保守版0.20低，避免错过明显低点）
            signal_strength = 'weak'
            should_buy = True
        else:
            signal_strength = 'none'
            should_buy = False
        
        confidence = min(score, 1.0)
        
        if should_buy:
            logger.info(f"[市场择时] 买入信号 - 强度={signal_strength}, 得分={score:.2f}, 理由={reasons}")
        else:
            logger.debug(f"[市场择时] 无买入信号 - 得分={score:.2f}, 理由={reasons if reasons else ['无明显信号']}")
        
        return {
            'should_buy': should_buy,
            'signal_strength': signal_strength,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def _is_trading_time(self, current_time: time) -> bool:
        """
        检查是否在交易时间
        
        注意：此方法只检查时间段，不检查是否为交易日（周末、节假日）
        交易日判断由外部 is_trading_time() 函数负责
        """
        # 交易时段：9:30-11:30, 13:00-15:00
        morning_start = time(9, 30)
        morning_end = time(11, 30)
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)
        
        return (morning_start <= current_time <= morning_end) or \
               (afternoon_start <= current_time <= afternoon_end)
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """获取信号统计信息"""
        if not self.signal_history:
            return {
                'total_signals': 0,
                'strong_signals': 0,
                'medium_signals': 0,
                'weak_signals': 0,
                'avg_confidence': 0.0
            }
        
        strong_count = sum(1 for s in self.signal_history if s['signal_strength'] == 'strong')
        medium_count = sum(1 for s in self.signal_history if s['signal_strength'] == 'medium')
        weak_count = sum(1 for s in self.signal_history if s['signal_strength'] == 'weak')
        avg_confidence = sum(s['confidence'] for s in self.signal_history) / len(self.signal_history)
        
        return {
            'total_signals': len(self.signal_history),
            'strong_signals': strong_count,
            'medium_signals': medium_count,
            'weak_signals': weak_count,
            'avg_confidence': avg_confidence,
            'last_signal_time': self.signal_history[-1]['time'] if self.signal_history else None
        }

