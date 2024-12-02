# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.fina_mainbz(**{
    "ts_code": 2120,
    "period": "",
    "type": "",
    "start_date": "",
    "end_date": "",
    "is_publish": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "end_date",
    "bz_item",
    "bz_code",
    "bz_sales",
    "bz_profit",
    "bz_cost",
    "curr_type"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','财务数据', '主营业务构成.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

