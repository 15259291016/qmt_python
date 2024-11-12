import tushare as ts

# 设置你的tushare API Token
ts.set_token('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')
pro = ts.pro_api()

# 获取股票代码
stock_code = '002085.SZ'  # 例如平安银行

# 获取主力净额数据
df = pro.moneyflow_hsgt(trade_date='20241104')  # 替换为你需要的日期

# 打印数据
print(df)

# 如果需要获取特定股票的主力净额数据
money_flow = pro.moneyflow(ts_code=stock_code, trade_date='20241104')
print(money_flow)
