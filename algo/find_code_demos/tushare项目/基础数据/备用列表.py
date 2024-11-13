# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.bak_basic(**{
    "trade_date": "",
    "ts_code": "",
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "ts_code",
    "name",
    "industry",
    "area",
    "pe",
    "float_share",
    "total_share",
    "total_assets",
    "liquid_assets",
    "fixed_assets",
    "reserved",
    "reserved_pershare",
    "eps",
    "bvps",
    "pb",
    "list_date",
    "undp",
    "per_undp",
    "rev_yoy",
    "profit_yoy",
    "gpr",
    "npr",
    "holder_num"
])
print(df)

