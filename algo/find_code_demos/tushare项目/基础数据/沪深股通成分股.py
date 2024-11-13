# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.hs_const(**{
    "hs_type": "SZ",    #SH
    "is_new": "",
    "ts_code": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "hs_type",
    "in_date",
    "out_date",
    "is_new"
])
print(df)

