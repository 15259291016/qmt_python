# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.slb_len_mm(**{
    "trade_date": "20241106",
    "ts_code": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "ts_code",
    "name",
    "ope_inv",
    "lent_qnt",
    "cls_inv",
    "end_bal"
])
print(df)

