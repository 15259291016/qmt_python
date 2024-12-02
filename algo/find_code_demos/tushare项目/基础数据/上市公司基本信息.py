# 导入tushare
import tushare as ts

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

# 拉取数据
df = pro.stock_company(**{
    "ts_code": "",
    "exchange": "",
    "status": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "com_name",
    "com_id",
    "chairman",
    "manager",
    "secretary",
    "reg_capital",
    "setup_date",
    "province",
    "city",
    "introduction",
    "website",
    "email",
    "office",
    "business_scope",
    "employees",
    "main_business",
    "exchange"
])

import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建上一级目录的路径
parent_dir = os.path.dirname(current_dir)

# 构建目标路径
target_path = os.path.join(parent_dir, 'data','基础数据', '上市公司基本信息.csv')

# 保存DataFrame到CSV文件
df.to_csv(target_path, index=False)
print(df)

