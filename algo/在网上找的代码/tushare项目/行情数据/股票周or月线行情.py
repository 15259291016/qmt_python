# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.stk_weekly_monthly(**{
    "ts_code": "",
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "freq": "week", # month
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "trade_date",
    "freq",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "vol",
    "amount",
    "change",
    "pct_chg"
])
print(df)

