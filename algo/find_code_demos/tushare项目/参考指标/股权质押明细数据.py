# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.pledge_detail(**{
    "ts_code": 2120,
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "ann_date",
    "holder_name",
    "pledge_amount",
    "start_date",
    "end_date",
    "is_release",
    "release_date",
    "pledgor",
    "holding_amount",
    "pledged_amount",
    "p_total_ratio",
    "h_total_ratio",
    "is_buyback"
])
print(df)

