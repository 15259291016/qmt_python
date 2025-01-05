
import pandas as pd
from xtquant import xtdata  

# # 获取交易日期
# tdl = xtdata.get_trading_dates('SH')  
# print(tdl)  

# 获取板块列表
sl = xtdata.get_stock_list_in_sector('沪深A股')  
print(sl)  

# # 输出平安银行的相关信息 
data = xtdata.get_instrument_detail("000001.SZ")  
print(data)

# 其他数据获取的方法请参考数据字典：http://dict.thinktrader.net/dictionary/stock.html  
