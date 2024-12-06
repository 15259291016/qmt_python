import os
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, JSON, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

class PostgreSQLDatabase:
    def __init__(self, user, password, host, port, dbname="postgres"):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dbname = dbname
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.connection.cursor()
            print(f"Connected to '{self.dbname}' database")
        except Exception as error:
            print(f"Error while connecting to '{self.dbname}' database", error)

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection is closed")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.fetchall()
        except Exception as error:
            print("Error executing query", error)
            self.connection.rollback()
            return None

    def create_database_if_not_exists(self, dbname):
        try:
            self.connect()
            self.cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [dbname])
            exists = self.cursor.fetchone()
            
            if not exists:
                self.cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                print(f"Database '{dbname}' created successfully")
            else:
                print(f"Database '{dbname}' already exists")
        except Exception as error:
            print("Error while checking/creating database", error)
        finally:
            self.close()

    def connect_to_database(self, dbname):
        self.dbname = dbname
        self.connect()

    def create_tables(self, table_definitions):
        try:
            self.connect()
            for table_name, table_definition in table_definitions.items():
                create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({});").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.SQL, table_definition))
                )
                self.cursor.execute(create_table_query)
                self.connection.commit()
                print(f"Table '{table_name}' created successfully")
        except Exception as error:
            print("Error while creating tables", error)
        finally:
            self.close()

# 使用示例
load_dotenv()

user = "postgres"
password = "611698"
host = "120.26.202.151"
port = "5432"
dbname = "data"

# 创建数据库类实例
db = PostgreSQLDatabase(user, password, host, port)

# 检查并创建数据库（如果不存在）
db.create_database_if_not_exists(dbname)

# 连接到新创建的或已存在的数据库
db.connect_to_database(dbname)

# 执行查询
result = db.execute_query("SELECT version();")
if result:
    print("你连接到的数据库信息是: ", result[0], "\n")

# 定义表结构
table_definitions = {
    "wc_stock_data": [
        "id SERIAL PRIMARY KEY",
        "stock_code VARCHAR(20)",
        "stock_name VARCHAR(100)",
        "data JSONB",
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    ],
    "easyquotation_stock_data": [
        "id SERIAL PRIMARY KEY",
        "stock_code VARCHAR(20)",
        "stock_name VARCHAR(100)",
        "data JSONB",
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    ],
    "company_info": [  # 新增表定义
        "ts_code VARCHAR(10) NOT NULL PRIMARY KEY",   # 股票代码
        "symbol VARCHAR(6)",                          # 简称代码
        "name VARCHAR(50)",                           # 公司名称
        "area VARCHAR(50)",                           # 地区
        "industry VARCHAR(50)",                       # 行业
        "cnspell VARCHAR(50)",                        # 拼音缩写
        "market VARCHAR(20)",                         # 市场板块
        "list_date DATE",                             # 上市日期
        "act_name VARCHAR(100)",                      # 实际控制人姓名
        "act_ent_type VARCHAR(50)"                    # 实际控制人类型
    ],
    "trade_data": [  # 新增表定义
        "id SERIAL PRIMARY KEY",
        "ts_code VARCHAR(10) NOT NULL",   # 股票代码
        "trade_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "now FLOAT",
        "涨跌 FLOAT",
        "量比 FLOAT",
        "均价 FLOAT"
    ],
    "easyquotation_trade_stock_data_sec": [  # 新增表定义
        "id SERIAL PRIMARY KEY",
        "name VARCHAR(100)",
        "code VARCHAR(20) NOT NULL",
        "now FLOAT",
        "close FLOAT",
        "open FLOAT",
        "volume FLOAT",
        "bid_volume FLOAT",
        "ask_volume FLOAT",
        "bid1 FLOAT",
        "bid1_volume FLOAT",
        "bid2 FLOAT",
        "bid2_volume FLOAT",
        "bid3 FLOAT",
        "bid3_volume FLOAT",
        "bid4 FLOAT",
        "bid4_volume FLOAT",
        "bid5 FLOAT",
        "bid5_volume FLOAT",
        "ask1 FLOAT",
        "ask1_volume FLOAT",
        "ask2 FLOAT",
        "ask2_volume FLOAT",
        "ask3 FLOAT",
        "ask3_volume FLOAT",
        "ask4 FLOAT",
        "ask4_volume FLOAT",
        "ask5 FLOAT",
        "ask5_volume FLOAT",
        "最近逐笔成交 FLOAT",
        "datetime TIMESTAMP",
        "涨跌 FLOAT",
        "涨跌百分比 FLOAT",
        "high FLOAT",
        "low FLOAT",
        "价格成交量成交额 VARCHAR(100)",
        "成交量手 FLOAT",
        "成交额万 FLOAT",
        "turnover FLOAT",
        "PE FLOAT",
        "unknown VARCHAR(100)",
        "high_2 FLOAT",
        "low_2 FLOAT",
        "振幅 FLOAT",
        "流通市值 FLOAT",
        "总市值 FLOAT",
        "PB FLOAT",
        "涨停价 FLOAT",
        "跌停价 FLOAT",
        "量比 FLOAT",
        "委差 FLOAT",
        "均价 FLOAT",
        "市盈动 FLOAT",
        "市盈静 FLOAT",
        "trade_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    ]
}

# 批量创建表
db.create_tables(table_definitions)

# 关闭连接
db.close()