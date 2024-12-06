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
    
    print(f"{data["每日dde散户数量与股价走势"]["barline3"].iloc[-1].to_list()[-1]}")

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
        print(f"{stock_data[stock_code]['now']},  {stock_data[stock_code]['涨跌(%)']}, {stock_data[stock_code]['量比']}, {stock_data[stock_code]['均价']}")
        time.sleep(interval)

thread_list = [] 
thread_list.append(threading.Thread(target=print_now_info, args=('嵘泰股份', '605133', 150)))
thread_list.append(threading.Thread(target=print_sh_info, args=('605133', 15)))
for i in thread_list:
    i.start()

for i in thread_list:
    i.join()