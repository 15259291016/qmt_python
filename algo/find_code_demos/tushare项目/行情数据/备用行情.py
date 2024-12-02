# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.bak_daily(**{
    "ts_code": "",
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "offset": "",
    "limit": ""
}, fields=[
    "ts_code",
    "trade_date",
    "name",
    "pct_change",
    "close",
    "change",
    "open",
    "high",
    "low",
    "pre_close",
    "vol_ratio",
    "turn_over",
    "swing",
    "vol",
    "amount",
    "selling",
    "buying",
    "total_share",
    "float_share",
    "pe",
    "industry",
    "area",
    "float_mv",
    "total_mv",
    "avg_price",
    "strength",
    "activity",
    "avg_turnover",
    "attack",
    "interval_3",
    "interval_6"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','行情数据', '备用行情.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

