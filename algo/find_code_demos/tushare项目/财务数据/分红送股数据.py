# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.dividend(**{
    "ts_code": 2120,
    "ann_date": "",
    "end_date": "",
    "record_date": "",
    "ex_date": "",
    "imp_ann_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "end_date",
    "ann_date",
    "div_proc",
    "stk_div",
    "stk_bo_rate",
    "stk_co_rate",
    "cash_div",
    "cash_div_tax",
    "record_date",
    "ex_date",
    "pay_date",
    "div_listdate",
    "imp_ann_date",
    "base_date",
    "base_share",
    "update_flag"
])
print(df)

