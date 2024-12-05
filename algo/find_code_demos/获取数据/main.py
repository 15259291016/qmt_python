import threading
import easyquotation
import pandas as pd
import time
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, JSON, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import insert
from wc import WC

load_dotenv()

user = os.getenv("PG_USER")
password = os.getenv("PG_PASSWORD")
host = os.getenv("PG_HOST")
port = os.getenv("PG_PORT")
dbname = os.getenv("PG_DBNAME")

# 创建数据库连接 URL
wc_data_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
engine = create_engine(wc_data_url)
# 保存数据到 PostgreSQL wc_data 数据库
def save_stock_dde_data_all_today(data: dict, stock_code: str, stock_name: str):
    

    # 定义表结构
    metadata = MetaData()
    wc_stock_data = Table('wc_stock_data', metadata,
                          Column('id', Integer, primary_key=True),
                          Column('stock_code', String),
                          Column('stock_name', String),
                          Column('data', JSON),
                          Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')))

    # 将 dict 转换为 DataFrame
    # 将 DataFrame 转换为 JSON 字符串
    data_json = {
        "data":
            {
            "suggestion":data["container"]["txt1"][60:-12],
            # ""
            }
        }
    
    data_json = data

    # 插入数据
    with engine.connect() as connection:
        insert_stmt = insert(wc_stock_data).values(
            stock_code=stock_code,
            stock_name=stock_name,
            data=data_json
        )
        connection.execute(insert_stmt)
        print("Data inserted successfully")

def is_trade_time():
    now = time.localtime()
    if now.tm_hour >= 9 and now.tm_hour <= 15:
        return True
    return False

def print_now_info(stock_name, stock_code, interval):
    while True:
        stock_dde_info = WC().get_stock_dde_info(stock_name)
        save_stock_dde_data_all_today(stock_dde_info, stock_code, stock_name)
        time.sleep(interval)

def print_sh_info(stock_code, interval):
    quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']
    while True:
        # 获取嵘泰股份公司的股价信息
        stock_data = quotation.real(stock_code)
        # print(f"当前价格: {stock_data[stock_code]['now']}, 涨跌幅: {stock_data[stock_code]['涨跌(%)']}, 量比: {stock_data[stock_code]['量比']}, 均价: {stock_data[stock_code]['均价']}")
        time.sleep(interval)

thread_list = [] 
thread_list.append(threading.Thread(target=print_now_info, args=('嵘泰股份', '603331', 150)))
# thread_list.append(threading.Thread(target=print_sh_info, args=('603331', 15)))
for i in thread_list:
    i.start()

for i in thread_list:
    i.join()