# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.forecast(**{
    "ts_code": 2120,
    "ann_date": "",
    "start_date": "",
    "end_date": "",
    "period": "",
    "type": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "ann_date",
    "end_date",
    "type",
    "p_change_min",
    "p_change_max",
    "net_profit_min",
    "net_profit_max",
    "last_parent_net",
    "first_ann_date",
    "summary",
    "change_reason",
    "update_flag"
])
print(df)

