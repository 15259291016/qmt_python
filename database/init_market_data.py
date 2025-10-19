#!/usr/bin/env python3
"""
市场数据数据库初始化脚本
专门用于记录市场数据，为量化AI模型准备

作者: AI Assistant
创建时间: 2025-01-15
版本: 1.0
"""

import os
import sys
import argparse
import logging
import pymysql
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class MarketDataInitializer:
    """市场数据数据库初始化器"""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 3306,
                 user: str = 'root',
                 password: str = '',
                 database: str = 'market_data'):
        """
        初始化数据库连接器
        
        Args:
            host: 数据库主机
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
        # 设置日志
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('MarketDataInitializer')
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
    
    def connect(self) -> bool:
        """连接数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                autocommit=False
            )
            self.logger.info(f"成功连接到数据库 {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"连接数据库失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.logger.info("数据库连接已关闭")
    
    def create_database(self) -> bool:
        """创建数据库"""
        try:
            with self.connection.cursor() as cursor:
                # 创建数据库
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} "
                              f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                self.logger.info(f"数据库 {self.database} 创建成功")
                
                # 选择数据库
                cursor.execute(f"USE {self.database}")
                self.logger.info(f"已选择数据库 {self.database}")
                
                self.connection.commit()
                return True
        except Exception as e:
            self.logger.error(f"创建数据库失败: {e}")
            return False
    
    def execute_sql_file(self, sql_file: str) -> bool:
        """执行SQL文件"""
        try:
            sql_path = Path(sql_file)
            if not sql_path.exists():
                self.logger.error(f"SQL文件不存在: {sql_file}")
                return False
            
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            with self.connection.cursor() as cursor:
                for i, statement in enumerate(sql_statements):
                    if statement:
                        try:
                            cursor.execute(statement)
                            self.logger.debug(f"执行SQL语句 {i+1}/{len(sql_statements)}")
                        except Exception as e:
                            self.logger.warning(f"执行SQL语句失败: {e}")
                            self.logger.warning(f"语句内容: {statement[:100]}...")
                            continue
                
                self.connection.commit()
                self.logger.info(f"SQL文件 {sql_file} 执行完成")
                return True
        except Exception as e:
            self.logger.error(f"执行SQL文件失败: {e}")
            return False
    
    def verify_tables(self) -> Dict[str, Any]:
        """验证表结构"""
        try:
            with self.connection.cursor() as cursor:
                # 获取所有表
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                
                result = {
                    'total_tables': len(tables),
                    'tables': [],
                    'success': True
                }
                
                # 检查每个表的结构
                for table in tables:
                    cursor.execute(f"DESCRIBE {table}")
                    columns = cursor.fetchall()
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    
                    result['tables'].append({
                        'name': table,
                        'columns': len(columns),
                        'rows': row_count
                    })
                
                self.logger.info(f"验证完成: 共 {len(tables)} 个表")
                return result
        except Exception as e:
            self.logger.error(f"验证表结构失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_sample_data(self) -> bool:
        """创建示例数据"""
        try:
            with self.connection.cursor() as cursor:
                # 插入示例股票数据
                sample_stocks = [
                    ('000001.SZ', '000001', '平安银行', '深圳', '银行', '主板', '19910403'),
                    ('000002.SZ', '000002', '万科A', '深圳', '房地产', '主板', '19910129'),
                    ('000858.SZ', '000858', '五粮液', '四川', '食品饮料', '主板', '19980427'),
                    ('002415.SZ', '002415', '海康威视', '浙江', '电子', '中小板', '20100528'),
                    ('002594.SZ', '002594', '比亚迪', '广东', '汽车', '中小板', '20110630'),
                    ('300059.SZ', '300059', '东方财富', '上海', '互联网', '创业板', '20100319'),
                    ('300750.SZ', '300750', '宁德时代', '福建', '电气设备', '创业板', '20180611'),
                    ('600000.SH', '600000', '浦发银行', '上海', '银行', '主板', '19991110'),
                    ('600036.SH', '600036', '招商银行', '广东', '银行', '主板', '20020409'),
                    ('600519.SH', '600519', '贵州茅台', '贵州', '食品饮料', '主板', '20010827'),
                    ('600887.SH', '600887', '伊利股份', '内蒙古', '食品饮料', '主板', '19960312'),
                    ('601318.SH', '601318', '中国平安', '广东', '保险', '主板', '20070301'),
                    ('601398.SH', '601398', '工商银行', '北京', '银行', '主板', '20061027'),
                    ('601857.SH', '601857', '中国石油', '北京', '石油石化', '主板', '20071105')
                ]
                
                for stock in sample_stocks:
                    cursor.execute("""
                        INSERT IGNORE INTO stock_basic 
                        (ts_code, symbol, name, area, industry, market, list_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, stock)
                
                # 插入示例日线数据（最近30天）
                from datetime import datetime, timedelta
                import random
                
                base_date = datetime.now().date()
                for i in range(30):
                    trade_date = base_date - timedelta(days=i)
                    if trade_date.weekday() < 5:  # 只插入工作日
                        for stock in sample_stocks[:5]:  # 只插入前5只股票
                            symbol = stock[0]
                            base_price = 10 + random.random() * 100
                            open_price = base_price * (1 + random.uniform(-0.05, 0.05))
                            close_price = base_price * (1 + random.uniform(-0.05, 0.05))
                            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.03))
                            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.03))
                            volume = random.randint(1000000, 10000000)
                            amount = volume * close_price
                            pct_chg = (close_price - base_price) / base_price * 100
                            
                            cursor.execute("""
                                INSERT IGNORE INTO daily_data
                                (symbol, trade_date, open, high, low, close, volume, amount, pct_chg)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (symbol, trade_date, open_price, high_price, low_price, close_price, volume, amount, pct_chg))
                
                self.connection.commit()
                self.logger.info("示例数据创建完成")
                return True
        except Exception as e:
            self.logger.error(f"创建示例数据失败: {e}")
            return False
    
    def test_connections(self) -> Dict[str, bool]:
        """测试数据库用户连接"""
        users = {
            'market_data_readonly': 'readonly_password',
            'market_data_app': 'app_password',
            'market_data_admin': 'admin_password'
        }
        
        results = {}
        
        for username, password in users.items():
            try:
                test_conn = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=username,
                    password=password,
                    database=self.database,
                    charset='utf8mb4'
                )
                test_conn.close()
                results[username] = True
                self.logger.info(f"用户 {username} 连接测试成功")
            except Exception as e:
                results[username] = False
                self.logger.error(f"用户 {username} 连接测试失败: {e}")
        
        return results
    
    def initialize(self, create_sample_data: bool = True) -> bool:
        """完整初始化数据库"""
        try:
            self.logger.info("开始初始化市场数据数据库...")
            
            # 1. 连接数据库
            if not self.connect():
                return False
            
            # 2. 创建数据库
            if not self.create_database():
                return False
            
            # 3. 执行SQL文件
            sql_file = Path(__file__).parent / 'market_data_schema.sql'
            if not self.execute_sql_file(str(sql_file)):
                return False
            
            # 4. 验证表结构
            verification = self.verify_tables()
            if not verification['success']:
                return False
            
            # 5. 创建示例数据
            if create_sample_data:
                if not self.create_sample_data():
                    self.logger.warning("创建示例数据失败，但继续初始化")
            
            # 6. 测试用户连接
            connection_tests = self.test_connections()
            success_count = sum(connection_tests.values())
            self.logger.info(f"用户连接测试: {success_count}/{len(connection_tests)} 成功")
            
            self.logger.info("数据库初始化完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            return False
        finally:
            self.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='市场数据数据库初始化工具')
    parser.add_argument('--host', default='localhost', help='数据库主机')
    parser.add_argument('--port', type=int, default=3306, help='数据库端口')
    parser.add_argument('--user', default='root', help='数据库用户名')
    parser.add_argument('--password', default='', help='数据库密码')
    parser.add_argument('--database', default='market_data', help='数据库名称')
    parser.add_argument('--no-sample-data', action='store_true', help='不创建示例数据')
    parser.add_argument('--test-only', action='store_true', help='仅测试连接')
    
    args = parser.parse_args()
    
    # 创建初始化器
    initializer = MarketDataInitializer(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    if args.test_only:
        # 仅测试连接
        if initializer.connect():
            print("数据库连接测试成功！")
            initializer.close()
        else:
            print("数据库连接测试失败！")
            sys.exit(1)
    else:
        # 完整初始化
        success = initializer.initialize(create_sample_data=not args.no_sample_data)
        if success:
            print("数据库初始化成功！")
        else:
            print("数据库初始化失败！")
            sys.exit(1)


if __name__ == '__main__':
    main()

