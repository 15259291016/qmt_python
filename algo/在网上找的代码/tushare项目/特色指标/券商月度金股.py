# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.broker_recommend(**{
    "month": 202410,
    "limit": "",
    "offset": ""
}, fields=[
    "month",
    "broker",
    "ts_code",
    "name"
])
print(df)

