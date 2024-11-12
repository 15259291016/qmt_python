# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.ggt_monthly(**{
    "month": "",
    "start_month": "",
    "end_month": "",
    "limit": "",
    "offset": ""
}, fields=[
    "month",
    "day_buy_amt",
    "day_buy_vol",
    "day_sell_amt",
    "day_sell_vol",
    "total_buy_amt",
    "total_buy_vol",
    "total_sell_amt",
    "total_sell_vol"
])
print(df)

