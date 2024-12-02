# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.hsgt_top10(**{
    "ts_code": "",
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "market_type": "",
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "ts_code",
    "name",
    "close",
    "change",
    "rank",
    "market_type",
    "amount",
    "net_amount",
    "buy",
    "sell"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','行情数据', '沪深股通十大成交股.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

