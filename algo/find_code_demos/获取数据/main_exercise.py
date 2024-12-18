import threading
import easyquotation
import pandas as pd
import time
import datetime
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, JSON, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import insert
from wc import WC
import pywencai as wc

load_dotenv()

user = os.getenv("PG_USER")
password = os.getenv("PG_PASSWORD")
host = os.getenv("PG_HOST")
port = os.getenv("PG_PORT")
dbname = os.getenv("PG_DBNAME")

# 创建数据库连接 URL
wc_data_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
engine = create_engine(wc_data_url)
quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']
sh_num = 0
data = {
    'trade_datetime': [],
    'now': [],  # 模拟收盘价数据
    '涨跌(%)': [],  # 模拟收盘价数据
    '量比': [],  # 模拟收盘价数据
    '均价': [],  # 模拟收盘价数据
}

# 保存数据到 PostgreSQL wc_data 数据库
def save_stock_dde_data_all_today(data: dict, stock_code: str, stock_name: str):
    
    print(data)

def is_trade_time():
    now = time.localtime()
    if (now.tm_hour == 9 and now.tm_min >= 24) or (now.tm_hour == 10) or (now.tm_hour == 11 and now.tm_min <= 30) or (now.tm_hour == 13) or (now.tm_hour == 14) or (now.tm_hour == 15 and now.tm_min == 0):
        return True
    return False


def save_now_info(stock_name, stock_code, interval):
    global sh_num
    while True:
        if is_trade_time() is False:
            time.sleep(60)
            continue
        try:
            stock_dde_info = WC().get_stock_dde_info(stock_name)
            # save_stock_dde_data_all_today(stock_dde_info, stock_code, stock_name)
            sh_num = float(stock_dde_info["barline3"]["dde散户数量"].iloc[-1])
            print(sh_num)
            # df = pd.DataFrame(stock_dde_info)
            # df.to_sql('easyquotation_trade_stock_data_sec', engine, if_exists='append', index=False)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(interval)
        
def save_sh_info(stock_name, stock_code, interval):
    global sh_num
    while True:
        if is_trade_time() is False:
            time.sleep(60)
            continue
        
        # 获取嵘泰股份公司的股价信息
        stock_data = quotation.real(stock_code)
        # print(stock_data[stock_code])
        rename_mapping = {
            'PE': 'pe',
            'PB': 'pb',
            '涨跌(%)': '涨跌百分比',
            '价格/成交量(手)/成交额': '价格成交量成交额',
            '成交量(手)': '成交量手',
            '成交额(万)': '成交额万',
            '市盈(动)': '市盈动',
            '市盈(静)': '市盈静'
        }
        renamed_data = {rename_mapping.get(k, k): v for k, v in stock_data[stock_code].items()}
        for i in renamed_data.keys():
            renamed_data[i] = [renamed_data[i]]
        # 将 dict 转换为 DataFrame
        renamed_data["unknown"] = [1]
        renamed_data["最近逐笔成交"] = [0]
        df = pd.DataFrame(renamed_data)
        # 将 DataFrame 写入到 PostgreSQL 数据库中的表
        df.to_sql('easyquotation_trade_stock_data_sec', engine, if_exists='append', index=False)
        ef = pd.DataFrame([{"ts_code":stock_code,"now":stock_data[stock_code]['now'], "涨跌":stock_data[stock_code]['涨跌(%)'], "量比":stock_data[stock_code]['量比'],"均价":stock_data[stock_code]['均价']}])
        ef.to_sql('trade_data', engine, if_exists='append', index=False)
        print(f"{sh_num}---{stock_data[stock_code]['now']}, {stock_data[stock_code]['涨跌(%)']},{stock_data[stock_code]['量比']},{stock_data[stock_code]['均价']}")
        print("Data inserted successfully")
        time.sleep(interval)

thread_list = []
thread_list.append(threading.Thread(target=save_now_info, args=('河化股份', '000953', 60)))
thread_list.append(threading.Thread(target=save_sh_info, args=('河化股份','000953', 3)))
for i in thread_list:
    i.start()
    
for i in thread_list:
    i.join()