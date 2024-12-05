"""

"""
import easyquotation
import pandas as pd
import time

quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']

# 获取所有股票行情
# all_data = quotation.market_snapshot(prefix=True)  # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀

# all_stock_info = pd.DataFrame(all_data.values())
# print(all_stock_info)

# 获取嵘泰股份公司当天的股价
stock_code = '605133'


# 打印嵘泰股份公司的股价信息
# print(stock_data[stock_code].keys())
# while True:
#     stock_data = quotation.real(stock_code)
#     print(f"{stock_data[stock_code]["now"]},{stock_data[stock_code]["涨跌(%)"]},{stock_data[stock_code]["量比"]},{stock_data[stock_code]["均价"]}")
#     time.sleep(15)

stock_data = quotation.real(stock_code)
print(stock_data)