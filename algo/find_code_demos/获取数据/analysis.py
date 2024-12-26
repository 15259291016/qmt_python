
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import easyquotation
import tushare as ts

from stock_names_to_list import stock_names_to_list

ts.set_token('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')  # 替换为你的 Tushare Token
pro = ts.pro_api()

quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']
def is_trade_time():
    now = time.localtime()
    if (now.tm_hour == 9 and now.tm_min >= 24) or (now.tm_hour == 10) or (now.tm_hour == 11 and now.tm_min <= 30) or (now.tm_hour == 13) or (now.tm_hour == 14) or (now.tm_hour == 15 and now.tm_min == 0):
        return True
    return False


def save_sh_info(stock_name: list[str], interval):
    """
    获取并保存指定股票名称列表的股票信息，并按指定间隔时间更新。

    参数:
        stock_name (list[str]): 要获取信息的股票名称列表。
        interval (int): 每次获取操作之间的时间间隔（以秒为单位）。

    返回:
        None

    该函数执行以下步骤:
    1. 将股票名称列表转换为股票代码列表。
    2. 为每个股票代码初始化一个空的 DataFrame。
    3. 按指定间隔时间连续获取实时股票数据。
    4. 重命名获取数据中的某些列以保持一致性。
    5. 计算 '涨跌'（价格变化）列的滚动最大值和最小值。
    6. 根据滚动值生成买入和卖出信号。
    7. 将新数据连接到每个股票代码的现有 DataFrame。
    8. 打印最新的股票信息和买入/卖出信号。
    9. 在再次获取数据之前按指定间隔时间休眠。
    """ 
    stock_code_list = stock_names_to_list(stock_name)
    df_dict = {}
    for stock_code in stock_code_list:
        df_dict[stock_code] = pd.DataFrame()
    df = None
    cjbs = 0
    while True:
        if is_trade_time() is False:
            time.sleep(60)
            continue
        stock_data = quotation.real(stock_code_list)
        # stock_dataDF = pd.DataFrame(stock_data).T
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
        for stock_code in stock_code_list:
            renamed_data = {rename_mapping.get(k, k): v for k, v in stock_data[stock_code].items()}
            for i in renamed_data.keys():
                renamed_data[i] = [renamed_data[i]]
            renamed_data["unknown"] = [1]
            ef = pd.DataFrame(renamed_data)
            ef['rolling_max'] = ef['涨跌百分比']
            ef['rolling_min'] = ef['涨跌百分比'].rolling(window=100, min_periods=1).min()
            if len(df_dict[stock_code])<=10:
                ef['signal_sell'] = np.nan
                ef['signal_buy'] = np.nan
                df_dict[stock_code] = pd.concat([df_dict[stock_code], ef], ignore_index=True)
            else:
                ef['signal_sell'] = 'sell' if df_dict[stock_code]['rolling_max'].rolling(window=100, min_periods=1).max().max() - ef['涨跌百分比'].iloc[-1] >= 1.5 else np.nan
                ef['signal_buy'] = 'buy' if ef['涨跌百分比'].iloc[-1] - df_dict[stock_code]['rolling_min'].rolling(window=100, min_periods=1).min().min() >= 1.5 else np.nan
                df_dict[stock_code] = pd.concat([df_dict[stock_code], ef], ignore_index=True)
            jgcjl = renamed_data["价格成交量成交额"][0].split("/")
            if cjbs != int(jgcjl[1]):
                cjbs = int(jgcjl[1])
            print(f'{ef["name"].iloc[-1]}:{ef["now"].iloc[-1]}||{ef["涨跌百分比"].iloc[-1]}-{ef["量比"].iloc[-1]}-{ef["均价"].iloc[-1]}' +
                  f'-{df_dict[stock_code]['rolling_max'].rolling(window=100, min_periods=1).max().max()}' +
                  f'-{df_dict[stock_code]['rolling_min'].rolling(window=100, min_periods=1).min().min()}-{ef["signal_sell"].iloc[-1]}-{ef["signal_buy"].iloc[-1]}, {int(jgcjl[1]) - cjbs}')
        # print(df_dict)
        print('-'*100)
        time.sleep(interval)

save_sh_info(['嵘泰股份', '宝胜股份', '精伦电子', '华胜天成', '中国核电', '国机精工', '电光科技', '小方制药', '中际旭创', '好想你', '长盛轴承'], 3)
# 中国核电、国机精工、电光科技、小方制药、中际旭创