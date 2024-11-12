# 导入tushare
import tushare as ts
from sqlalchemy import create_engine

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')
engine = create_engine('postgresql://postgres:611698@localhost:5432/data')
# 拉取数据
df = pro.moneyflow_dc(**{
    "ts_code": "",
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "ts_code",
    "name",
    "pct_change",
    "close",
    "net_amount",
    "net_amount_rate",
    "buy_elg_amount",
    "buy_elg_amount_rate",
    "buy_lg_amount",
    "buy_lg_amount_rate",
    "buy_md_amount",
    "buy_md_amount_rate",
    "buy_sm_amount",
    "buy_sm_amount_rate"
])
print(df)
df.to_sql('个股资金流向(DC)', engine, if_exists='replace', index=False)
