import pywencai as wc
import pandas as pd
# https://zhuanlan.zhihu.com/p/678521592
import akshare as ak
from akshare import stock_zh_a_hist

# res = wc.get(query='法尔胜', )
# print(res)
stock = stock_zh_a_hist(symbol='603444', period="daily", start_date="20220301", end_date='20231225', adjust="")
print(stock)

stock_history = stock_zh_a_hist(symbol='603444', period='daily', adjust='').iloc[:, 0:6]
# 列名
stock_history.columns = [
    'date',
    'open',
    'close',
    'high',
    'low',
    'volume',
]
# 对列进行重新排序设置成OHLC
stock_history = stock_history[['date', 'open', 'high', 'low', 'close', 'volume']]
# 设置以日期为索引
stock_history.set_index('date', drop=True, inplace=True)

# 保存成csv文件
stock_history.to_csv('./backtra/603444.csv')
print(stock_history)
