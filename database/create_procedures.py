#!/usr/bin/env python3
"""
创建存储过程和触发器脚本
"""

import pymysql
import os
import sys
from datetime import datetime

def execute_procedures():
    """执行存储过程和触发器"""
    print("🚀 开始创建存储过程和触发器...")
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
    
    try:
        # 连接数据库
        print("🔄 正在连接数据库...")
        connection = pymysql.connect(**db_config)
        print("✅ 数据库连接成功")
        
        # 读取SQL文件
        sql_file_path = 'database_procedures.sql'
        if not os.path.exists(sql_file_path):
            print(f"❌ SQL文件不存在: {sql_file_path}")
            return False
        
        print(f"📖 读取SQL文件: {sql_file_path}")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（处理DELIMITER）
        sql_statements = []
        current_statement = ""
        delimiter = ";"
        
        lines = sql_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过注释和空行
            if line.startswith('--') or line.startswith('#') or not line:
                i += 1
                continue
            
            # 检查DELIMITER语句
            if line.upper().startswith('DELIMITER'):
                delimiter = line.split()[1]
                i += 1
                continue
            
            current_statement += line + " "
            
            if line.endswith(delimiter):
                sql_statements.append(current_statement.strip())
                current_statement = ""
            
            i += 1
        
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
        
        # 验证存储过程和触发器
        print("\n🔍 验证存储过程和触发器...")
        with connection.cursor() as cursor:
            # 检查存储过程
            cursor.execute("SHOW PROCEDURE STATUS WHERE Db = 'stock_data'")
            procedures = cursor.fetchall()
            print(f"📊 存储过程数量: {len(procedures)}")
            for proc in procedures:
                print(f"   - {proc[1]}")
            
            # 检查触发器
            cursor.execute("SHOW TRIGGERS")
            triggers = cursor.fetchall()
            print(f"📊 触发器数量: {len(triggers)}")
            for trigger in triggers:
                print(f"   - {trigger[0]}")
        
        connection.close()
        print("\n" + "=" * 60)
        print("🎉 存储过程和触发器创建完成!")
        return True
        
    except Exception as e:
        print(f"❌ 创建存储过程和触发器失败: {e}")
        return False

if __name__ == "__main__":
    success = execute_procedures()
    sys.exit(0 if success else 1) 