import pandas as pd
from pathlib import Path

# 获取当前脚本所在的目录
script_dir = Path(__file__).parent

# 拼接路径
data_dir = script_dir.parent / "data" / "打板专题数据"
file_path = data_dir / "东方财富App热榜.csv"

# 打印路径
print("文件路径:", file_path)
# 读取 CSV 文件
# file_path = "同花顺App热榜.csv"
# 读取CSV文件
df = pd.read_csv(file_path)

# 筛选出data_type为A股市场的信息
a_shares_df = df[df['data_type'] == 'A股市场']

# 打印筛选后的数据
print(a_shares_df)