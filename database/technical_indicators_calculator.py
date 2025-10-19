#!/usr/bin/env python3
"""
技术指标计算器
基于日线数据计算各种技术指标并存储到数据库

作者: AI Assistant
创建时间: 2025-01-15
版本: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, date
import logging

class TechnicalIndicatorsCalculator:
    """技术指标计算器"""
    
    def __init__(self, market_data_manager):
        """
        初始化技术指标计算器
        
        Args:
            market_data_manager: 市场数据管理器实例
        """
        self.manager = market_data_manager
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('TechnicalIndicatorsCalculator')
        logger.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        return logger
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算移动平均线"""
        df = df.copy()
        
        # 移动平均线
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma60'] = df['close'].rolling(60).mean()
        df['ma120'] = df['close'].rolling(120).mean()
        df['ma250'] = df['close'].rolling(250).mean()
        
        return df
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        df = df.copy()
        
        # 计算EMA
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        
        # MACD线
        df['macd_dif'] = ema12 - ema26
        
        # 信号线
        df['macd_dea'] = df['macd_dif'].ewm(span=9).mean()
        
        # 柱状图
        df['macd_histogram'] = df['macd_dif'] - df['macd_dea']
        
        return df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """计算布林带"""
        df = df.copy()
        
        # 中轨（移动平均线）
        df['boll_middle'] = df['close'].rolling(period).mean()
        
        # 标准差
        std = df['close'].rolling(period).std()
        
        # 上轨和下轨
        df['boll_upper'] = df['boll_middle'] + (std * std_dev)
        df['boll_lower'] = df['boll_middle'] - (std * std_dev)
        
        return df
    
    def calculate_kdj(self, df: pd.DataFrame, k_period: int = 9, d_period: int = 3, j_period: int = 3) -> pd.DataFrame:
        """计算KDJ指标"""
        df = df.copy()
        
        # 计算RSV
        low_min = df['low'].rolling(k_period).min()
        high_max = df['high'].rolling(k_period).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        
        # 计算K值
        df['kdj_k'] = rsv.ewm(alpha=1/d_period).mean()
        
        # 计算D值
        df['kdj_d'] = df['kdj_k'].ewm(alpha=1/j_period).mean()
        
        # 计算J值
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        return df
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算ATR指标"""
        df = df.copy()
        
        # 计算真实波幅
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr'] = true_range.rolling(period).mean()
        
        return df
    
    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """计算CCI指标"""
        df = df.copy()
        
        # 典型价格
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # 移动平均
        sma = typical_price.rolling(period).mean()
        
        # 平均偏差
        mean_deviation = typical_price.rolling(period).apply(
            lambda x: np.mean(np.abs(x - x.mean()))
        )
        
        # CCI
        df['cci'] = (typical_price - sma) / (0.015 * mean_deviation)
        
        return df
    
    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算威廉指标"""
        df = df.copy()
        
        # 计算最高价和最低价
        highest_high = df['high'].rolling(period).max()
        lowest_low = df['low'].rolling(period).min()
        
        # 威廉指标
        df['williams_r'] = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        
        return df
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标"""
        df = df.copy()
        
        # 确保数据按日期排序
        df = df.sort_values('trade_date')
        
        # 计算各种指标
        df = self.calculate_moving_averages(df)
        df = self.calculate_macd(df)
        df = self.calculate_bollinger_bands(df)
        df = self.calculate_kdj(df)
        df = self.calculate_atr(df)
        df = self.calculate_cci(df)
        df = self.calculate_williams_r(df)
        
        # 计算RSI
        df['rsi6'] = self.calculate_rsi(df['close'], 6)
        df['rsi12'] = self.calculate_rsi(df['close'], 12)
        df['rsi24'] = self.calculate_rsi(df['close'], 24)
        
        return df
    
    def calculate_and_store_indicators(self, symbol: str, start_date: str, end_date: str) -> int:
        """计算并存储技术指标"""
        try:
            # 获取日线数据
            daily_data = self.manager.get_daily_data(symbol, start_date, end_date)
            
            if daily_data.empty:
                self.logger.warning(f"没有找到 {symbol} 的日线数据")
                return 0
            
            # 计算技术指标
            indicators_data = self.calculate_all_indicators(daily_data)
            
            # 选择需要的列
            indicator_columns = [
                'symbol', 'trade_date', 'ma5', 'ma10', 'ma20', 'ma60', 'ma120', 'ma250',
                'macd_dif', 'macd_dea', 'macd_histogram',
                'rsi6', 'rsi12', 'rsi24',
                'kdj_k', 'kdj_d', 'kdj_j',
                'boll_upper', 'boll_middle', 'boll_lower',
                'atr', 'cci', 'williams_r'
            ]
            
            # 过滤数据
            indicators_df = indicators_data[indicator_columns].copy()
            
            # 删除包含NaN的行（因为需要足够的历史数据计算指标）
            indicators_df = indicators_df.dropna()
            
            if indicators_df.empty:
                self.logger.warning(f"{symbol} 没有足够的数据计算技术指标")
                return 0
            
            # 存储到数据库
            result = self.manager.insert_technical_indicators(indicators_df)
            
            self.logger.info(f"成功计算并存储 {symbol} 的技术指标: {len(indicators_df)} 条记录")
            return len(indicators_df)
            
        except Exception as e:
            self.logger.error(f"计算 {symbol} 技术指标失败: {e}")
            return 0
    
    def batch_calculate_indicators(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, int]:
        """批量计算技术指标"""
        results = {}
        
        for symbol in symbols:
            try:
                count = self.calculate_and_store_indicators(symbol, start_date, end_date)
                results[symbol] = count
                
                # 更新同步状态
                self.manager.update_sync_status(
                    'technical_indicators', 
                    symbol, 
                    'SUCCESS' if count > 0 else 'FAILED',
                    count
                )
                
            except Exception as e:
                self.logger.error(f"批量计算 {symbol} 技术指标失败: {e}")
                results[symbol] = 0
                
                # 更新同步状态
                self.manager.update_sync_status(
                    'technical_indicators', 
                    symbol, 
                    'FAILED',
                    0,
                    str(e)
                )
        
        return results
    
    def update_latest_indicators(self, symbol: str) -> int:
        """更新最新日期的技术指标"""
        try:
            # 获取最新的技术指标日期
            latest_indicators = self.manager.execute_query(
                "SELECT MAX(trade_date) as latest_date FROM technical_indicators WHERE symbol = %s",
                (symbol,)
            )
            
            if not latest_indicators or not latest_indicators[0]['latest_date']:
                # 如果没有历史数据，计算最近一年的指标
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            else:
                # 从最新日期开始计算
                latest_date = latest_indicators[0]['latest_date']
                start_date = latest_date.strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            return self.calculate_and_store_indicators(symbol, start_date, end_date)
            
        except Exception as e:
            self.logger.error(f"更新 {symbol} 最新技术指标失败: {e}")
            return 0


# 使用示例
if __name__ == '__main__':
    from database.market_data_manager import MarketDataManager
    
    # 创建数据管理器
    manager = MarketDataManager()
    
    # 创建技术指标计算器
    calculator = TechnicalIndicatorsCalculator(manager)
    
    # 计算单只股票的技术指标
    symbol = '000001.SZ'
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    count = calculator.calculate_and_store_indicators(symbol, start_date, end_date)
    print(f"成功计算并存储 {symbol} 的技术指标: {count} 条记录")
    
    # 批量计算多只股票的技术指标
    symbols = ['000001.SZ', '000002.SZ', '600519.SH']
    results = calculator.batch_calculate_indicators(symbols, start_date, end_date)
    
    print("批量计算结果:")
    for symbol, count in results.items():
        print(f"  {symbol}: {count} 条记录")

