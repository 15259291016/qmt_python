import time
import os
import tushare as ts
import pandas as pd
import efinance as ef
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv  # 新增

# 加载.env文件
load_dotenv()

# tushare token从环境变量获取
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(TUSHARE_TOKEN)  # 5000积分


# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)


def save_all_stock_list():
    # 拉取数据
    df = pro.stock_basic(**{
        "ts_code": "",
        "name": "",
        "exchange": "",
        "market": "",
        "is_hs": "",
        "list_status": "",
        "limit": "",
        "offset": ""
    }, fields=[
        "ts_code",
        "symbol",
        "name",
        "area",
        "industry",
        "cnspell",
        "market",
        "list_date",
        "act_name",
        "act_ent_type"
    ])
    # 构建目标路径
    target_path = os.path.join('data', '股票列表.csv')

    # 保存DataFrame到CSV文件
    df.to_csv(target_path, index=False)
    print(df)


def save_one_stock_history_data(stock='000601.SZ'):
    from utils.date_util import get_today_trade_day
    end_day = get_today_trade_day(is_format=True)
    df = pro.daily(ts_code=stock)
    df.to_csv(f"./data/all_data/{stock}.csv", index=False)


def download_all_data(stock_list=[]):
    print("download_all_data")
    # 获取当前日期
    now = datetime.now()

    # 格式化为 YYYYMMDD 格式
    formatted_date = now.strftime("%Y%m%d")
    if stock_list == []:
        # 获取股票信息
        # df = ak.stock_info_a_code_name()
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')

        # 确保数据目录存在
        os.makedirs('./data/all_data', exist_ok=True)


        # 获取股票历史数据
        stock_list = list(map(lambda x: x[:-3], list(df['ts_code'])))
    all_data = ef.stock.get_quote_history(stock_list, formatted_date, formatted_date)
    # all_data = ef.stock.get_quote_history(stock_list[:1])
    for code in all_data.keys():
        # 构造文件路径
        file_path = f'./data/all_data/{code}.csv'
        new_data = all_data[code]
        # 检查文件是否存在
        if os.path.exists(file_path):
            # 如果文件存在，读取现有数据
            existing_data = pd.read_csv(file_path)

            # 合并新数据和现有数据
            combined_data = pd.concat([existing_data, new_data], ignore_index=True)

            # 去重（如果需要）
            combined_data = combined_data.drop_duplicates()

            # 保存合并后的数据
            combined_data.to_csv(file_path, encoding='utf-8-sig', index=False)
            print(f"数据已追加到文件: {file_path}")
        else:
            # 如果文件不存在，直接保存新数据
            new_data.to_csv(file_path, encoding='utf-8-sig', index=False)
            print(f"新文件已创建并保存: {file_path}")

def get_all_data_path():
    return r"F:\Code\python\qmt_python\data\all_data"

if __name__ == '__main__':

    print("start")
    df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')

    # 确保数据目录存在
    os.makedirs(os.path.abspath('./data/all_data'), exist_ok=True)

    # 获取股票历史数据
    stock_list = list(map(lambda x: x[:-3], list(df['ts_code'])))
    total_length = len(stock_list)  # 总长度
    num_parts = 20  # 分成的份数
    part_length = total_length // num_parts
    parts = [(i * part_length, (i + 1) * part_length) for i in range(num_parts)]
    code_list = stock_list[parts[0][0]:parts[0][1]]
    download_all_data(code_list)
    # 使用线程池
    # with ThreadPoolExecutor(max_workers=num_parts) as executor:
    #     for part in parts:
    #         code_list = stock_list[part[0]:part[1]]
    #         executor.submit(download_all_data, code_list)
    print("done")
    # save_one_stock_history_data()
    # print("start")
    # df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    #
    # # 确保数据目录存在
    # os.makedirs('./data/all_data', exist_ok=True)
    #
    # # 获取当前日期
    # now = datetime.now()

    # 格式化为 YYYYMMDD 格式
    # formatted_date = now.strftime("%Y%m%d")
    # 获取股票历史数据
    # stock_list = list(map(lambda x: x[:-3], list(df['ts_code'])))
    # total_length = len(stock_list)  # 总长度
    # num_parts = 5  # 分成的份数
    # part_length = total_length // num_parts
    # parts = [(i * part_length, (i + 1) * part_length) for i in range(num_parts)]
    # thread_list = []
    # for i, part in enumerate(parts):
    #     # print(stock_list[part[0]:part[1]])
    #     code_list = stock_list[part[0]:part[1]]
    #     print(code_list)
    #     thread_list.append(threading.Thread(target=download_all_data, args=(code_list,)))
    #     # print(f"Part {i + 1}: {part}")
    # for i in thread_list:
    #     i.start()
    #     i.join()
    # print("done")
