"""

"""
import easyquotation
import pandas as pd


quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']

# 获取所有股票行情
all_data = quotation.market_snapshot(prefix=True)  # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀

all_stock_info = pd.DataFrame(all_data.values())
print(all_stock_info)
