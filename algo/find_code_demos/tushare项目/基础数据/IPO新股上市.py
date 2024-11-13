# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.new_share(**{
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "sub_code",
    "name",
    "ipo_date",
    "issue_date",
    "amount",
    "market_amount",
    "price",
    "pe",
    "limit_amount",
    "funds",
    "ballot"
])
print(df)

