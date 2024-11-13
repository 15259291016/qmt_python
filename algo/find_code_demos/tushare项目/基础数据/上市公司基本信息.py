# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.stock_company(**{
    "ts_code": "",
    "exchange": "",
    "status": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "com_name",
    "com_id",
    "chairman",
    "manager",
    "secretary",
    "reg_capital",
    "setup_date",
    "province",
    "city",
    "introduction",
    "website",
    "email",
    "office",
    "business_scope",
    "employees",
    "main_business",
    "exchange"
])
print(df)

