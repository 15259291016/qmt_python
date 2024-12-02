# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.stk_surv(**{
    "ts_code": "002120.SZ",
    "trade_date": 20241107,
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "name",
    "surv_date",
    "fund_visitors",
    "rece_place",
    "rece_mode",
    "rece_org",
    "org_type",
    "comp_rece"
])
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','特色指标', '机构调研数据.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

