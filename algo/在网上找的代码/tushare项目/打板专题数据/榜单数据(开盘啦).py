# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.kpl_list(**{
    "ts_code": "",
    "trade_date": "",
    "tag": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "name",
    "trade_date",
    "lu_time",
    "ld_time",
    "open_time",
    "last_time",
    "lu_desc",
    "tag",
    "theme",
    "net_change",
    "bid_amount",
    "status",
    "bid_change",
    "bid_turnover",
    "lu_bid_vol",
    "pct_chg",
    "bid_pct_chg",
    "rt_pct_chg",
    "limit_order",
    "amount",
    "turnover_rate",
    "free_float",
    "lu_limit_order"
])
print(df)

