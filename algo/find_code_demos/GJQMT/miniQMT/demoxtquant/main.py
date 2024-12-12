# # 导入 xtdatacenter 模块
# from xtquant import xtdatacenter as xtdc  
  
# '''  
# 设置用于登录行情服务的token，此接口应该先于 init_quote 调用

# token可以从投研用户中心获取
# https://xuntou.net/#/userInfo
# '''  
# xtdc.set_token('816c0405e78be6a45fd9ae1a262666d8b0da7dc7')
  
# '''  
# 设置数据存储根目录，此接口应该先于 init_quote 调用  
# datacenter 启动后，会在 data_home_dir 目录下建立若干目录存储数据  
# 此接口不是必须调用，如果不设置，会使用默认路径
# '''  
# # xtdc.set_data_home_dir('data') 

# '''
# 函数用法可通过以下方式查看：
# '''
# # print(help(xtdc.set_data_home_dir))  
  
# '''  
# 初始化行情模块  
# '''  
# xtdc.init()

# '''
# 初始化需要一定时间，完成后即可按照数据字典的对应引导使用
# '''

# 导入 xtdata
import pandas as pd
from xtquant import xtdata  

# # 获取交易日期
# tdl = xtdata.get_trading_dates('SH')  
# print(tdl)  

# 获取板块列表
sl = xtdata.get_stock_list_in_sector('沪深A股')  
print(sl)  

# # 输出平安银行的相关信息 
# data = xtdata.get_instrument_detail("000001.SZ")  
# print(data)

# 其他数据获取的方法请参考数据字典：http://dict.thinktrader.net/dictionary/stock.html  
