
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import easyquotation

quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']
def is_trade_time():
    now = time.localtime()
    if (now.tm_hour == 9 and now.tm_min >= 24) or (now.tm_hour == 10) or (now.tm_hour == 11 and now.tm_min <= 30) or (now.tm_hour == 13) or (now.tm_hour == 14) or (now.tm_hour == 15 and now.tm_min == 0):
        return True
    return False
def save_sh_info(stock_name, stock_code, interval):
    df = None
    cjbs = 0
    while True:
        if is_trade_time() is False:
            time.sleep(60)
            continue
        # 获取嵘泰股份公司的股价信息
        stock_data = quotation.real(stock_code)
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
        # renamed_data["最近逐笔成交"] = [0]
        # print(renamed_data)
        if df is None:
            df = pd.DataFrame(pd.DataFrame([{"ts_code":stock_code,"now":stock_data[stock_code]['now'], "涨跌":stock_data[stock_code]['涨跌(%)'], "量比":stock_data[stock_code]['量比'],"均价":stock_data[stock_code]['均价']}]))
        else:
            ef = pd.DataFrame([{"ts_code":stock_code,"now":stock_data[stock_code]['now'], "涨跌":stock_data[stock_code]['涨跌(%)'], "量比":stock_data[stock_code]['量比'],"均价":stock_data[stock_code]['均价']}])
            # 计算滚动最高点
            ef['rolling_max'] = df['now'].rolling(window=10, min_periods=1).max()
            ef['rolling_min'] = df['涨跌'].rolling(window=10, min_periods=1).min()
            if len(df)>=10:
                ef['signal'] = np.where(ef['now'] > df['rolling_max'].max(), 'SELL', np.nan)
                # ef['signal'] = np.where(ef['涨跌'] > df['rolling_min'].min() , 'BUY', np.nan)
            else:
                ef['signal'] = np.where(ef['now'] == ef['rolling_max'], 'SELL', np.nan)
                # ef['signal'] = np.where(ef['涨跌'] > ef['rolling_min'], 'BUY', np.nan)
            df = pd.concat([df, ef], ignore_index=True)
            jgcjl = renamed_data["价格成交量成交额"][0].split("/")
            
            print(f"{df['now'].iloc[-1]}, {df['涨跌'].iloc[-1]},{df['量比'].iloc[-1]},{df['均价'].iloc[-1]},{df['signal'].iloc[-1]},{jgcjl[1]}, {int(jgcjl[1]) - cjbs}")
            
            if cjbs != int(jgcjl[1]):
                cjbs = int(jgcjl[1])

        time.sleep(interval)

save_sh_info('嵘泰股份', '605133', 3)