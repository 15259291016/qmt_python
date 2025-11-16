# coding=utf-8
"""
数据源适配器
将不同数据源的数据转换为 Backtrader 格式
"""

import backtrader as bt
import pandas as pd
import numpy as np
import tushare as ts
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TushareDataFeed(bt.feeds.PandasData):
    """Tushare 数据源适配器"""
    @classmethod
    def from_tushare(cls, symbol, start_date, end_date, tushare_token, **kwargs):
        df = cls._fetch_data_static(symbol, start_date, end_date, tushare_token)
        bt_df = cls._convert_to_backtrader_format_static(df)
        return cls(dataname=bt_df, **kwargs)

    @staticmethod
    def _fetch_data_static(symbol, start_date, end_date, tushare_token):
        import tushare as ts
        pro = ts.pro_api(tushare_token)
        df = pro.daily(
            ts_code=symbol,
            start_date=start_date,
            end_date=end_date
        )
        if df.empty:
            raise ValueError(f"未获取到 {symbol} 的数据")
        df = df.sort_values('trade_date').reset_index(drop=True)
        return df

    @staticmethod
    def _convert_to_backtrader_format_static(df):
        import pandas as pd
        column_mapping = {
            'trade_date': 'datetime',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'vol': 'volume'
        }
        bt_df = df.rename(columns=column_mapping)
        bt_df['datetime'] = pd.to_datetime(bt_df['datetime'])
        bt_df.set_index('datetime', inplace=True)
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in bt_df.columns:
                bt_df[col] = pd.to_numeric(bt_df[col], errors='coerce')
        bt_df = bt_df.dropna()
        return bt_df


class XtQuantDataFeed(bt.feeds.PandasData):
    """XtQuant 数据源适配器"""
    
    def __init__(self, symbol: str, start_date: str, end_date: str,
                 qmt_path: str, account: str, **kwargs):
        """
        初始化 XtQuant 数据源
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            qmt_path: QMT 安装路径
            account: 账户信息
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.qmt_path = qmt_path
        self.account = account
        
        # 获取数据
        df = self._fetch_data()
        
        # 转换为 Backtrader 格式
        bt_df = self._convert_to_backtrader_format(df)
        
        super().__init__(dataname=bt_df, **kwargs)
    
    def _fetch_data(self) -> pd.DataFrame:
        """获取 XtQuant 数据"""
        try:
            from xtquant import xtdata
            
            # 初始化 XtQuant
            xtdata.download_sector_data()
            
            # 获取历史数据
            df = xtdata.get_history_data(
                stock_list=[self.symbol],
                period='1d',
                start_time=self.start_date,
                end_time=self.end_date,
                count=-1,
                dividend_type='none'
            )
            
            if df is None or df.empty:
                raise ValueError(f"未获取到 {self.symbol} 的数据")
            
            logger.info(f"成功获取 {self.symbol} XtQuant 数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取 {self.symbol} XtQuant 数据失败: {e}")
            raise
    
    def _convert_to_backtrader_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换为 Backtrader 格式"""
        # XtQuant 数据格式转换
        if isinstance(df, dict):
            # 如果是字典格式，取第一个股票的数据
            symbol_data = list(df.values())[0]
            bt_df = pd.DataFrame(symbol_data)
        else:
            bt_df = df.copy()
        
        # 重命名列
        column_mapping = {
            'time': 'datetime',
            'open': 'open',
            'high': 'high',
            'low': 'low', 
            'close': 'close',
            'volume': 'volume'
        }
        
        bt_df = bt_df.rename(columns=column_mapping)
        
        # 转换日期格式
        bt_df['datetime'] = pd.to_datetime(bt_df['datetime'], unit='ms')
        bt_df.set_index('datetime', inplace=True)
        
        # 确保数据类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in bt_df.columns:
                bt_df[col] = pd.to_numeric(bt_df[col], errors='coerce')
        
        # 删除无效数据
        bt_df = bt_df.dropna()
        
        return bt_df


class MultiSymbolDataFeed:
    """多股票数据源管理器"""
    
    def __init__(self, data_source: str = 'tushare', **kwargs):
        """
        初始化多股票数据源管理器
        
        Args:
            data_source: 数据源类型 ('tushare' 或 'xtquant')
            **kwargs: 其他参数
        """
        self.data_source = data_source
        self.kwargs = kwargs
        self.data_feeds = {}
    
    def add_symbol(self, symbol: str, start_date: str, end_date: str) -> bt.feeds.PandasData:
        """添加股票数据源"""
        if self.data_source == 'tushare':
            feed = TushareDataFeed.from_tushare(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                **self.kwargs
            )
        elif self.data_source == 'xtquant':
            feed = XtQuantDataFeed(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                **self.kwargs
            )
        else:
            raise ValueError(f"不支持的数据源: {self.data_source}")
        
        self.data_feeds[symbol] = feed
        return feed
    
    def get_all_feeds(self) -> List[bt.feeds.PandasData]:
        """获取所有数据源"""
        return list(self.data_feeds.values())
    
    def get_feed(self, symbol: str) -> Optional[bt.feeds.PandasData]:
        """获取指定股票的数据源"""
        return self.data_feeds.get(symbol)


class CSVDataFeed(bt.feeds.PandasData):
    """CSV 数据源适配器"""
    
    def __init__(self, csv_file: str, **kwargs):
        """
        初始化 CSV 数据源
        
        Args:
            csv_file: CSV 文件路径
        """
        try:
            df = pd.read_csv(csv_file)
            
            # 转换日期格式
            if 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'])
                df.set_index('datetime', inplace=True)
            elif 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
            
            # 确保列名正确
            column_mapping = {
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            
            for bt_col, csv_col in column_mapping.items():
                if csv_col in df.columns and bt_col not in df.columns:
                    df[bt_col] = df[csv_col]
            
            # 确保数据类型正确
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 删除无效数据
            df = df.dropna()
            
            super().__init__(dataname=df, **kwargs)
            
        except Exception as e:
            logger.error(f"CSV数据源初始化失败: {e}")
            raise 