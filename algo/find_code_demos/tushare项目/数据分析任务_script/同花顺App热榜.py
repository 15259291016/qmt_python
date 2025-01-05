import pandas as pd
from pathlib import Path

# 获取当前脚本所在的目录
script_dir = Path(__file__).parent

# 拼接路径
data_dir = script_dir.parent / "data" / "打板专题数据"
file_path = data_dir / "同花顺App热榜.csv"

# 打印路径
print("文件路径:", file_path)
# 读取 CSV 文件
# file_path = "同花顺App热榜.csv"
df = pd.read_csv(file_path)

# 筛选出 data_type 为 "热股" 的行
hot_stocks = df[df["data_type"] == "热股"]

# 打印筛选结果
print(hot_stocks)

# 如果需要保存到新的 CSV 文件
# hot_stocks.to_csv("热股信息.csv", index=False, encoding="utf_8_sig")