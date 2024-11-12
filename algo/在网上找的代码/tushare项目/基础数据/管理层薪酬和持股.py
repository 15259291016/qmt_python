# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.stk_rewards(**{
    "ts_code": 2120,        #股票代码
    "end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "ann_date",
    "end_date",
    "name",
    "title",
    "reward",
    "hold_vol"
])
print(df)

