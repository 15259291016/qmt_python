# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.hk_hold(**{
    "code": "",
    "ts_code": "002120.SZ",
    "trade_date": 20241106,
    "start_date": "",
    "end_date": "",
    "exchange": "",
    "limit": "",
    "offset": ""
}, fields=[
    "code",
    "trade_date",
    "ts_code",
    "name",
    "vol",
    "ratio",
    "exchange"
])
print(df)

