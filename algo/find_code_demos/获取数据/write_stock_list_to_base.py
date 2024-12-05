import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# 使用示例
load_dotenv()

user = os.getenv("PG_USER")
password = os.getenv("PG_PASSWORD")
host = os.getenv("PG_HOST")
port = os.getenv("PG_PORT")
dbname = os.getenv("PG_DBNAME")

# PostgreSQL数据库连接信息
db_params = {
    'dbname': dbname,
    'user': user,
    'password': password,
    'host': host,
    'port': port
}

# 创建数据库连接引擎
engine = create_engine(f'postgresql+psycopg2://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["dbname"]}')

# 读取CSV文件
csv_file_path = u'./algo/find_code_demos/tushare项目/data/基础数据/股票列表.csv'    # 替换为您的CSV文件路径
df = pd.read_csv(csv_file_path)

# 将列名转换为小写以匹配表定义（如果需要）
df.columns = df.columns.str.lower()

# 如果CSV中的日期列不是正确的日期格式，可以使用pd.to_datetime转换
df['list_date'] = pd.to_datetime(df['list_date'], format='%Y%m%d')

# 写入到PostgreSQL的company_info表中
df.to_sql('company_info', engine, if_exists='append', index=False, method='multi')

print("Data has been successfully written to the company_info table.")