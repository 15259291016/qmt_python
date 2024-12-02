# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.moneyflow_ind_ths(**{
    "ts_code": "",
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "ts_code",
    "industry",
    "lead_stock",
    "close",
    "pct_change",
    "company_num",
    "pct_change_stock",
    "close_price",
    "net_buy_amount",
    "net_sell_amount",
    "net_amount"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','资金流向数据', '行业资金流向(THS).csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

