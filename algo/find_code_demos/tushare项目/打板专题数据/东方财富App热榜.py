# 一天最多2次
# 导入tushare
import tushare as ts

# 7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020          # 15259291016
# 4c3dc659f980eee492435040f724d384d032eb0bba7d50b8dc43c3b1          
# 1e1642bf41b53b487916b343c3afadd224737579c64dc1b9ddae1539
# 初始化pro接口
pro = ts.pro_api('1e1642bf41b53b487916b343c3afadd224737579c64dc1b9ddae1539')

# 拉取数据
df = pro.dc_hot(**{
    "trade_date": "20241230",
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

