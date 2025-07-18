#!/usr/bin/env python3
"""
MySQL数据库初始化脚本
用于创建量化交易平台所需的所有表结构和初始数据
"""

import pymysql
import os
import sys
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库配置
from config.database_config import DB_CONFIG, get_db_config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    try:
        # 连接MySQL服务器（不指定数据库）
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 创建数据库
            create_db_query = f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET {DB_CONFIG['charset']} COLLATE {DB_CONFIG['collation']}"
            cursor.execute(create_db_query)
            logger.info(f"数据库 {DB_CONFIG['database']} 创建成功或已存在")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        logger.error(f"创建数据库时出错: {e}")
        raise

class DatabaseInitializer:
    def __init__(self, host='localhost', port=3306, user='root', password='6116988.niu'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = 'stock_data'
        self.connection = None
        
    def connect(self):
        """连接到MySQL服务器"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            print(f"✅ 成功连接到MySQL服务器 {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ 连接MySQL服务器失败: {e}")
            return False
    
    def create_database(self):
        """创建数据库"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ 数据库 {self.database} 创建成功")
                
                # 切换到目标数据库
                cursor.execute(f"USE {self.database}")
                print(f"✅ 切换到数据库 {self.database}")
                return True
        except Exception as e:
            print(f"❌ 创建数据库失败: {e}")
            return False
    
    def execute_sql_file(self, sql_file_path):
        """执行SQL文件"""
        try:
            if not os.path.exists(sql_file_path):
                print(f"❌ SQL文件不存在: {sql_file_path}")
                return False
            
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句
            sql_statements = []
            current_statement = ""
            delimiter = ";"
            
            for line in sql_content.split('\n'):
                line = line.strip()
                
                # 跳过注释和空行
                if line.startswith('--') or line.startswith('#') or not line:
                    continue
                
                # 检查是否包含DELIMITER语句
                if line.upper().startswith('DELIMITER'):
                    delimiter = line.split()[1]
                    continue
                
                current_statement += line + " "
                
                if line.endswith(delimiter):
                    sql_statements.append(current_statement.strip())
                    current_statement = ""
            
            # 执行SQL语句
            with self.connection.cursor() as cursor:
                for i, statement in enumerate(sql_statements, 1):
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                            print(f"✅ 执行SQL语句 {i}/{len(sql_statements)}: {statement[:50]}...")
                        except Exception as e:
                            print(f"⚠️  SQL语句执行失败 {i}: {e}")
                            print(f"   语句: {statement[:100]}...")
                            # 继续执行其他语句
                
                self.connection.commit()
                print(f"✅ 所有SQL语句执行完成")
                return True
                
        except Exception as e:
            print(f"❌ 执行SQL文件失败: {e}")
            return False
    
    def verify_tables(self):
        """验证表是否创建成功"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]
                
                expected_tables = [
                    'stock_basic', 'daily_data', 'adj_factor', 'minute_data',
                    'fina_indicator', 'daily_basic', 'orders', 'risk_config',
                    'stock_blacklist', 'risk_logs', 'compliance_rules',
                    'compliance_logs', 'audit_logs', 'strategy_config',
                    'strategy_signals', 'backtest_results', 'backtest_trades',
                    'statistics', 'ml_results', 'system_config'
                ]
                
                print("\n📊 表创建验证结果:")
                print("=" * 50)
                
                for table in expected_tables:
                    if table in tables:
                        print(f"✅ {table}")
                    else:
                        print(f"❌ {table} (缺失)")
                
                missing_tables = set(expected_tables) - set(tables)
                if missing_tables:
                    print(f"\n⚠️  缺失的表: {', '.join(missing_tables)}")
                else:
                    print(f"\n🎉 所有表创建成功!")
                
                return len(missing_tables) == 0
                
        except Exception as e:
            print(f"❌ 验证表失败: {e}")
            return False
    
    def check_initial_data(self):
        """检查初始数据"""
        try:
            with self.connection.cursor() as cursor:
                print("\n📋 初始数据检查:")
                print("=" * 50)
                
                # 检查系统配置
                cursor.execute("SELECT COUNT(*) FROM system_config")
                config_count = cursor.fetchone()[0]
                print(f"✅ 系统配置: {config_count} 条记录")
                
                # 检查风控配置
                cursor.execute("SELECT COUNT(*) FROM risk_config")
                risk_count = cursor.fetchone()[0]
                print(f"✅ 风控配置: {risk_count} 条记录")
                
                # 检查合规规则
                cursor.execute("SELECT COUNT(*) FROM compliance_rules")
                compliance_count = cursor.fetchone()[0]
                print(f"✅ 合规规则: {compliance_count} 条记录")
                
                # 检查策略配置
                cursor.execute("SELECT COUNT(*) FROM strategy_config")
                strategy_count = cursor.fetchone()[0]
                print(f"✅ 策略配置: {strategy_count} 条记录")
                
                return True
                
        except Exception as e:
            print(f"❌ 检查初始数据失败: {e}")
            return False
    
    def create_sample_data(self):
        """创建示例数据"""
        try:
            with self.connection.cursor() as cursor:
                print("\n📝 创建示例数据:")
                print("=" * 50)
                
                # 插入示例股票数据
                sample_stocks = [
                    ('000001.SZ', '000001', '平安银行', '深圳', '银行', 'payh', '主板', '1991-04-03'),
                    ('000002.SZ', '000002', '万科A', '深圳', '全国地产', 'wka', '主板', '1991-01-29'),
                    ('600519.SH', '600519', '贵州茅台', '贵州', '白酒', 'gzmt', '主板', '2001-08-27'),
                    ('000858.SZ', '000858', '五粮液', '四川', '白酒', 'wly', '主板', '1998-04-27'),
                    ('002415.SZ', '002415', '海康威视', '浙江', '安防设备', 'hkws', '中小板', '2010-05-28')
                ]
                
                for stock in sample_stocks:
                    cursor.execute("""
                        INSERT IGNORE INTO stock_basic 
                        (ts_code, symbol, name, area, industry, cnspell, market, list_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, stock)
                
                print(f"✅ 示例股票数据: {len(sample_stocks)} 条记录")
                
                # 插入示例日线数据
                sample_daily_data = [
                    ('000001.SZ', '2024-01-15', 12.50, 12.80, 12.30, 12.60, 12.40, 0.20, 1.61, 1000000, 12600000),
                    ('000001.SZ', '2024-01-16', 12.60, 12.90, 12.50, 12.70, 12.60, 0.10, 0.81, 1200000, 15240000),
                    ('000002.SZ', '2024-01-15', 15.20, 15.50, 15.00, 15.30, 15.10, 0.20, 1.32, 800000, 12240000),
                    ('000002.SZ', '2024-01-16', 15.30, 15.60, 15.20, 15.40, 15.30, 0.10, 0.66, 900000, 13860000)
                ]
                
                for data in sample_daily_data:
                    cursor.execute("""
                        INSERT IGNORE INTO daily_data 
                        (ts_code, trade_date, open, high, low, close, pre_close, change_amount, pct_chg, vol, amount)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, data)
                
                print(f"✅ 示例日线数据: {len(sample_daily_data)} 条记录")
                
                self.connection.commit()
                return True
                
        except Exception as e:
            print(f"❌ 创建示例数据失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("✅ 数据库连接已关闭")
    
    def run(self, sql_file_path='database_schema.sql'):
        """运行完整的初始化流程"""
        print("🚀 开始初始化MySQL数据库...")
        print("=" * 60)
        
        # 1. 连接数据库
        if not self.connect():
            return False
        
        # 2. 创建数据库
        if not self.create_database():
            return False
        
        # 3. 执行SQL文件
        if not self.execute_sql_file(sql_file_path):
            return False
        
        # 4. 验证表创建
        if not self.verify_tables():
            return False
        
        # 5. 检查初始数据
        if not self.check_initial_data():
            return False
        
        # 6. 创建示例数据
        if not self.create_sample_data():
            return False
        
        print("\n🎉 数据库初始化完成!")
        print("=" * 60)
        print("📋 数据库信息:")
        print(f"   主机: {self.host}:{self.port}")
        print(f"   数据库: {self.database}")
        print(f"   用户: {self.user}")
        print("\n🔗 连接信息:")
        print(f"   应用连接: mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}")
        print(f"   只读用户: stock_readonly@%")
        print(f"   应用用户: stock_app@%")
        print(f"   管理员: stock_admin@%")
        
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MySQL数据库初始化工具')
    parser.add_argument('--host', default='localhost', help='MySQL主机地址')
    parser.add_argument('--port', type=int, default=3306, help='MySQL端口')
    parser.add_argument('--user', default='root', help='MySQL用户名')
    parser.add_argument('--password', default='6116988.niu', help='MySQL密码')
    parser.add_argument('--sql-file', default='database_schema.sql', help='SQL文件路径')
    
    args = parser.parse_args()
    
    # 创建初始化器
    initializer = DatabaseInitializer(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password
    )
    
    try:
        # 运行初始化
        success = initializer.run(args.sql_file)
        if success:
            print("\n✅ 数据库初始化成功完成!")
            sys.exit(0)
        else:
            print("\n❌ 数据库初始化失败!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)
    finally:
        initializer.close()

if __name__ == '__main__':
    main() 