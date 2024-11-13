# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.ccass_hold_detail(**{
    "ts_code": "002120.SZ",
    "trade_date": 20241107,
    "start_date": "",
    "end_date": "",
    "hk_code": "",
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "ts_code",
    "name",
    "col_participant_id",
    "col_participant_name",
    "col_shareholding",
    "col_shareholding_percent"
])
print(df)

