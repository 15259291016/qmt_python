#!/usr/bin/env python3
"""
简化的MySQL数据库初始化脚本
用于创建量化交易平台所需的所有表结构和初始数据
"""

import pymysql
import os
import sys
from datetime import datetime

def main():
    """主函数"""
    print("🚀 开始初始化MySQL数据库...")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 数据库连接配置
    db_config = {
        'host': '120.26.202.151',
        'port': 3306,
        'user': 'root',
        'password': '611698',
        'database': 'stock_data',
        'charset': 'utf8mb4',
        'connect_timeout': 60,
        'read_timeout': 30,
        'write_timeout': 30
    }
    
    print("🔍 连接信息:")
    print(f"   服务器: {db_config['host']}:{db_config['port']}")
    print(f"   用户: {db_config['user']}")
    print(f"   数据库: {db_config['database']}")
    print()
    
    try:
        # 连接数据库
        print("🔄 正在连接数据库...")
        connection = pymysql.connect(**db_config)
        print("✅ 数据库连接成功")
        
        # 读取SQL文件
        sql_file_path = 'database_schema.sql'
        if not os.path.exists(sql_file_path):
            print(f"❌ SQL文件不存在: {sql_file_path}")
            return False
        
        print(f"📖 读取SQL文件: {sql_file_path}")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        sql_statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # 跳过注释和空行
            if line.startswith('--') or line.startswith('#') or not line:
                continue
            
            current_statement += line + " "
            
            if line.endswith(';'):
                sql_statements.append(current_statement.strip())
                current_statement = ""
        
        print(f"📋 找到 {len(sql_statements)} 个SQL语句")
        print()
        
        # 执行SQL语句
        with connection.cursor() as cursor:
            for i, statement in enumerate(sql_statements, 1):
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        print(f"✅ 执行SQL语句 {i}/{len(sql_statements)}: {statement[:50]}...")
                    except Exception as e:
                        print(f"⚠️  SQL语句执行失败 {i}: {e}")
                        print(f"   语句: {statement[:100]}...")
                        # 继续执行其他语句
            
            connection.commit()
            print(f"\n✅ 所有SQL语句执行完成")
        
        # 验证表创建
        print("\n🔍 验证表创建...")
        with connection.cursor() as cursor:
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
            
            print(f"📊 数据库表数量: {len(tables)}")
            print("📋 表列表:")
            for i, table in enumerate(tables, 1):
                print(f"   {i:2d}. {table}")
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"\n⚠️  缺失的表: {', '.join(missing_tables)}")
            else:
                print(f"\n🎉 所有预期表都已创建!")
        
        # 检查初始数据
        print("\n📋 检查初始数据...")
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT COUNT(*) FROM system_config")
                config_count = cursor.fetchone()[0]
                print(f"✅ 系统配置: {config_count} 条记录")
            except:
                print("⚠️  系统配置表为空或不存在")
            
            try:
                cursor.execute("SELECT COUNT(*) FROM risk_config")
                risk_count = cursor.fetchone()[0]
                print(f"✅ 风控配置: {risk_count} 条记录")
            except:
                print("⚠️  风控配置表为空或不存在")
        
        connection.close()
        print("\n" + "=" * 60)
        print("🎉 数据库初始化完成!")
        print("💡 您现在可以开始使用数据库进行开发了")
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        print("\n💡 可能的解决方案:")
        print("1. 检查网络连接是否正常")
        print("2. 检查数据库配置是否正确")
        print("3. 检查SQL文件是否存在")
        print("4. 检查数据库权限")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 