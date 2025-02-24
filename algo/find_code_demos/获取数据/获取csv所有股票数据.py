import os
import pandas as pd
import akshare as ak
import efinance as ef
from datetime import datetime

# 获取股票信息
df = ak.stock_info_a_code_name()

# 确保数据目录存在
os.makedirs('./data', exist_ok=True)

# 获取当前日期
now = datetime.now()

# 格式化为 YYYYMMDD 格式
formatted_date = now.strftime("%Y%m%d")
# 获取股票历史数据
all_data = ef.stock.get_quote_history(list(df['code']),beg=formatted_date)
for code in all_data.keys():
    # 构造文件路径
    file_path = f'./data/{code}.csv'
    new_data = all_data[code]
    # 检查文件是否存在
    if os.path.exists(file_path):
        # 如果文件存在，读取现有数据
        existing_data = pd.read_csv(file_path)
        
        # 合并新数据和现有数据
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 去重（如果需要）
        combined_data = combined_data.drop_duplicates()
        
        # 保存合并后的数据
        combined_data.to_csv(file_path, encoding='utf-8-sig', index=False)
        print(f"数据已追加到文件: {file_path}")
    else:
        # 如果文件不存在，直接保存新数据
        new_data.to_csv(file_path, encoding='utf-8-sig', index=False)
        print(f"新文件已创建并保存: {file_path}")