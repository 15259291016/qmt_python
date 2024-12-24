
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


def save_sh_info(stock_name:list[str], interval):
    stock_code_list = stock_names_to_list(stock_name)
    df_dict = {}
    for stock_code in stock_code_list:
        df_dict[stock_code] = pd.DataFrame()
    df = None
    cjbs = 0
    while True:
        # if is_trade_time() is False:
        #     time.sleep(60)
        #     continue
        # 获取嵘泰股份公司的股价信息
        print(stock_code_list)
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
            # 将 dict 转换为 DataFrame
            renamed_data["unknown"] = [1]
            # renamed_data["最近逐笔成交"] = [0]
            # print(renamed_data)
            ef = pd.DataFrame(renamed_data)
            ef['rolling_max'] = ef['涨跌'].rolling(window=10, min_periods=1).max()
            ef['rolling_min'] = ef['涨跌'].rolling(window=10, min_periods=1).min()
            if len(df_dict[stock_code])<=10:
                ef['signal_sell'] = np.nan
                ef['signal_buy'] = np.nan
                df_dict[stock_code] = pd.concat([df_dict[stock_code], ef], ignore_index=True)
            else:
                ef['signal_sell'] = np.where(ef['涨跌'] >= df_dict[stock_code]['rolling_max'].max(), 'SELL', np.nan)
                ef['signal_buy'] = np.where(ef['涨跌'] > df_dict[stock_code]['rolling_min'].min(), 'BUY', np.nan)
                df_dict[stock_code] = pd.concat([df_dict[stock_code], ef], ignore_index=True)
            # if df is None:
                # df = pd.DataFrame(pd.DataFrame([{"ts_code":stock_code,"now":stock_data[stock_code]['now'], "涨跌":stock_data[stock_code]['涨跌(%)'], "量比":stock_data[stock_code]['量比'],"均价":stock_data[stock_code]['均价']}]))
            # else:
                # ef = pd.DataFrame([{"ts_code":stock_code,"now":stock_data[stock_code]['now'], "涨跌":stock_data[stock_code]['涨跌(%)'], "量比":stock_data[stock_code]['量比'],"均价":stock_data[stock_code]['均价']}])
                # # 计算滚动最高点
                # ef['rolling_max'] = df['now'].rolling(window=10, min_periods=1).max()
                # ef['rolling_min'] = df['涨跌'].rolling(window=10, min_periods=1).min()
                # if len(df)>=10:
                #     ef['signal_sell'] = np.where(ef['now'] > df['rolling_max'].max(), 'SELL', np.nan)
                #     ef['signal_buy'] = np.where(ef['涨跌'] > df['rolling_min'].min() , 'BUY', np.nan)
                # else:
                #     ef['signal_sell'] = np.where(ef['now'] == ef['rolling_max'], 'SELL', np.nan)
                #     ef['signal_buy'] = np.where(ef['涨跌'] > ef['rolling_min'], 'BUY', np.nan)
                # df = pd.concat([df, ef], ignore_index=True)
                # jgcjl = renamed_data["价格成交量成交额"][0].split("/")
                # print(f"{df['now'].iloc[-1]}, {df['涨跌'].iloc[-1]},{df['量比'].iloc[-1]},{df['均价'].iloc[-1]},{df['signal_sell'].iloc[-1]},{df['signal_buy'].iloc[-1]},{jgcjl[1]}, {int(jgcjl[1]) - cjbs}")
                # if cjbs != int(jgcjl[1]):
                #     cjbs = int(jgcjl[1])
            print(df_dict[stock_code].tail(1))
        print(df_dict)
        print('-'*50)
        time.sleep(interval)

save_sh_info(['嵘泰股份','宝胜股份','精伦电子','华胜天成', '中国核电', '国机精工', '电光科技', '小方制药', '中际旭创'], 3)
# 中国核电、国机精工、电光科技、小方制药、中际旭创