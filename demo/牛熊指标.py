#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大智慧牛熊指标计算
根据股票的收盘价和成交量计算牛熊指标，用于判断市场趋势

牛熊指标计算逻辑：
1. 价格趋势：短期均线与长期均线的相对位置
2. 成交量趋势：成交量是否放大，是否配合价格上涨
3. 综合评分：结合价格和成交量给出牛熊评分（0-100）

作者: AI Assistant
创建时间: 2025-01-28
版本: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime, timedelta
import logging
import asyncio

try:
    from xtquant import xtdata
    HAS_XTQUANT = True
except ImportError:
    HAS_XTQUANT = False
    logging.warning("xtquant 未安装，将使用模拟数据")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BullBearIndicator:
    """大智慧牛熊指标计算器"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20, volume_period: int = 5):
        """
        初始化牛熊指标计算器
        
        Args:
            short_period: 短期均线周期，默认5日
            long_period: 长期均线周期，默认20日
            volume_period: 成交量均线周期，默认5日
        """
        self.short_period = short_period
        self.long_period = long_period
        self.volume_period = volume_period
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算牛熊指标
        
        Args:
            df: 股票数据DataFrame，必须包含以下列：
                - time: 时间（日期）
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
        
        Returns:
            添加了牛熊指标列的DataFrame，包含：
                - ma_short: 短期均线
                - ma_long: 长期均线
                - volume_ma: 成交量均线
                - price_trend: 价格趋势（1=上涨，-1=下跌，0=震荡）
                - volume_trend: 成交量趋势（1=放量，-1=缩量，0=平量）
                - bull_bear_score: 牛熊评分（0-100，>50为牛市，<50为熊市）
                - bull_bear_signal: 牛熊信号（'BULL'=牛市，'BEAR'=熊市，'NEUTRAL'=中性）
        """
        if df.empty:
            raise ValueError("数据为空，无法计算牛熊指标")
        
        # 确保数据按时间排序
        if 'time' in df.columns:
            df = df.sort_values('time').copy()
        elif df.index.name == 'time' or isinstance(df.index, pd.DatetimeIndex):
            df = df.sort_index().copy()
        
        # 检查必需列
        required_cols = ['close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"缺少必需列: {missing_cols}")
        
        # 计算移动平均线
        df['ma_short'] = df['close'].rolling(window=self.short_period).mean()
        df['ma_long'] = df['close'].rolling(window=self.long_period).mean()
        df['volume_ma'] = df['volume'].rolling(window=self.volume_period).mean()
        
        # 计算价格趋势
        # 1: 短期均线 > 长期均线（上涨趋势）
        # -1: 短期均线 < 长期均线（下跌趋势）
        # 0: 短期均线 ≈ 长期均线（震荡）
        df['price_trend'] = 0
        ma_diff = df['ma_short'] - df['ma_long']
        ma_diff_pct = (ma_diff / df['ma_long']) * 100
        
        df.loc[ma_diff_pct > 1, 'price_trend'] = 1  # 上涨趋势（短期均线高于长期均线1%以上）
        df.loc[ma_diff_pct < -1, 'price_trend'] = -1  # 下跌趋势（短期均线低于长期均线1%以上）
        
        # 计算成交量趋势
        # 1: 当前成交量 > 均量（放量）
        # -1: 当前成交量 < 均量（缩量）
        # 0: 当前成交量 ≈ 均量（平量）
        df['volume_trend'] = 0
        volume_ratio = df['volume'] / df['volume_ma']
        
        df.loc[volume_ratio > 1.2, 'volume_trend'] = 1  # 放量（成交量大于均量20%以上）
        df.loc[volume_ratio < 0.8, 'volume_trend'] = -1  # 缩量（成交量小于均量20%以下）
        
        # 计算价格变化率
        df['price_change'] = df['close'].pct_change()
        
        # 计算牛熊评分（0-100）
        # 评分规则：
        # 1. 价格趋势（40分）：上涨趋势+40，下跌趋势-40，震荡0
        # 2. 成交量配合（30分）：放量上涨+30，缩量下跌-30，其他情况按比例给分
        # 3. 价格强度（30分）：基于价格变化率和均线位置
        df['bull_bear_score'] = 50.0  # 初始中性分数
        
        # 价格趋势得分（40分）
        price_score = df['price_trend'] * 20  # 上涨+20，下跌-20，震荡0
        
        # 成交量配合得分（30分）
        volume_score = 0
        # 放量上涨：+15分
        volume_score += np.where((df['volume_trend'] == 1) & (df['price_change'] > 0), 15, 0)
        # 缩量下跌：-15分
        volume_score += np.where((df['volume_trend'] == -1) & (df['price_change'] < 0), -15, 0)
        # 放量下跌：-10分（异常情况）
        volume_score += np.where((df['volume_trend'] == 1) & (df['price_change'] < 0), -10, 0)
        # 缩量上涨：+5分（上涨但量能不足）
        volume_score += np.where((df['volume_trend'] == -1) & (df['price_change'] > 0), 5, 0)
        
        # 价格强度得分（30分）
        # 基于价格变化率和均线位置
        strength_score = 0
        # 价格在短期均线之上且上涨：+15分
        strength_score += np.where((df['close'] > df['ma_short']) & (df['price_change'] > 0), 15, 0)
        # 价格在短期均线之下且下跌：-15分
        strength_score += np.where((df['close'] < df['ma_short']) & (df['price_change'] < 0), -15, 0)
        # 价格变化率较大时额外加分/减分
        strength_score += np.where(df['price_change'] > 0.03, 10, 0)  # 涨幅超过3%：+10分
        strength_score += np.where(df['price_change'] < -0.03, -10, 0)  # 跌幅超过3%：-10分
        
        # 综合评分
        df['bull_bear_score'] = 50 + price_score + volume_score + strength_score
        
        # 限制评分范围在0-100
        df['bull_bear_score'] = df['bull_bear_score'].clip(0, 100)
        
        # 生成牛熊信号
        df['bull_bear_signal'] = 'NEUTRAL'
        df.loc[df['bull_bear_score'] > 60, 'bull_bear_signal'] = 'BULL'  # 牛市
        df.loc[df['bull_bear_score'] < 40, 'bull_bear_signal'] = 'BEAR'  # 熊市
        
        return df
    
    def get_latest_signal(self, df: pd.DataFrame) -> Dict:
        """
        获取最新的牛熊信号
        
        Args:
            df: 已计算牛熊指标的DataFrame
        
        Returns:
            包含最新信号的字典
        """
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        return {
            'date': latest.get('time', df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else None),
            'close': float(latest['close']),
            'ma_short': float(latest['ma_short']) if not pd.isna(latest['ma_short']) else None,
            'ma_long': float(latest['ma_long']) if not pd.isna(latest['ma_long']) else None,
            'volume': float(latest['volume']),
            'volume_ma': float(latest['volume_ma']) if not pd.isna(latest['volume_ma']) else None,
            'price_trend': int(latest['price_trend']),
            'volume_trend': int(latest['volume_trend']),
            'bull_bear_score': float(latest['bull_bear_score']),
            'bull_bear_signal': str(latest['bull_bear_signal'])
        }


def get_stock_data_xtquant(symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    使用xtquant获取股票历史数据
    
    Args:
        symbol: 股票代码，如 '000001.SZ' 或 '600000.SH'
        days: 获取最近多少天的数据，默认60天
    
    Returns:
        包含股票数据的DataFrame，如果获取失败返回None
    """
    if not HAS_XTQUANT:
        logger.warning("xtquant 未安装，使用模拟数据")
        return generate_mock_data(days)
    
    try:
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime('%Y%m%d')  # 多获取一些数据以确保有足够数据计算指标
        
        # 下载历史数据（如果需要）
        try:
            xtdata.download_history_data(symbol, period='1d', start_time=start_date, end_time=end_date)
        except Exception as e:
            logger.warning(f"下载历史数据失败: {e}，尝试直接获取")
        
        # 获取历史数据
        data = xtdata.get_market_data(
            field_list=[],
            stock_list=[symbol],
            period='1d',
            start_time=start_date,
            end_time=end_date,
            count=-1
        )
        
        if not data:
            logger.error(f"未获取到 {symbol} 的数据")
            return None
        
        # xtdata.get_market_data 可能返回两种格式：
        # 格式1: {symbol: DataFrame} - 按股票代码组织
        # 格式2: {field: DataFrame} - 按字段组织（字段为键，DataFrame的列为日期）
        df = None
        
        # 尝试格式1：按股票代码组织
        if symbol in data:
            df = pd.DataFrame(data[symbol])
        # 格式2：按字段组织，需要转换
        elif 'time' in data or 'close' in data:
            # 从按字段组织的格式转换为按股票代码组织的格式
            # 数据格式：{field: DataFrame}，其中 DataFrame 的列是日期，行是股票代码
            try:
                # 获取日期列（从任意字段的 DataFrame 列名获取）
                date_columns = None
                if 'time' in data and len(data['time']) > 0:
                    # 从 time 字段获取日期
                    time_df = data['time']
                    if len(time_df.columns) > 0:
                        date_columns = time_df.columns.tolist()
                        # 提取时间值（第一行，因为只查询了一个股票）
                        time_values = time_df.iloc[0].values if len(time_df) > 0 else date_columns
                    else:
                        date_columns = time_df.index.tolist()
                        time_values = time_df.iloc[0].values if len(time_df) > 0 else date_columns
                elif 'close' in data and len(data['close']) > 0:
                    # 从 close 字段的列名获取日期
                    date_columns = data['close'].columns.tolist()
                    time_values = date_columns
                
                if date_columns is None or len(date_columns) == 0:
                    logger.error(f"无法从数据中提取日期信息")
                    return None
                
                # 转换日期格式
                # 日期可能是时间戳（毫秒）或日期字符串（如 20250901）
                try:
                    # 尝试作为时间戳转换
                    if isinstance(time_values[0], (int, float)) and time_values[0] > 1e10:
                        # 时间戳（毫秒）
                        dates = pd.to_datetime(time_values, unit='ms')
                    else:
                        # 尝试作为日期字符串转换
                        dates = pd.to_datetime([str(d) for d in date_columns], format='%Y%m%d', errors='coerce')
                        # 如果转换失败，尝试其他格式
                        if dates.isna().any():
                            dates = pd.to_datetime([str(d) for d in date_columns], errors='coerce')
                except Exception as e:
                    logger.warning(f"日期转换失败，尝试其他方式: {e}")
                    dates = pd.to_datetime([str(d) for d in date_columns], errors='coerce')
                
                # 构建 DataFrame，行是日期，列是字段
                df_data = {}
                has_time_column = False
                
                # 提取各个字段的数据
                field_mapping = {
                    'time': 'time',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                }
                
                for field_key, field_name in field_mapping.items():
                    if field_key in data:
                        field_df = data[field_key]
                        # 提取该股票的数据（第一行，因为只查询了一个股票）
                        if len(field_df) > 0:
                            if len(field_df.columns) > 0:
                                # 列是日期
                                field_values = field_df.iloc[0].values
                            else:
                                # 索引是日期
                                field_values = field_df.iloc[0].values
                            
                            # 如果字段是 time，使用转换后的日期
                            if field_key == 'time':
                                df_data[field_name] = dates.values
                                has_time_column = True
                            else:
                                df_data[field_name] = field_values
                
                # 创建 DataFrame
                if has_time_column:
                    # 如果已经有 time 列，直接创建 DataFrame（不使用日期索引，避免重复）
                    df = pd.DataFrame(df_data)
                    # 确保 time 列是 datetime 类型
                    if 'time' in df.columns:
                        df['time'] = pd.to_datetime(df['time'])
                        # 按时间排序
                        df = df.sort_values('time')
                else:
                    # 如果没有 time 列，使用日期作为索引，然后重置为列
                    df = pd.DataFrame(df_data, index=dates)
                    df.index.name = 'time'
                    # 重置索引，使 time 成为列
                    df = df.reset_index()
                
            except Exception as e:
                logger.error(f"转换数据格式失败: {e}", exc_info=True)
                logger.debug(f"数据格式: {type(data)}, keys: {list(data.keys())[:10] if isinstance(data, dict) else 'N/A'}")
                return None
        
        if df is None or df.empty:
            logger.error(f"无法解析 {symbol} 的数据格式")
            logger.debug(f"数据格式: {type(data)}, keys: {list(data.keys())[:10] if isinstance(data, dict) else 'N/A'}")
            return None
        
        # 标准化列名和时间格式
        if 'time' in df.columns:
            # 如果 time 是时间戳（毫秒），转换为 datetime
            if df['time'].dtype in ['int64', 'float64']:
                df['time'] = pd.to_datetime(df['time'], unit='ms')
            else:
                df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time')
        elif df.index.name == 'time' or isinstance(df.index, pd.DatetimeIndex):
            df = df.sort_index()
        else:
            # 如果没有 time 列，尝试从索引推断
            try:
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
            except:
                pass
        
        # 确保有必需的列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"数据缺少必需列: {missing_cols}")
            logger.debug(f"现有列: {list(df.columns)}")
            return None
        
        # 确保数据类型正确
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 删除无效数据
        df = df.dropna(subset=required_cols)
        
        if df.empty:
            logger.error(f"清理后 {symbol} 的数据为空")
            return None
        
        logger.info(f"成功获取 {symbol} 数据: {len(df)} 条记录")
        return df
        
    except Exception as e:
        logger.error(f"获取 {symbol} 数据失败: {e}")
        return None


async def calculate_market_bull_bear_indicator(
    index_codes: List[str] = None,
    days: int = 60
) -> Dict[str, Any]:
    """
    计算大盘牛熊指标（多指数综合判断）- 异步版本
    
    Args:
        index_codes: 指数代码列表，默认使用主要指数
        days: 获取最近多少天的数据
    
    Returns:
        包含市场趋势判断的字典：
        {
            'market_trend': 'BULL'/'BEAR'/'NEUTRAL',  # 市场趋势
            'confidence': 0.0-1.0,  # 置信度
            'score': 0-100,  # 综合得分
            'details': {...},  # 各指数详情
            'index_count': int,  # 参与计算的指数数量
            'condition': str,  # 市场状态描述
            'description': str  # 详细描述
        }
    """
    if index_codes is None:
        index_codes = ['000001.SH', '399001.SZ', '399006.SZ', '000905.SH']
    
    indicator = BullBearIndicator(short_period=5, long_period=20, volume_period=5)
    index_results = {}
    
    # 对每个指数计算牛熊指标（并行处理）
    async def process_index(index_code: str):
        try:
            # 使用 asyncio.to_thread 将同步IO操作转为异步
            df = await asyncio.to_thread(get_stock_data_xtquant, index_code, days)
            if df is not None and not df.empty:
                df_with_indicator = indicator.calculate(df)
                latest_signal = indicator.get_latest_signal(df_with_indicator)
                return index_code, latest_signal
        except Exception as e:
            # 静默处理错误，不打印日志
            pass
        return index_code, None
    
    # 并行处理所有指数
    tasks = [process_index(code) for code in index_codes]
    results = await asyncio.gather(*tasks)
    
    for index_code, signal in results:
        if signal is not None:
            index_results[index_code] = signal
    
    # 综合判断市场趋势
    if not index_results:
        return {
            'market_trend': 'UNKNOWN',
            'confidence': 0.0,
            'score': 50.0,
            'details': {},
            'index_count': 0,
            'condition': 'UNKNOWN',
            'description': '无法获取指数数据'
        }
    
    # 计算综合得分（加权平均）
    total_score = 0.0
    valid_count = 0
    weights = {
        '000001.SH': 0.4,  # 上证指数权重最高
        '399001.SZ': 0.3,  # 深证成指
        '399006.SZ': 0.2,  # 创业板指
        '000905.SH': 0.1   # 中证500
    }
    
    for index_code, signal in index_results.items():
        weight = weights.get(index_code, 0.25)
        score = signal.get('bull_bear_score', 50.0)
        total_score += score * weight
        valid_count += 1
    
    # 计算平均得分
    avg_score = total_score if valid_count > 0 else 50.0
    
    # 判断市场趋势
    if avg_score > 60:
        market_trend = 'BULL'  # 牛市
        confidence = min((avg_score - 60) / 40, 1.0)  # 60-100映射到0-1
    elif avg_score < 40:
        market_trend = 'BEAR'  # 熊市
        confidence = min((40 - avg_score) / 40, 1.0)  # 0-40映射到1-0
    else:
        market_trend = 'NEUTRAL'  # 震荡市
        # 震荡市的置信度：距离50越远，置信度越高
        confidence = abs(avg_score - 50) / 10  # 40-60映射到0-1
    
    # 判断市场状态
    condition, description = judge_market_condition(avg_score)
    
    return {
        'market_trend': market_trend,
        'confidence': confidence,
        'score': avg_score,
        'details': index_results,
        'index_count': valid_count,
        'condition': condition,
        'description': description
    }


def judge_market_condition(score: float) -> Tuple[str, str]:
    """
    根据牛熊评分判断市场状态
    
    Args:
        score: 牛熊评分（0-100）
    
    Returns:
        (市场状态, 描述)
    """
    if score >= 70:
        return 'STRONG_BULL', '强势牛市：市场情绪极度乐观，多指数上涨，均线多头排列'
    elif score >= 60:
        return 'BULL', '牛市：市场情绪乐观，多指数上涨，均线多头排列'
    elif score >= 50:
        return 'NEUTRAL_BULL', '偏多震荡：市场情绪偏乐观，指数震荡上行'
    elif score >= 40:
        return 'NEUTRAL_BEAR', '偏空震荡：市场情绪偏悲观，指数震荡下行'
    elif score >= 30:
        return 'BEAR', '熊市：市场情绪悲观，多指数下跌，均线空头排列'
    else:
        return 'STRONG_BEAR', '强势熊市：市场情绪极度悲观，多指数大幅下跌'


async def get_bull_bear_indicator(symbol_or_market: str = 'market', days: int = 60) -> Dict[str, Any]:
    """
    获取牛熊指标（统一接口）- 异步函数
    
    Args:
        symbol_or_market: 
            - 'market' 或 '大盘': 返回市场整体牛熊指标
            - 股票代码（如 '000001.SZ'）: 返回该股票和市场整体的牛熊指标
        days: 获取最近多少天的数据，默认60天
    
    Returns:
        如果 symbol_or_market == 'market':
        {
            'type': 'market',
            'market': {
                'market_trend': 'BULL'/'BEAR'/'NEUTRAL',
                'confidence': 0.0-1.0,
                'score': 0-100,
                'condition': str,
                'description': str,
                'details': {...}  # 各指数详情
            }
        }
        
        如果 symbol_or_market 是股票代码:
        {
            'type': 'stock',
            'stock': {
                'symbol': str,
                'bull_bear_score': float,
                'bull_bear_signal': str,
                'price_trend': int,
                'volume_trend': int,
                'close': float,
                'ma_short': float,
                'ma_long': float,
                ...
            },
            'market': {
                'market_trend': 'BULL'/'BEAR'/'NEUTRAL',
                'confidence': 0.0-1.0,
                'score': 0-100,
                'condition': str,
                'description': str,
                ...
            }
        }
    """
    # 判断是市场还是股票代码
    is_market = symbol_or_market.lower() in ['market', '大盘', 'market_index']
    
    # 获取市场牛熊指标
    market_result = await calculate_market_bull_bear_indicator(days=days)
    
    if is_market:
        # 只返回市场指标
        return {
            'type': 'market',
            'market': market_result
        }
    else:
        # 返回股票和市场指标
        symbol = symbol_or_market
        indicator = BullBearIndicator(short_period=5, long_period=20, volume_period=5)
        
        try:
            # 获取股票数据（使用 asyncio.to_thread 将同步IO操作转为异步）
            df = await asyncio.to_thread(get_stock_data_xtquant, symbol, days)
            if df is None or df.empty:
                return {
                    'type': 'stock',
                    'stock': None,
                    'error': f'无法获取股票 {symbol} 的数据',
                    'market': market_result
                }
            
            # 计算股票牛熊指标
            df_with_indicator = indicator.calculate(df)
            stock_signal = indicator.get_latest_signal(df_with_indicator)
            
            return {
                'type': 'stock',
                'stock': {
                    'symbol': symbol,
                    **stock_signal
                },
                'market': market_result
            }
        except Exception as e:
            # 静默处理错误，只返回错误信息
            return {
                'type': 'stock',
                'stock': None,
                'error': str(e),
                'market': market_result
            }


def generate_mock_data(days: int = 60) -> pd.DataFrame:
    """
    生成模拟数据用于测试
    
    Args:
        days: 生成多少天的数据
    
    Returns:
        模拟的股票数据DataFrame
    """
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # 生成模拟价格数据（随机游走）
    np.random.seed(42)
    base_price = 10.0
    price_changes = np.random.randn(days) * 0.02  # 2%的标准差
    prices = base_price * (1 + price_changes).cumprod()
    
    # 生成OHLC数据
    df = pd.DataFrame({
        'time': dates,
        'open': prices * (1 + np.random.randn(days) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(days) * 0.01)),
        'low': prices * (1 - np.abs(np.random.randn(days) * 0.01)),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, days)
    })
    
    return df


async def detect_market_reversal(
    index_code: str = '000001.SH',
    lookback_days: int = 20,
    get_history_func=None
) -> Dict[str, Any]:
    """
    检测市场反转信号
    
    反转判断逻辑：
    1. 趋势变化：从牛市变熊市，或从熊市变牛市
    2. 均线交叉：金叉（死叉）信号
    3. 恐贪指数背离：价格创新低但恐贪指数不创新低（或相反）
    4. 成交量配合：放量突破或放量下跌
    5. 多周期确认：多个时间周期同时出现反转信号
    
    Args:
        index_code: 指数代码，默认 '000001.SH'（上证指数）
        lookback_days: 回看天数，默认20天
        get_history_func: 获取历史数据的函数，如果为None则使用xtquant
    
    Returns:
        {
            'has_reversal': bool,  # 是否出现反转信号
            'reversal_type': str,  # 'BULL_TO_BEAR'（牛转熊）/'BEAR_TO_BULL'（熊转牛）/'NONE'（无反转）
            'confidence': float,  # 反转信号置信度（0-1）
            'signals': {
                'trend_change': bool,  # 趋势变化
                'ma_cross': bool,  # 均线交叉
                'divergence': bool,  # 恐贪指数背离
                'volume_confirmation': bool,  # 成交量确认
            },
            'details': {
                'current_trend': str,  # 当前趋势
                'previous_trend': str,  # 之前趋势
                'ma_cross_type': str,  # 均线交叉类型
                'price_change_pct': float,  # 价格变化百分比
                'volume_ratio': float,  # 成交量比率
            }
        }
    """
    if get_history_func is None:
        if not HAS_XTQUANT:
            return {
                'has_reversal': False,
                'reversal_type': 'NONE',
                'confidence': 0.0,
                'error': 'xtquant未安装，无法获取数据'
            }
        get_history_func = get_stock_data_xtquant
    
    try:
        # 获取历史数据（需要足够长的数据来计算趋势变化）
        # 需要至少 lookback_days + 20 天的数据来计算指标
        required_days = lookback_days + 20
        df = await asyncio.to_thread(get_history_func, index_code, required_days)
        if df is None or df.empty or len(df) < required_days:
            return {
                'has_reversal': False,
                'reversal_type': 'NONE',
                'confidence': 0.0,
                'error': f'数据不足，需要至少{required_days}天数据'
            }
        
        # 计算牛熊指标
        indicator = BullBearIndicator(short_period=5, long_period=20, volume_period=5)
        df = indicator.calculate(df)
        
        # 获取当前和之前的数据
        current = df.iloc[-1]
        previous = df.iloc[-lookback_days] if len(df) > lookback_days else df.iloc[0]
        
        # 1. 检测趋势变化
        current_trend = current['bull_bear_signal']
        previous_trend = previous['bull_bear_signal']
        trend_change = (current_trend == 'BULL' and previous_trend == 'BEAR') or \
                      (current_trend == 'BEAR' and previous_trend == 'BULL')
        
        # 2. 检测均线交叉（金叉/死叉）
        # 当前：短期均线 vs 长期均线
        current_ma_cross = 'none'
        if current['ma_short'] > current['ma_long'] and previous['ma_short'] <= previous['ma_long']:
            current_ma_cross = 'golden_cross'  # 金叉：短期上穿长期
        elif current['ma_short'] < current['ma_long'] and previous['ma_short'] >= previous['ma_long']:
            current_ma_cross = 'death_cross'  # 死叉：短期下穿长期
        
        # 检查最近5天是否有交叉信号
        ma_cross_signal = False
        if len(df) >= 5:
            recent_5d = df.iloc[-5:]
            for i in range(1, len(recent_5d)):
                prev_row = recent_5d.iloc[i-1]
                curr_row = recent_5d.iloc[i]
                if prev_row['ma_short'] <= prev_row['ma_long'] and curr_row['ma_short'] > curr_row['ma_long']:
                    ma_cross_signal = True
                    current_ma_cross = 'golden_cross'
                    break
                elif prev_row['ma_short'] >= prev_row['ma_long'] and curr_row['ma_short'] < curr_row['ma_long']:
                    ma_cross_signal = True
                    current_ma_cross = 'death_cross'
                    break
        
        # 3. 检测价格和成交量的变化
        price_change_pct = (current['close'] - previous['close']) / previous['close'] * 100
        volume_ratio = current['volume'] / previous['volume'] if previous['volume'] > 0 else 1.0
        
        # 成交量确认：放量配合趋势变化
        volume_confirmation = False
        if trend_change:
            if (current_trend == 'BULL' and volume_ratio > 1.2) or \
               (current_trend == 'BEAR' and volume_ratio > 1.2):
                volume_confirmation = True
        
        # 4. 检测恐贪指数背离（需要外部传入，这里先标记）
        # 背离：价格创新低但恐贪指数不创新低（或相反）
        divergence = False
        # 注意：这里需要外部传入恐贪指数数据，暂时标记为False
        # 实际使用时，可以从 position_analyzer 获取恐贪指数历史数据
        
        # 5. 综合判断反转信号
        signals = {
            'trend_change': trend_change,
            'ma_cross': ma_cross_signal,
            'divergence': divergence,
            'volume_confirmation': volume_confirmation
        }
        
        # 计算置信度
        signal_count = sum([1 for v in signals.values() if v])
        confidence = min(signal_count / 4.0, 1.0)  # 最多4个信号，全部满足时置信度为1.0
        
        # 判断反转类型
        reversal_type = 'NONE'
        if trend_change or ma_cross_signal:
            if current_trend == 'BULL' and previous_trend == 'BEAR':
                reversal_type = 'BEAR_TO_BULL'  # 熊转牛
            elif current_trend == 'BEAR' and previous_trend == 'BULL':
                reversal_type = 'BULL_TO_BEAR'  # 牛转熊
            elif ma_cross_signal:
                if current_ma_cross == 'golden_cross':
                    reversal_type = 'BEAR_TO_BULL'
                elif current_ma_cross == 'death_cross':
                    reversal_type = 'BULL_TO_BEAR'
        
        has_reversal = reversal_type != 'NONE' and confidence >= 0.3
        
        return {
            'has_reversal': has_reversal,
            'reversal_type': reversal_type,
            'confidence': confidence,
            'signals': signals,
            'details': {
                'current_trend': current_trend,
                'previous_trend': previous_trend,
                'ma_cross_type': current_ma_cross,
                'price_change_pct': float(price_change_pct),
                'volume_ratio': float(volume_ratio),
                'current_score': float(current['bull_bear_score']),
                'previous_score': float(previous['bull_bear_score']),
                'current_close': float(current['close']),
                'previous_close': float(previous['close'])
            }
        }
        
    except Exception as e:
        logger.error(f"[反转检测] 检测失败: {e}", exc_info=True)
        return {
            'has_reversal': False,
            'reversal_type': 'NONE',
            'confidence': 0.0,
            'error': str(e)
        }


async def detect_market_reversal_with_fear_greed(
    index_code: str = '000001.SH',
    lookback_days: int = 20,
    fear_greed_history: Optional[List[Dict[str, Any]]] = None,
    get_history_func=None
) -> Dict[str, Any]:
    """
    检测市场反转信号（增强版：包含恐贪指数背离检测）
    
    在基础反转检测的基础上，增加恐贪指数背离检测：
    - 价格创新低，但恐贪指数不创新低 → 可能见底反转（熊转牛）
    - 价格创新高，但恐贪指数不创新高 → 可能见顶反转（牛转熊）
    
    Args:
        index_code: 指数代码，默认 '000001.SH'（上证指数）
        lookback_days: 回看天数，默认20天
        fear_greed_history: 恐贪指数历史数据列表，格式：
            [
                {'date': '20250101', 'index': 45.5, 'price': 3000.0},
                ...
            ]
        get_history_func: 获取历史数据的函数，如果为None则使用xtquant
    
    Returns:
        同 detect_market_reversal，但增加 'divergence_details' 字段
    """
    # 先执行基础反转检测
    base_result = await detect_market_reversal(
        index_code=index_code,
        lookback_days=lookback_days,
        get_history_func=get_history_func
    )
    
    if 'error' in base_result:
        return base_result
    
    # 如果有恐贪指数历史数据，检测背离
    if fear_greed_history and len(fear_greed_history) >= lookback_days:
        try:
            # 获取价格历史数据
            if get_history_func is None:
                if not HAS_XTQUANT:
                    return base_result
                get_history_func = get_stock_data_xtquant
            
            # 需要足够的数据来计算背离
            required_days = lookback_days + 10
            df = await asyncio.to_thread(get_history_func, index_code, required_days)
            if df is None or df.empty or len(df) < lookback_days:
                return base_result
            
            # 对齐价格和恐贪指数数据（按日期）
            recent_prices = df[['time', 'close']].tail(lookback_days).copy()
            recent_prices['date'] = pd.to_datetime(recent_prices['time']).dt.strftime('%Y%m%d')
            
            # 构建恐贪指数DataFrame
            fg_df = pd.DataFrame(fear_greed_history)
            if 'date' not in fg_df.columns:
                return base_result
            
            # 合并数据
            merged = recent_prices.merge(fg_df, on='date', how='inner')
            if len(merged) < 5:  # 至少需要5个数据点
                return base_result
            
            # 检测背离
            # 1. 价格创新低，但恐贪指数不创新低（可能见底）
            recent_prices_sorted = merged.sort_values('close')
            recent_fg_sorted = merged.sort_values('index')
            
            price_lowest = recent_prices_sorted.iloc[0]
            fg_lowest = recent_fg_sorted.iloc[0]
            
            # 如果价格最低点不是恐贪指数最低点，可能存在背离
            price_lowest_date = price_lowest['date']
            fg_lowest_date = fg_lowest['date']
            
            bear_to_bull_divergence = False
            if price_lowest_date != fg_lowest_date:
                # 价格创新低，但恐贪指数在更早的日期达到最低点
                price_lowest_matches = merged[merged['date'] == price_lowest_date]
                fg_lowest_matches = merged[merged['date'] == fg_lowest_date]
                
                if len(price_lowest_matches) > 0 and len(fg_lowest_matches) > 0:
                    price_lowest_idx = price_lowest_matches.index[0]
                    fg_lowest_idx = fg_lowest_matches.index[0]
                    
                    if price_lowest_idx > fg_lowest_idx:
                        # 价格在更晚的日期创新低，但恐贪指数已经提前见底
                        bear_to_bull_divergence = True
            
            # 2. 价格创新高，但恐贪指数不创新高（可能见顶）
            recent_prices_sorted_desc = merged.sort_values('close', ascending=False)
            recent_fg_sorted_desc = merged.sort_values('index', ascending=False)
            
            price_highest = recent_prices_sorted_desc.iloc[0]
            fg_highest = recent_fg_sorted_desc.iloc[0]
            
            price_highest_date = price_highest['date']
            fg_highest_date = fg_highest['date']
            
            bull_to_bear_divergence = False
            if price_highest_date != fg_highest_date:
                price_highest_matches = merged[merged['date'] == price_highest_date]
                fg_highest_matches = merged[merged['date'] == fg_highest_date]
                
                if len(price_highest_matches) > 0 and len(fg_highest_matches) > 0:
                    price_highest_idx = price_highest_matches.index[0]
                    fg_highest_idx = fg_highest_matches.index[0]
                    
                    if price_highest_idx > fg_highest_idx:
                        # 价格在更晚的日期创新高，但恐贪指数已经提前见顶
                        bull_to_bear_divergence = True
            
            # 更新背离信号
            base_result['signals']['divergence'] = bear_to_bull_divergence or bull_to_bear_divergence
            
            # 更新反转类型和置信度
            if bear_to_bull_divergence and base_result['reversal_type'] == 'NONE':
                base_result['reversal_type'] = 'BEAR_TO_BULL'
                base_result['confidence'] = min(base_result['confidence'] + 0.2, 1.0)
            elif bull_to_bear_divergence and base_result['reversal_type'] == 'NONE':
                base_result['reversal_type'] = 'BULL_TO_BEAR'
                base_result['confidence'] = min(base_result['confidence'] + 0.2, 1.0)
            
            # 添加背离详情
            base_result['divergence_details'] = {
                'bear_to_bull': bear_to_bull_divergence,
                'bull_to_bear': bull_to_bear_divergence,
                'price_lowest_date': price_lowest_date if bear_to_bull_divergence else None,
                'fg_lowest_date': fg_lowest_date if bear_to_bull_divergence else None,
                'price_highest_date': price_highest_date if bull_to_bear_divergence else None,
                'fg_highest_date': fg_highest_date if bull_to_bear_divergence else None
            }
            
            # 重新计算是否有反转
            signal_count = sum([1 for v in base_result['signals'].values() if v])
            base_result['confidence'] = min(signal_count / 4.0, 1.0)
            base_result['has_reversal'] = base_result['reversal_type'] != 'NONE' and base_result['confidence'] >= 0.3
            
        except Exception as e:
            logger.warning(f"[反转检测] 恐贪指数背离检测失败: {e}")
            # 如果背离检测失败，返回基础结果
    
    return base_result


async def main_async(symbol_or_market: str = 'market') -> Dict[str, Any]:
    """
    异步主函数：获取牛熊指标（纯函数，不打印）
    
    Args:
        symbol_or_market: 'market' 或股票代码（如 '000001.SZ'）
    
    Returns:
        牛熊指标数据字典（同 get_bull_bear_indicator 返回值）
    """
    # 直接返回指标数据，不进行任何打印
    return await get_bull_bear_indicator(symbol_or_market, days=60)


def main():
    """主函数：演示牛熊指标的使用（同步包装，带打印）"""
    import sys
    import json
    
    # 从命令行参数获取股票代码或市场
    if len(sys.argv) > 1:
        symbol_or_market = sys.argv[1]
    else:
        # 默认使用市场模式
        symbol_or_market = 'market'
    
    # 如果第二个参数是 'reversal'，则执行反转检测
    if len(sys.argv) > 2 and sys.argv[2] == 'reversal':
        # 执行反转检测
        result = asyncio.run(detect_market_reversal(
            index_code='000001.SH',
            lookback_days=20
        ))
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        # 运行异步主函数并打印结果
        result = asyncio.run(main_async(symbol_or_market))
        # 以JSON格式打印结果（便于调试和查看）
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()

