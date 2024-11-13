# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.repurchase(**{
    "ann_date": "",
    "start_date": "",
    "end_date": "",
    "ts_code": 2120,
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "ann_date",
    "end_date",
    "proc",
    "exp_date",
    "vol",
    "amount",
    "high_limit",
    "low_limit"
])
print(df)

