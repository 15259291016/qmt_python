# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.fina_mainbz(**{
    "ts_code": 2120,
    "period": "",
    "type": "",
    "start_date": "",
    "end_date": "",
    "is_publish": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "end_date",
    "bz_item",
    "bz_code",
    "bz_sales",
    "bz_profit",
    "bz_cost",
    "curr_type"
])
print(df)

