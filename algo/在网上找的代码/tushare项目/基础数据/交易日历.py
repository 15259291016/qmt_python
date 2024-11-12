# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.trade_cal(**{
    "exchange": "",
    "cal_date": "",
    "start_date": "",
    "end_date": "",
    "is_open": "",
    "limit": "",
    "offset": ""
}, fields=[
    "exchange",
    "cal_date",
    "is_open",
    "pretrade_date"
])
print(df)

