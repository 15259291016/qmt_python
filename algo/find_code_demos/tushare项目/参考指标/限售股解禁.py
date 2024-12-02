# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.share_float(**{
    "ts_code": "",
    "ann_date": "",
    "float_date": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "ann_date",
    "float_date",
    "float_share",
    "float_ratio",
    "holder_name",
    "share_type"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','参考指标', '限售股解禁.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

