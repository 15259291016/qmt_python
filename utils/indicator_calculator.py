#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标计算工具类
支持 tick 数据、分钟数据、日线数据的技术指标计算

作者: AI Assistant
创建时间: 2025-01-26
版本: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
import logging

# 尝试导入 talib，如果没有则使用纯 Python 实现
try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
    logging.warning("TA-Lib 未安装，将使用纯 Python 实现技术指标")


class IndicatorCalculator:
    """技术指标计算工具类"""
    
    def __init__(self):
        """初始化指标计算器"""
        self.logger = logging.getLogger(__name__)
        self._supported_indicators = self._init_supported_indicators()
    
    def _init_supported_indicators(self) -> Dict[str, Dict[str, Any]]:
        """初始化支持的指标列表"""
        return {
            # 移动平均线
            'MA5': {
                'name': '5日移动平均线',
                'description': '5日简单移动平均线',
                'params': {'period': 5},
                'requires': ['close']
            },
            'MA10': {
                'name': '10日移动平均线',
                'description': '10日简单移动平均线',
                'params': {'period': 10},
                'requires': ['close']
            },
            'MA20': {
                'name': '20日移动平均线',
                'description': '20日简单移动平均线',
                'params': {'period': 20},
                'requires': ['close']
            },
            'MA60': {
                'name': '60日移动平均线',
                'description': '60日简单移动平均线',
                'params': {'period': 60},
                'requires': ['close']
            },
            'EMA12': {
                'name': '12日指数移动平均线',
                'description': '12日指数移动平均线',
                'params': {'period': 12},
                'requires': ['close']
            },
            'EMA26': {
                'name': '26日指数移动平均线',
                'description': '26日指数移动平均线',
                'params': {'period': 26},
                'requires': ['close']
            },
            
            # MACD 指标
            'MACD': {
                'name': 'MACD指标',
                'description': 'MACD指标（快线、慢线、柱状图）',
                'params': {'fast': 12, 'slow': 26, 'signal': 9},
                'requires': ['close'],
                'returns': ['macd', 'signal', 'histogram']
            },
            'MACD_DIF': {
                'name': 'MACD快线',
                'description': 'MACD快线（DIF）',
                'params': {'fast': 12, 'slow': 26},
                'requires': ['close']
            },
            'MACD_DEA': {
                'name': 'MACD慢线',
                'description': 'MACD慢线（DEA）',
                'params': {'fast': 12, 'slow': 26, 'signal': 9},
                'requires': ['close']
            },
            'MACD_HIST': {
                'name': 'MACD柱状图',
                'description': 'MACD柱状图',
                'params': {'fast': 12, 'slow': 26, 'signal': 9},
                'requires': ['close']
            },
            
            # RSI 指标
            'RSI': {
                'name': 'RSI相对强弱指标',
                'description': 'RSI相对强弱指标（默认14周期）',
                'params': {'period': 14},
                'requires': ['close']
            },
            'RSI6': {
                'name': 'RSI6',
                'description': '6周期RSI指标',
                'params': {'period': 6},
                'requires': ['close']
            },
            'RSI12': {
                'name': 'RSI12',
                'description': '12周期RSI指标',
                'params': {'period': 12},
                'requires': ['close']
            },
            'RSI24': {
                'name': 'RSI24',
                'description': '24周期RSI指标',
                'params': {'period': 24},
                'requires': ['close']
            },
            
            # 布林带
            'BOLL': {
                'name': '布林带',
                'description': '布林带（上轨、中轨、下轨）',
                'params': {'period': 20, 'std': 2},
                'requires': ['close'],
                'returns': ['upper', 'middle', 'lower']
            },
            'BOLL_UPPER': {
                'name': '布林带上轨',
                'description': '布林带上轨',
                'params': {'period': 20, 'std': 2},
                'requires': ['close']
            },
            'BOLL_MIDDLE': {
                'name': '布林带中轨',
                'description': '布林带中轨',
                'params': {'period': 20},
                'requires': ['close']
            },
            'BOLL_LOWER': {
                'name': '布林带下轨',
                'description': '布林带下轨',
                'params': {'period': 20, 'std': 2},
                'requires': ['close']
            },
            
            # KDJ 指标
            'KDJ': {
                'name': 'KDJ指标',
                'description': 'KDJ随机指标（K值、D值、J值）',
                'params': {'k_period': 9, 'd_period': 3, 'j_period': 3},
                'requires': ['high', 'low', 'close'],
                'returns': ['k', 'd', 'j']
            },
            'KDJ_K': {
                'name': 'KDJ K值',
                'description': 'KDJ K值',
                'params': {'k_period': 9, 'd_period': 3},
                'requires': ['high', 'low', 'close']
            },
            'KDJ_D': {
                'name': 'KDJ D值',
                'description': 'KDJ D值',
                'params': {'k_period': 9, 'd_period': 3, 'j_period': 3},
                'requires': ['high', 'low', 'close']
            },
            'KDJ_J': {
                'name': 'KDJ J值',
                'description': 'KDJ J值',
                'params': {'k_period': 9, 'd_period': 3, 'j_period': 3},
                'requires': ['high', 'low', 'close']
            },
            
            # ATR 指标
            'ATR': {
                'name': 'ATR平均真实波幅',
                'description': 'ATR平均真实波幅',
                'params': {'period': 14},
                'requires': ['high', 'low', 'close']
            },
            
            # CCI 指标
            'CCI': {
                'name': 'CCI商品通道指标',
                'description': 'CCI商品通道指标',
                'params': {'period': 20},
                'requires': ['high', 'low', 'close']
            },
            
            # 威廉指标
            'WILLR': {
                'name': '威廉指标',
                'description': '威廉指标（Williams %R）',
                'params': {'period': 14},
                'requires': ['high', 'low', 'close']
            },
            
            # 成交量指标
            'VOLUME_MA5': {
                'name': '成交量5日均线',
                'description': '成交量5日移动平均',
                'params': {'period': 5},
                'requires': ['volume']
            },
            'VOLUME_MA10': {
                'name': '成交量10日均线',
                'description': '成交量10日移动平均',
                'params': {'period': 10},
                'requires': ['volume']
            },
            'VOLUME_RATIO': {
                'name': '量比',
                'description': '当前成交量与5日均量的比值',
                'params': {'period': 5},
                'requires': ['volume']
            },
            
            # 价格相关
            'INTRADAY_LOW': {
                'name': '日内最低价',
                'description': '当日最低价',
                'params': {},
                'requires': ['low']
            },
            'INTRADAY_HIGH': {
                'name': '日内最高价',
                'description': '当日最高价',
                'params': {},
                'requires': ['high']
            },
            'PRICE_RANGE': {
                'name': '价格波动幅度',
                'description': '（最高价-最低价）/最低价 * 100',
                'params': {},
                'requires': ['high', 'low']
            }
        }
    
    def help(self) -> Dict[str, Dict[str, Any]]:
        """
        返回所有支持的指标列表
        
        Returns:
            Dict: 支持的指标字典，格式为 {指标代码: {名称, 描述, 参数, 所需字段}}
            
        Example:
            >>> calculator = IndicatorCalculator()
            >>> indicators = calculator.help()
            >>> print(indicators['MA5']['name'])
            5日移动平均线
        """
        return self._supported_indicators.copy()
    
    def calculate(self, data: pd.DataFrame, indicator: str, **kwargs) -> Union[float, Dict[str, float], pd.Series]:
        """
        计算指定指标
        
        Args:
            data: 股票数据（DataFrame），必须包含以下列之一：
                  - tick数据：'last_price' 或 'price'（价格），'volume'（成交量），'time'（时间）
                  - 分钟/日线数据：'open', 'high', 'low', 'close', 'volume'
            indicator: 指标名称（如 'MA5', 'RSI', 'MACD' 等）
            **kwargs: 指标参数（可选，会覆盖默认参数）
            
        Returns:
            - 单个指标值：返回 float
            - 多个指标值：返回 Dict[str, float]（如 MACD 返回 {'macd': ..., 'signal': ..., 'histogram': ...}）
            - 序列数据：返回 pd.Series（如果需要历史值）
            
        Example:
            >>> calculator = IndicatorCalculator()
            >>> # 计算MA5
            >>> ma5 = calculator.calculate(df, 'MA5')
            >>> # 计算MACD（返回多个值）
            >>> macd = calculator.calculate(df, 'MACD')
            >>> print(macd['macd'], macd['signal'], macd['histogram'])
        """
        if indicator not in self._supported_indicators:
            raise ValueError(f"不支持的指标: {indicator}。使用 help() 查看支持的指标列表")
        
        indicator_info = self._supported_indicators[indicator]
        
        # 预处理数据（如果是tick数据，需要转换为OHLCV格式）
        df = self._preprocess_data(data.copy())
        
        # 检查所需字段
        required_fields = indicator_info['requires']
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            raise ValueError(f"缺少必需字段: {missing_fields}。指标 {indicator} 需要: {required_fields}")
        
        # 合并参数（kwargs 优先）
        params = {**indicator_info['params'], **kwargs}
        
        # 计算指标
        try:
            result = self._calculate_indicator(df, indicator, params)
            
            # 如果返回多个值，返回字典；否则返回最后一个值
            if isinstance(result, dict):
                return {k: float(v.iloc[-1]) if isinstance(v, pd.Series) else float(v) 
                       for k, v in result.items()}
            elif isinstance(result, pd.Series):
                # 检查是否为空
                if len(result) == 0 or result.isna().all():
                    raise ValueError(f"指标 {indicator} 计算结果为空，可能需要更多历史数据")
                return float(result.iloc[-1])
            elif isinstance(result, (int, float, np.number)):
                return float(result)
            else:
                return float(result)
                
        except Exception as e:
            self.logger.error(f"计算指标 {indicator} 失败: {e}", exc_info=True)
            raise
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        预处理数据，将tick数据转换为OHLCV格式
        
        Args:
            data: 原始数据
            
        Returns:
            处理后的DataFrame，包含 open, high, low, close, volume 列
        """
        # 如果已经是OHLCV格式，直接返回
        if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
            return data
        
        # 如果是tick数据，转换为分钟级OHLCV
        if 'last_price' in data.columns or 'price' in data.columns:
            price_col = 'last_price' if 'last_price' in data.columns else 'price'
            volume_col = 'volume' if 'volume' in data.columns else 'vol'
            time_col = 'time' if 'time' in data.columns else 'tick_time'
            
            # 确保有时间列
            if time_col not in data.columns:
                data.index = pd.to_datetime(data.index)
                time_col = data.index.name if data.index.name else 'time'
            
            # 转换为分钟级数据
            data[time_col] = pd.to_datetime(data[time_col])
            data = data.set_index(time_col)
            
            # 按分钟聚合
            ohlcv = data.groupby(pd.Grouper(freq='1min')).agg({
                price_col: ['first', 'max', 'min', 'last'],
                volume_col: 'sum'
            })
            
            ohlcv.columns = ['open', 'high', 'low', 'close', 'volume']
            ohlcv = ohlcv.dropna()
            
            return ohlcv.reset_index()
        
        # 如果数据格式不明确，尝试推断
        if 'close' in data.columns:
            # 假设是日线或分钟数据，但缺少某些列
            if 'high' not in data.columns:
                data['high'] = data['close']
            if 'low' not in data.columns:
                data['low'] = data['close']
            if 'open' not in data.columns:
                data['open'] = data['close']
            if 'volume' not in data.columns and 'vol' in data.columns:
                data['volume'] = data['vol']
            elif 'volume' not in data.columns:
                data['volume'] = 0
            
            return data
        
        raise ValueError("无法识别数据格式。需要包含 'open/high/low/close' 或 'last_price/price' 列")
    
    def _calculate_indicator(self, df: pd.DataFrame, indicator: str, params: Dict[str, Any]) -> Union[float, Dict[str, float], pd.Series]:
        """内部方法：计算具体指标"""
        
        if HAS_TALIB:
            try:
                return self._calculate_with_talib(df, indicator, params)
            except Exception as e:
                # 如果 talib 计算失败，回退到 pandas 实现
                self.logger.warning(f"TA-Lib 计算 {indicator} 失败，回退到 pandas 实现: {e}")
                return self._calculate_with_pandas(df, indicator, params)
        else:
            return self._calculate_with_pandas(df, indicator, params)
    
    def _calculate_with_talib(self, df: pd.DataFrame, indicator: str, params: Dict[str, Any]) -> Union[float, Dict[str, float], pd.Series]:
        """使用 TA-Lib 计算指标"""
        close = df['close'].values.astype(np.float64)
        high = df['high'].values.astype(np.float64) if 'high' in df.columns else None
        low = df['low'].values.astype(np.float64) if 'low' in df.columns else None
        volume = df['volume'].values.astype(np.float64) if 'volume' in df.columns else None
        
        # 注意：必须先检查 MACD 相关指标，因为它们以 'MA' 开头
        if indicator == 'MACD':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            return {
                'macd': pd.Series(macd),
                'signal': pd.Series(macd_signal),
                'histogram': pd.Series(macd_hist)
            }
        
        elif indicator == 'MACD_DIF':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            macd, _, _ = talib.MACD(close, fastperiod=fast, slowperiod=slow)
            return pd.Series(macd)
        
        elif indicator == 'MACD_DEA':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            _, macd_signal, _ = talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            return pd.Series(macd_signal)
        
        elif indicator == 'MACD_HIST':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            _, _, macd_hist = talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            return pd.Series(macd_hist)
        
        # 移动平均线（必须在 MACD 之后检查）
        elif indicator.startswith('MA'):
            period = params.get('period', 5)
            return pd.Series(talib.SMA(close, timeperiod=period))
        
        elif indicator.startswith('EMA'):
            period = params.get('period', 12)
            return pd.Series(talib.EMA(close, timeperiod=period))
        
        elif indicator.startswith('RSI'):
            period = params.get('period', 14)
            return pd.Series(talib.RSI(close, timeperiod=period))
        
        elif indicator.startswith('BOLL'):
            period = params.get('period', 20)
            std = params.get('std', 2)
            upper, middle, lower = talib.BBANDS(close, timeperiod=period, nbdevup=std, nbdevdn=std)
            
            if indicator == 'BOLL':
                return {
                    'upper': pd.Series(upper),
                    'middle': pd.Series(middle),
                    'lower': pd.Series(lower)
                }
            elif indicator == 'BOLL_UPPER':
                return pd.Series(upper)
            elif indicator == 'BOLL_MIDDLE':
                return pd.Series(middle)
            elif indicator == 'BOLL_LOWER':
                return pd.Series(lower)
        
        elif indicator.startswith('KDJ'):
            k_period = params.get('k_period', 9)
            d_period = params.get('d_period', 3)
            j_period = params.get('j_period', 3)
            k, d = talib.STOCH(high, low, close, fastk_period=k_period, slowk_period=d_period, slowd_period=j_period)
            j = 3 * k - 2 * d
            
            if indicator == 'KDJ':
                return {
                    'k': pd.Series(k),
                    'd': pd.Series(d),
                    'j': pd.Series(j)
                }
            elif indicator == 'KDJ_K':
                return pd.Series(k)
            elif indicator == 'KDJ_D':
                return pd.Series(d)
            elif indicator == 'KDJ_J':
                return pd.Series(j)
        
        elif indicator == 'ATR':
            period = params.get('period', 14)
            return pd.Series(talib.ATR(high, low, close, timeperiod=period))
        
        elif indicator == 'CCI':
            period = params.get('period', 20)
            return pd.Series(talib.CCI(high, low, close, timeperiod=period))
        
        elif indicator == 'WILLR':
            period = params.get('period', 14)
            return pd.Series(talib.WILLR(high, low, close, timeperiod=period))
        
        elif indicator.startswith('VOLUME_MA'):
            period = params.get('period', 5)
            return pd.Series(talib.SMA(volume, timeperiod=period))
        
        elif indicator == 'VOLUME_RATIO':
            period = params.get('period', 5)
            volume_ma = talib.SMA(volume, timeperiod=period)
            return pd.Series(volume / volume_ma)
        
        elif indicator == 'INTRADAY_LOW':
            return df['low'].min()
        
        elif indicator == 'INTRADAY_HIGH':
            return df['high'].max()
        
        elif indicator == 'PRICE_RANGE':
            return ((df['high'] - df['low']) / df['low'] * 100).iloc[-1]
        
        # 如果 TA-Lib 不支持，回退到 pandas 实现
        return self._calculate_with_pandas(df, indicator, params)
    
    def _calculate_with_pandas(self, df: pd.DataFrame, indicator: str, params: Dict[str, Any]) -> Union[float, Dict[str, float], pd.Series]:
        """使用 pandas 计算指标（纯 Python 实现）"""
        
        # 注意：必须先检查 MACD 相关指标，因为它们以 'MA' 开头
        if indicator == 'MACD':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signal).mean()
            macd_hist = macd - macd_signal
            return {
                'macd': macd,
                'signal': macd_signal,
                'histogram': macd_hist
            }
        
        elif indicator == 'MACD_DIF':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            return ema_fast - ema_slow
        
        elif indicator == 'MACD_DEA':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            return macd.ewm(span=signal).mean()
        
        elif indicator == 'MACD_HIST':
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signal).mean()
            return macd - macd_signal
        
        # 移动平均线（必须在 MACD 之后检查）
        elif indicator.startswith('MA'):
            period = params.get('period', 5)
            return df['close'].rolling(window=period).mean()
        
        elif indicator.startswith('EMA'):
            period = params.get('period', 12)
            return df['close'].ewm(span=period).mean()
        
        elif indicator.startswith('RSI'):
            period = params.get('period', 14)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        elif indicator.startswith('BOLL'):
            period = params.get('period', 20)
            std = params.get('std', 2)
            middle = df['close'].rolling(period).mean()
            std_val = df['close'].rolling(period).std()
            upper = middle + (std_val * std)
            lower = middle - (std_val * std)
            
            if indicator == 'BOLL':
                return {
                    'upper': upper,
                    'middle': middle,
                    'lower': lower
                }
            elif indicator == 'BOLL_UPPER':
                return upper
            elif indicator == 'BOLL_MIDDLE':
                return middle
            elif indicator == 'BOLL_LOWER':
                return lower
        
        elif indicator.startswith('KDJ'):
            k_period = params.get('k_period', 9)
            d_period = params.get('d_period', 3)
            j_period = params.get('j_period', 3)
            low_min = df['low'].rolling(k_period).min()
            high_max = df['high'].rolling(k_period).max()
            rsv = (df['close'] - low_min) / (high_max - low_min) * 100
            k = rsv.ewm(alpha=1/d_period).mean()
            d = k.ewm(alpha=1/j_period).mean()
            j = 3 * k - 2 * d
            
            if indicator == 'KDJ':
                return {
                    'k': k,
                    'd': d,
                    'j': j
                }
            elif indicator == 'KDJ_K':
                return k
            elif indicator == 'KDJ_D':
                return d
            elif indicator == 'KDJ_J':
                return j
        
        elif indicator == 'ATR':
            period = params.get('period', 14)
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            return true_range.rolling(period).mean()
        
        elif indicator == 'CCI':
            period = params.get('period', 20)
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            sma = typical_price.rolling(period).mean()
            mean_deviation = typical_price.rolling(period).apply(
                lambda x: np.mean(np.abs(x - x.mean()))
            )
            return (typical_price - sma) / (0.015 * mean_deviation)
        
        elif indicator == 'WILLR':
            period = params.get('period', 14)
            highest_high = df['high'].rolling(period).max()
            lowest_low = df['low'].rolling(period).min()
            return -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        
        elif indicator.startswith('VOLUME_MA'):
            period = params.get('period', 5)
            return df['volume'].rolling(window=period).mean()
        
        elif indicator == 'VOLUME_RATIO':
            period = params.get('period', 5)
            volume_ma = df['volume'].rolling(window=period).mean()
            return df['volume'] / volume_ma
        
        elif indicator == 'INTRADAY_LOW':
            return df['low'].min()
        
        elif indicator == 'INTRADAY_HIGH':
            return df['high'].max()
        
        elif indicator == 'PRICE_RANGE':
            return ((df['high'] - df['low']) / df['low'] * 100).iloc[-1]
        
        raise ValueError(f"不支持的指标: {indicator}")


# 使用示例
if __name__ == '__main__':
    # 创建计算器实例
    calculator = IndicatorCalculator()
    
    # 查看所有支持的指标
    print("=" * 60)
    print("支持的指标列表：")
    print("=" * 60)
    indicators = calculator.help()
    for code, info in indicators.items():
        print(f"{code:20s} - {info['name']:20s} - {info['description']}")
    
    print("\n" + "=" * 60)
    print("使用示例：")
    print("=" * 60)
    
    # 创建示例数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    df = pd.DataFrame({
        'open': prices + np.random.randn(100) * 0.5,
        'high': prices + np.abs(np.random.randn(100) * 1),
        'low': prices - np.abs(np.random.randn(100) * 1),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    # 计算指标示例
    print("\n1. 计算MA5:")
    ma5 = calculator.calculate(df, 'MA5')
    print(f"   MA5 = {ma5:.2f}")
    
    print("\n2. 计算RSI:")
    rsi = calculator.calculate(df, 'RSI')
    print(f"   RSI = {rsi:.2f}")
    
    print("\n3. 计算MACD:")
    macd = calculator.calculate(df, 'MACD')
    print(f"   MACD = {macd['macd']:.2f}, Signal = {macd['signal']:.2f}, Histogram = {macd['histogram']:.2f}")
    
    print("\n4. 计算日内最低价:")
    intraday_low = calculator.calculate(df, 'INTRADAY_LOW')
    print(f"   日内最低价 = {intraday_low:.2f}")

