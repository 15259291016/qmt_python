# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('1e1642bf41b53b487916b343c3afadd224737579c64dc1b9ddae1539')

# 拉取数据
df = pro.ths_hot(**{
    "trade_date": "20240102",
    "ts_code": "",
    "market": "",
    "is_new": "",
    "limit": "",
    "offset": ""
}, fields=[
    "trade_date",
    "data_type",
    "ts_code",
    "ts_name",
    "rank",
    "pct_change",
    "current_price",
    "hot",
    "concept",
    "rank_time",
    "rank_reason"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','打板专题数据', '同花顺App热榜.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

