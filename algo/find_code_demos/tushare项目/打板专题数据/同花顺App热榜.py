# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.ths_hot(**{
    "trade_date": "20241106",
    "ts_code": "",
    "market": "",
    "is_new": "",
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "data_type",
    "ts_code",
    "ts_name",
    "rank",
    "pct_change",
    "current_price",
    "hot",
    "concept",
    "rank_time",
    "rank_reason"
])
print(df)

