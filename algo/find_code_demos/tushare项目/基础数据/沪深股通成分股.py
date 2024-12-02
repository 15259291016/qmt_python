# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.hs_const(**{
    "hs_type": "SZ",    #SH
    "is_new": "",
    "ts_code": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "hs_type",
    "in_date",
    "out_date",
    "is_new"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','基础数据', '沪深股通成分股.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

