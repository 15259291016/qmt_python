import tushare as ts
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 初始化tushare API
pro = ts.pro_api('gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482')

# 获取股票数据 - 修正第5行，使用pro接口而不是ts.get_k_data
df = pro.daily(ts_code='600519.SH', start_date='19900101', end_date='20231231')
print("获取到的数据形状:", df.shape)
print("数据列名:", df.columns.tolist())
df.to_csv("600519.csv", index=False)  # 写入文件中，得到股票历史数据信息

# 对股票信息进行策略分析
df = pd.read_csv("600519.csv", index_col="trade_date", parse_dates=["trade_date"])  # 从600519.csv中读取数据，trade_date列作为索引
print("读取后的数据形状:", df.shape)
print("数据时间范围:", df.index.min(), "到", df.index.max())

# 收盘比开盘上涨3% 的所有日期
up_3_percent = df[(df["close"] - df["open"]) / df["open"] > 0.03].index
print("收盘比开盘上涨3%的日期:", up_3_percent)

# 开盘价比前一天收盘价下跌2%的日期
down_2_percent = df[(df["open"] - df["close"].shift(1)) / df["close"].shift(1) < -0.02].index
print("开盘价比前一天收盘价下跌2%的日期:", down_2_percent)

# 重采样为月度和年度数据
df_monthly = df.resample("ME").first()  # 月末
df_yearly = df.resample("YE").last()    # 年末
df_yearly = df_yearly.iloc[:-1, :]     # 去掉最后一行，因为本年最后还没到，取得是昨天的数据

# 计算投资策略
cost = 0
num = 0
for year in range(2010, 2019):
    # 使用年份过滤数据，而不是字符串索引
    year_data = df_monthly[df_monthly.index.year == year]["open"]
    if not year_data.empty:
        cost += (year_data * 100).sum()  # 每月的开盘价买进
        num = 100 * len(year_data)       # 每月买一手，一手是100股
        if year != 2018:
            year_end_data = df_yearly[df_yearly.index.year == year]["open"]
            if not year_end_data.empty:
                cost -= year_end_data.iloc[0] * num  # 卖出股票，抵消花费
                num = 0

# 最后卖出剩余股票
if not df.empty:
    cost -= num * df["close"].iloc[-1]
print("投资策略收益:", -cost)

# 计算移动平均线
df["ma5"] = df["close"].rolling(5).mean()   # 5日移动平均线
df["ma30"] = df["close"].rolling(30).mean() # 30日移动平均线

# 处理数据：丢掉nan并取到需要的时间段
df = df.dropna()
df = df.sort_index()  # 先排序，保证索引单调递增
df = df["2010-01-01":]

# 计算金叉和死叉
sr1 = df["ma5"] < df["ma30"]
sr2 = df["ma5"] >= df["ma30"]

# 死叉：5日均线从上方穿越到下方
death_cross = df[sr1 & sr2.shift(1)].index
# 金叉：5日均线从下方穿越到上方
golden_cross = df[sr2 & sr1.shift(1)].index

# 把金叉和死叉合并起来，一个金叉接着一个死叉排序
sr1 = pd.Series(1, index=golden_cross)
sr2 = pd.Series(0, index=death_cross)
sr = pd.concat([sr1, sr2]).sort_index()

# 模拟交易
first_money = 100000
money = first_money
hold = 0  # 有多少股的股票

for i in range(len(sr)):
    if sr.index[i] in df.index:
        p = df.loc[sr.index[i], "open"]  # 单股价格
        if sr.iloc[i] == 1:  # 金叉
            buy = money // (100 * p)  # 可以买多少手股票
            if buy > 0:
                hold += buy * 100     # 股票数
                money -= buy * 100 * p  # 剩余多少钱
        else:  # 死叉
            money += hold * p  # 卖出股票
            hold = 0

# 最后卖出所有股票
if not df.empty:
    p = df["close"].iloc[-1]
    now_money = hold * p + money
    print("最终资金:", now_money)
    print("收益率:", (now_money - first_money) / first_money * 100, "%")