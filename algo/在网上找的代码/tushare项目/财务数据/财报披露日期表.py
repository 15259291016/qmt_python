# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.disclosure_date(**{
    "ts_code": 2120,
    "end_date": "",
    "pre_date": "",
    "actual_date": "",
    "offset": "",
    "limit": ""
}, fields=[
    "ts_code",
    "ann_date",
    "end_date",
    "pre_date",
    "actual_date"
])
print(df)

