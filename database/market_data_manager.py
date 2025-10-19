#!/usr/bin/env python3
"""
市场数据管理器
专门用于记录市场数据，为量化AI模型准备

作者: AI Assistant
创建时间: 2025-01-15
版本: 1.0
"""

import os
import sys
import logging
import pymysql
import pandas as pd
from typing import Dict, Any, List, Optional, Union, Tuple
from contextlib import contextmanager
from datetime import datetime, date
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class MarketDataManager:
    """市场数据管理器 - 专注于数据存储"""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 3306,
                 user: str = 'market_data_app',
                 password: str = 'app_password',
                 database: str = 'market_data',
                 charset: str = 'utf8mb4',
                 autocommit: bool = False):
        """
        初始化市场数据管理器
        
        Args:
            host: 数据库主机
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
            charset: 字符集
            autocommit: 是否自动提交
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.autocommit = autocommit
        
        # 设置日志
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('MarketDataManager')
        logger.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        return logger
    
    def get_connection(self) -> pymysql.Connection:
        """获取数据库连接"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                autocommit=self.autocommit,
                cursorclass=pymysql.cursors.DictCursor
            )
            self.logger.debug(f"创建数据库连接: {self.host}:{self.port}/{self.database}")
            return connection
        except Exception as e:
            self.logger.error(f"创建数据库连接失败: {e}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            yield cursor
        except Exception as e:
            if connection:
                connection.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行查询SQL"""
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    def execute_update(self, sql: str, params: Optional[Tuple] = None) -> int:
        """执行更新SQL"""
        with self.get_cursor() as cursor:
            result = cursor.execute(sql, params)
            cursor.connection.commit()
            return result
    
    def execute_batch(self, sql: str, params_list: List[Tuple]) -> int:
        """批量执行SQL"""
        with self.get_cursor() as cursor:
            result = cursor.executemany(sql, params_list)
            cursor.connection.commit()
            return result
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, 
                        if_exists: str = 'append', index: bool = False) -> int:
        """将DataFrame插入数据库"""
        try:
            with self.get_cursor() as cursor:
                connection = cursor.connection
                df.to_sql(table_name, connection, if_exists=if_exists, index=index, method='multi')
                return len(df)
        except Exception as e:
            self.logger.error(f"插入DataFrame失败: {e}")
            raise
    
    def query_dataframe(self, sql: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """查询数据并返回DataFrame"""
        try:
            with self.get_cursor() as cursor:
                df = pd.read_sql(sql, cursor.connection, params=params)
                return df
        except Exception as e:
            self.logger.error(f"查询DataFrame失败: {e}")
            raise
    
    # ========================================
    # 股票基础信息相关方法
    # ========================================
    
    def get_stock_list(self, market: Optional[str] = None) -> List[Dict]:
        """获取股票列表"""
        sql = "SELECT * FROM stock_basic"
        params = None
        
        if market:
            sql += " WHERE market = %s"
            params = (market,)
        
        return self.execute_query(sql, params)
    
    def insert_stock_basic(self, df: pd.DataFrame) -> int:
        """插入股票基础信息"""
        return self.insert_dataframe(df, 'stock_basic', if_exists='append')
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """获取股票信息"""
        sql = "SELECT * FROM stock_basic WHERE symbol = %s"
        result = self.execute_query(sql, (symbol,))
        return result[0] if result else None
    
    # ========================================
    # 市场数据相关方法
    # ========================================
    
    def insert_tick_data(self, df: pd.DataFrame) -> int:
        """插入tick数据"""
        return self.insert_dataframe(df, 'tick_data', if_exists='append')
    
    def insert_minute_data(self, df: pd.DataFrame) -> int:
        """插入分钟数据"""
        return self.insert_dataframe(df, 'minute_data', if_exists='append')
    
    def insert_daily_data(self, df: pd.DataFrame) -> int:
        """插入日线数据"""
        return self.insert_dataframe(df, 'daily_data', if_exists='append')
    
    def insert_adj_factor(self, df: pd.DataFrame) -> int:
        """插入复权因子"""
        return self.insert_dataframe(df, 'adj_factor', if_exists='append')
    
    def get_tick_data(self, symbol: str, start_time: str, end_time: str) -> pd.DataFrame:
        """获取tick数据"""
        sql = """
        SELECT * FROM tick_data 
        WHERE symbol = %s AND tick_time BETWEEN %s AND %s
        ORDER BY tick_time
        """
        return self.query_dataframe(sql, (symbol, start_time, end_time))
    
    def get_minute_data(self, symbol: str, start_time: str, end_time: str) -> pd.DataFrame:
        """获取分钟数据"""
        sql = """
        SELECT * FROM minute_data 
        WHERE symbol = %s AND datetime BETWEEN %s AND %s
        ORDER BY datetime
        """
        return self.query_dataframe(sql, (symbol, start_time, end_time))
    
    def get_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据"""
        sql = """
        SELECT * FROM daily_data 
        WHERE symbol = %s AND trade_date BETWEEN %s AND %s
        ORDER BY trade_date
        """
        return self.query_dataframe(sql, (symbol, start_date, end_date))
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """获取最新价格"""
        sql = """
        SELECT close FROM daily_data 
        WHERE symbol = %s 
        ORDER BY trade_date DESC 
        LIMIT 1
        """
        result = self.execute_query(sql, (symbol,))
        return result[0]['close'] if result else None
    
    def get_latest_tick_data(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """获取最新tick数据"""
        sql = """
        SELECT * FROM tick_data 
        WHERE symbol = %s 
        ORDER BY tick_time DESC 
        LIMIT %s
        """
        return self.query_dataframe(sql, (symbol, limit))
    
    # ========================================
    # 技术指标相关方法
    # ========================================
    
    def insert_technical_indicators(self, df: pd.DataFrame) -> int:
        """插入技术指标"""
        return self.insert_dataframe(df, 'technical_indicators', if_exists='append')
    
    def get_technical_indicators(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取技术指标"""
        sql = """
        SELECT * FROM technical_indicators 
        WHERE symbol = %s AND trade_date BETWEEN %s AND %s
        ORDER BY trade_date
        """
        return self.query_dataframe(sql, (symbol, start_date, end_date))
    
    def calculate_technical_indicators(self, symbol: str, days: int = 60) -> int:
        """计算技术指标"""
        sql = "CALL CalculateTechnicalIndicators(%s, %s)"
        return self.execute_update(sql, (symbol, days))
    
    # ========================================
    # 数据同步相关方法
    # ========================================
    
    def update_sync_status(self, data_type: str, symbol: str, status: str, 
                          record_count: int = 0, error_message: str = '') -> int:
        """更新同步状态"""
        sql = """
        INSERT INTO data_sync_status (data_type, symbol, last_sync_time, sync_status, record_count, error_message)
        VALUES (%s, %s, NOW(), %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        last_sync_time = NOW(),
        sync_status = VALUES(sync_status),
        record_count = VALUES(record_count),
        error_message = VALUES(error_message),
        updated_at = NOW()
        """
        return self.execute_update(sql, (data_type, symbol, status, record_count, error_message))
    
    def get_sync_status(self, data_type: Optional[str] = None) -> pd.DataFrame:
        """获取同步状态"""
        sql = "SELECT * FROM data_sync_status"
        params = None
        
        if data_type:
            sql += " WHERE data_type = %s"
            params = (data_type,)
        
        sql += " ORDER BY last_sync_time DESC"
        return self.query_dataframe(sql, params)
    
    # ========================================
    # 数据统计相关方法
    # ========================================
    
    def get_data_statistics(self) -> Dict:
        """获取数据统计信息"""
        sql = "SELECT * FROM v_data_statistics"
        result = self.execute_query(sql)
        
        stats = {}
        for row in result:
            stats[row['data_type']] = {
                'total_records': row['total_records'],
                'unique_symbols': row['unique_symbols'],
                'earliest_time': row['earliest_time'],
                'latest_time': row['latest_time']
            }
        
        return stats
    
    def get_stock_summary(self) -> pd.DataFrame:
        """获取股票汇总信息"""
        sql = "SELECT * FROM v_stock_summary ORDER BY latest_date DESC"
        return self.query_dataframe(sql)
    
    def get_data_coverage(self, symbol: str) -> Dict:
        """获取数据覆盖情况"""
        coverage = {}
        
        # tick数据覆盖
        sql = """
        SELECT 
            COUNT(*) as count,
            MIN(tick_time) as start_time,
            MAX(tick_time) as end_time
        FROM tick_data WHERE symbol = %s
        """
        result = self.execute_query(sql, (symbol,))
        coverage['tick_data'] = result[0] if result else {}
        
        # 分钟数据覆盖
        sql = """
        SELECT 
            COUNT(*) as count,
            MIN(datetime) as start_time,
            MAX(datetime) as end_time
        FROM minute_data WHERE symbol = %s
        """
        result = self.execute_query(sql, (symbol,))
        coverage['minute_data'] = result[0] if result else {}
        
        # 日线数据覆盖
        sql = """
        SELECT 
            COUNT(*) as count,
            MIN(trade_date) as start_time,
            MAX(trade_date) as end_time
        FROM daily_data WHERE symbol = %s
        """
        result = self.execute_query(sql, (symbol,))
        coverage['daily_data'] = result[0] if result else {}
        
        return coverage
    
    # ========================================
    # 数据清理相关方法
    # ========================================
    
    def clean_historical_data(self, days_to_keep: int = 30) -> int:
        """清理历史数据"""
        sql = "CALL CleanHistoricalData(%s)"
        result = self.execute_query(sql, (days_to_keep,))
        return result[0]['deleted_rows'] if result else 0
    
    # ========================================
    # 系统配置相关方法
    # ========================================
    
    def get_system_config(self, config_key: str) -> Optional[str]:
        """获取系统配置"""
        sql = "SELECT config_value FROM system_config WHERE config_key = %s AND is_active = 1"
        result = self.execute_query(sql, (config_key,))
        return result[0]['config_value'] if result else None
    
    def set_system_config(self, config_key: str, config_value: str, 
                         config_type: str = 'string', description: str = '') -> int:
        """设置系统配置"""
        sql = """
        INSERT INTO system_config (config_key, config_value, config_type, description)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        config_value = VALUES(config_value),
        config_type = VALUES(config_type),
        description = VALUES(description),
        updated_at = NOW()
        """
        return self.execute_update(sql, (config_key, config_value, config_type, description))
    
    # ========================================
    # 工具方法
    # ========================================
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Dict:
        """获取表信息"""
        sql = """
        SELECT 
            TABLE_NAME,
            TABLE_ROWS,
            ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as size_mb,
            CREATE_TIME,
            UPDATE_TIME
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        result = self.execute_query(sql, (self.database, table_name))
        return result[0] if result else {}
    
    def export_data_to_csv(self, symbol: str, data_type: str, start_date: str, end_date: str, 
                          output_dir: str = 'data/export') -> str:
        """导出数据到CSV文件"""
        try:
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 根据数据类型获取数据
            if data_type == 'tick':
                df = self.get_tick_data(symbol, f"{start_date} 00:00:00", f"{end_date} 23:59:59")
                filename = f"{symbol}_{data_type}_{start_date}_{end_date}.csv"
            elif data_type == 'minute':
                df = self.get_minute_data(symbol, f"{start_date} 00:00:00", f"{end_date} 23:59:59")
                filename = f"{symbol}_{data_type}_{start_date}_{end_date}.csv"
            elif data_type == 'daily':
                df = self.get_daily_data(symbol, start_date, end_date)
                filename = f"{symbol}_{data_type}_{start_date}_{end_date}.csv"
            else:
                raise ValueError(f"不支持的数据类型: {data_type}")
            
            # 保存到CSV
            filepath = output_path / filename
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"数据导出成功: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"数据导出失败: {e}")
            raise


# 创建默认市场数据管理器实例
def get_default_market_data_manager() -> MarketDataManager:
    """获取默认市场数据管理器实例"""
    return MarketDataManager()


# 使用示例
if __name__ == '__main__':
    # 创建市场数据管理器
    manager = MarketDataManager()
    
    # 测试连接
    if manager.test_connection():
        print("✅ 数据库连接成功！")
        
        # 获取数据统计信息
        stats = manager.get_data_statistics()
        print(f"📊 数据统计: {stats}")
        
        # 获取股票汇总信息
        summary = manager.get_stock_summary()
        print(f"📈 股票数量: {len(summary)}")
        
        # 获取表信息
        table_info = manager.get_table_info('daily_data')
        print(f"📋 日线数据表信息: {table_info}")
    else:
        print("❌ 数据库连接失败！")

