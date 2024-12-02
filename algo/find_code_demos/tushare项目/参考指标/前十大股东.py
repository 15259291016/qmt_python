# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.top10_holders(**{
    "ts_code": "002120",
    "period": "",
    "ann_date": "",
    "start_date": "",
    "end_date": "",
    "offset": "",
    "limit": "",
    "hold_type": ""
}, fields=[
    "ts_code",
    "ann_date",
    "end_date",
    "holder_name",
    "hold_amount",
    "hold_ratio",
    "hold_float_ratio",
    "hold_change",
    "holder_type"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','参考指标', '前十大股东.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

