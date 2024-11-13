# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.concept_detail(**{
    "id": "",
    "ts_code": "",
    "limit": "",
    "offset": ""
}, fields=[
    "id",
    "concept_name",
    "ts_code",
    "name"
])
print(df)

