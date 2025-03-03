import tushare as ts

# 初始化pro接口
pro = ts.pro_api('df14a3576a3afa57b5ed210b9a4e68077110dde3018c06cbba1f00c1')

# 拉取数据
df = pro.stock_basic(**{
    "ts_code": "",
    "name": "",
    "exchange": "",
    "market": "",
    "is_hs": "",
    "list_status": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "symbol",
    "name",
    "area",
    "industry",
    "cnspell",
    "market",
    "list_date",
    "act_name",
    "act_ent_type"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join('data','股票列表.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)