import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# 获取当前脚本所在的目录
script_dir = Path(__file__).parent

# 拼接路径
data_dir = script_dir.parent / "data" / "打板专题数据"
file_path = data_dir / "涨跌停和炸板数据.csv"

# 打印路径
print("文件路径:", file_path)

# 读取 CSV 文件
df = pd.read_csv(file_path)

# 设置图表风格
plt.figure(figsize=(12, 6))  # 设置图表大小

# 绘制涨停封板率折线图
plt.plot(df["trade_date"], df["turnover_ratio"], marker="o", label="Daily limit sealing rate", color="blue", linewidth=2)

# 绘制涨停破板率折线图
# 假设涨停破板率列名为 "breaking_rate"
plt.plot(df["trade_date"], df["breaking_rate"], marker="o", label="Daily limit breaking rate", color="red", linewidth=2)

# 添加标题和标签
plt.title("Daily limit sealing rate and daily limit breaking rate statistical table", fontsize=16, fontweight="bold")
plt.xlabel("Date", fontsize=12)
plt.ylabel("Percentage (%)", fontsize=12)

# 旋转 x 轴标签
plt.xticks(rotation=45, fontsize=10)

# 设置 y 轴范围
plt.ylim(0, 100)

# 隐藏网格线
plt.grid(False)

# 显示图例
plt.legend(fontsize=12)

# 调整布局
plt.tight_layout()

# 显示图表
plt.show()

# 保存图表为图片
output_path = data_dir / "daily_limit_statistics.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"图表已保存到: {output_path}")