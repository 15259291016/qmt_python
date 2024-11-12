# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.top_inst(**{
    "trade_date": 20241107,
    "ts_code": 2120,
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "ts_code",
    "exalter",
    "buy",
    "buy_rate",
    "sell",
    "sell_rate",
    "net_buy",
    "side",
    "reason"
])
print(df)

