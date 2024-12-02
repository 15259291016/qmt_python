# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.dc_hot(**{
    "trade_date": "20241107",
    "ts_code": "",
    "market": "",
    "hot_type": "",
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
    "rank_time"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','打板专题数据', '东方财富App热榜.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

