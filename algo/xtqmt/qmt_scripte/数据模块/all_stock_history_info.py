from xtquant import xtdata

# res = xtdata.get_market_data(stock_list=['600519.SH'], period='1d')
# print(res)
# 获取沪深300的板块成分股
# sector = xtdata.get_stock_list_in_sector('沪深300')
# print(sector)

start_date = '20231001'# 格式"YYYYMMDD"，开始下载的日期，date = ""时全量下载
end_date = "" 
period = "1d" 

need_download = 1  # 取数据是空值时，将need_download赋值为1，确保正确下载了历史数据
subscribe = False # 设置订阅参数，使gmd_ex仅返回本地数据
count = -1 # 设置count参数，使gmd_ex返回全部数据

code_list = ["000001.SZ", "600519.SH"] # 股票列表
# data1 = xtdata.get_market_data_ex([],code_list,period = period, start_time = start_date, end_time = end_date)
# print(data1)
############ 仅获取历史行情 #####################
subscribe = False # 设置订阅参数，使gmd_ex仅返回本地数据
count = -1 # 设置count参数，使gmd_ex返回全部数据
data1 = xtdata.get_market_data_ex([],code_list,period = period, start_time = start_date, end_time = end_date)

############ 仅获取最新行情 #####################
subscribe = True # 设置订阅参数，使gmd_ex仅返回最新行情
count = 1 # 设置count参数，使gmd_ex仅返回最新行情数据
data2 = xtdata.get_market_data_ex([],code_list,period = period, start_time = start_date, end_time = end_date, count = 1) # count 设置为1，使返回值只包含最新行情

############ 获取历史行情+最新行情 #####################
subscribe = True # 设置订阅参数，使gmd_ex仅返回最新行情
count = -1 # 设置count参数，使gmd_ex返回全部数据
data3 = xtdata.get_market_data_ex([],code_list,period = period, start_time = start_date, end_time = end_date, count = -1) # count 设置为-1，使返回值包含最新行情和历史行情


print(data1[code_list[0]].tail())# 行情数据查看
print(data2[code_list[0]].tail())
print(data3[code_list[0]].tail())