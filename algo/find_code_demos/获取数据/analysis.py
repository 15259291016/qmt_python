
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 示例数据
df = pd.read_csv("stock_data.csv")
print(df.columns)
# 计算滚动最高点
df['rolling_max'] = df['now'].rolling(window=10, min_periods=1).max()

# 识别最高点并发出SELL信号
df['signal'] = np.where(df['now'] == df['rolling_max'], 'SELL', np.nan)

# 打印结果
# print(df[['trade_datetime', 'now', 'rolling_max', 'signal']])
for index, row in df[['trade_datetime', 'now', 'rolling_max', 'signal']].iterrows():
    print(row['trade_datetime'], row['now'], row['rolling_max'], row['signal'])
    time.sleep(3)