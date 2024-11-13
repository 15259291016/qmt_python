import requests
import pandas as pd
import time
import baostock as bs
import numpy as np

# 内容来源:
# https://blog.csdn.net/weixin_46277779/article/details/127123759
# 沪深300数据获取
lg = bs.login()
rs = bs.query_history_k_data_plus("sh.000300", "date,code,open,high,low,close,preclose,volume,amount,pctChg", start_date='2021-01-01', end_date='2024-02-19', frequency="d")
print('query_history_k_data_plus respond error_code:' + rs.error_code)
print('query_history_k_data_plus respond  error_msg:' + rs.error_msg)
# 打印结果集
data_list = []
while (rs.error_code == '0') & rs.next():
    # 获取一条记录，将记录合并在一起
    data_list.append(rs.get_row_data())
result = pd.DataFrame(data_list, columns=rs.fields)
print(result)
# 结果集输出到csv文件
result.to_csv("沪深300.csv", index=False)
bs.logout()
# 沪股通数据获取
import json

columns = ['日期', '当日资金流入', '当日余额', '历史资金累计流入', '当日成交净买入额', '买入成交额', '卖出成交额', '上证指数', '涨跌幅']
data = pd.DataFrame(columns=columns)

headers = {
    'Host': 'datacenter-web.eastmoney.com',
    'Referer': 'http://data.eastmoney.com/',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36'}

for i in range(1, 184):
    url = 'http://datacenter-web.eastmoney.com/api/data/v1/get?callback=jQuery112304911072279904296_1636170506756&sortColumns=TRADE_DATE&sortTypes=-1&pageSize=10&pageNumber=' + str(i) + '&reportName=RPT_MUTUAL_DEAL_HISTORY&columns=ALL&source=WEB&client=WEB&filter=(MUTUAL_TYPE%3D%22001%22)'
    res = requests.get(url, headers=headers)
    ren = res.text[42:-2]
    # print(ren)
    j = json.loads(ren)
    x = j['result']['data']
    for item in x:
        date = item['TRADE_DATE']  # '日期'
        n = item['FUND_INFLOW']  # '当日资金流入
        n2 = item['QUOTA_BALANCE']  # 当日余额
        n3 = item['ACCUM_DEAL_AMT']  # 历史资金累计流入'
        n4 = item['NET_DEAL_AMT']  # 当日成交净买入额'
        n5 = item['BUY_AMT']  # 买入成交额'
        n6 = item['SELL_AMT']  # 卖出成交额'
        n7 = item['INDEX_CLOSE_PRICE']  # 上证指数
        n8 = item['INDEX_CHANGE_RATE']  # 涨跌幅
        df = pd.DataFrame(dict(zip(columns, [date, n, n2, n3, n4, n5, n6, n7, n8])), index=[0])
        data = data._append(df, ignore_index=True)
# 百分比处理一下：
data.iloc[:, 1:7] = data.iloc[:, 1:7] / 100
print(data)
# 储存
data.to_csv('沪股通数据.csv', index=False)
# 深股通数据获取
columns = ['日期', '当日资金流入', '当日余额', '历史资金累计流入', '当日成交净买入额', '买入成交额', '卖出成交额', '深圳指数', '涨跌幅']
data2 = pd.DataFrame(columns=columns)

headers = {
    'Host': 'datacenter-web.eastmoney.com',
    'Referer': 'http://data.eastmoney.com/',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36'}

for i in range(1, 136):
    url = 'http://datacenter-web.eastmoney.com/api/data/v1/get?callback=jQuery112304911072279904296_1636170506777&sortColumns=TRADE_DATE&sortTypes=-1&pageSize=10&pageNumber=' + str(i) + '&reportName=RPT_MUTUAL_DEAL_HISTORY&columns=ALL&source=WEB&client=WEB&filter=(MUTUAL_TYPE%3D%22003%22)'
    res = requests.get(url, headers=headers)
    ren = res.text[42:-2]
    j = json.loads(ren)
    x = j['result']['data']
    for item in x:
        date = item['TRADE_DATE']
        n = item['FUND_INFLOW']
        n2 = item['QUOTA_BALANCE']
        n3 = item['ACCUM_DEAL_AMT']
        n4 = item['NET_DEAL_AMT']
        n5 = item['BUY_AMT']
        n6 = item['SELL_AMT']
        n7 = item['INDEX_CLOSE_PRICE']
        n8 = item['INDEX_CHANGE_RATE']
        df = pd.DataFrame(dict(zip(columns, [date, n, n2, n3, n4, n5, n6, n7, n8])), index=[0])
        data2 = data2._append(df, ignore_index=True)

# 同样处理一下百分比，统一数据口径。
data2.iloc[:, 1:7] = data2.iloc[:, 1:7] / 100
print(data2)
# 储存
data2.to_csv('深股通数据.csv', index=False)
# 数据预处理
# 先导入包，数据分析三剑客
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = 'SimHei'  # 显示中文
plt.rcParams['axes.unicode_minus'] = False  # 显示负号
# 读取数据
# 沪深300
hus300 = pd.read_csv('沪深300.csv', parse_dates=['date'])
print(hus300.head())
# 可以看到数据从2014-1月开始的，有每天的最高最低价，开盘收盘价。
# 沪股通数据
hgt = pd.read_csv('沪股通数据.csv', parse_dates=['日期'])
hgt = hgt.sort_values(by=['日期'])
print(hgt.head())
# 深股通数据
sgt = pd.read_csv('深股通数据.csv', parse_dates=['日期'])
sgt = sgt.sort_values(by=['日期'])
sgt.head()
# 数据合并
df = hus300.loc[:, ['date', 'close']].rename(columns={'date': '日期', 'close': '沪深300收盘价'})  # 取出日期和沪深300收盘价
df = (pd.merge(df, hgt.loc[:, ['日期', '当日成交净买入额']], how='left', left_on='日期', right_on='日期')
      .dropna().rename(columns={'当日成交净买入额': '沪股通净流入'}).reset_index(drop=True)  # 合并沪股通
      )
df = (pd.merge(df, sgt.loc[:, ['日期', '当日成交净买入额']], how='left', left_on='日期', right_on='日期')
      .rename(columns={'当日成交净买入额': '深股通净流入'}).reset_index(drop=True)  # 合并深股通
      .fillna(0).set_index('日期'))
print(df)
# 短期分析
# 短期我们要看评价1天后，3天后，5天后的涨跌幅。
# 计算如下：
df1 = (df.assign(北向资金总净流入=lambda df: df.沪股通净流入 + df.深股通净流入)
       .drop(columns=['沪股通净流入', '深股通净流入'])
       .assign(未来1日涨跌幅=lambda df: df['沪深300收盘价'].shift(-1) / df['沪深300收盘价'] - 1)
       .assign(未来3日涨跌幅=lambda df: df['沪深300收盘价'].shift(-3) / df['沪深300收盘价'] - 1)
       .assign(未来5日涨跌幅=lambda df: df['沪深300收盘价'].shift(-5) / df['沪深300收盘价'] - 1)
       .dropna()
       )
print(df1)
# 新建一个数据框，计算要显示的结果的数据：
# flow代表北向资金的净流入，我选择了[0,5,10,20,30,50,80,100]这几个阈值作为分析对象。
result = pd.DataFrame()
for flow in [0, 5, 10, 20, 30, 50, 80, 100]:
    t_df = df1[df1['北向资金总净流入'] > flow]
    result.loc[flow, '出现次数'] = t_df.shape[0]

    for i in [1, 3, 5]:
        result.loc[flow, f'未来{i}日上涨次数'] = t_df[t_df[f'未来{i}日涨跌幅'] > 0].shape[0]
        result.loc[flow, f'未来{i}日平均涨幅'] = t_df[f'未来{i}日涨跌幅'].mean()
# 计算上涨概率：
result['未来1日上涨概率'] = result['未来1日上涨次数'] / result['出现次数']
result['未来3日上涨概率'] = result['未来3日上涨次数'] / result['出现次数']
result['未来5日上涨概率'] = result['未来5日上涨次数'] / result['出现次数']
# 结果可视化
data = (result.reindex(columns=['出现次数', '未来1日上涨次数', '未来1日上涨概率', '未来1日平均涨幅', '未来3日上涨次数',
                                '未来3日上涨概率', '未来3日平均涨幅', '未来5日上涨次数', '未来5日上涨概率', '未来5日平均涨幅'])
        .rename_axis("资金流入阈值")  # 索引重命名
        .reset_index()
        .style.bar(color='#5CADAD', subset=['未来1日上涨概率', '未来3日上涨概率', '未来5日上涨概率'], vmin=0.4, vmax=0.6)
        .bar(color='violet', subset=['未来1日平均涨幅', '未来3日平均涨幅', '未来5日平均涨幅'], vmin=0.000, vmax=0.006)

        .format({'出现次数': "{:.0f}", '未来1日上涨次数': "{:.0f}", '未来3日上涨次数': "{:.0f}", '未来5日上涨次数': "{:.0f}"})
        .format({'未来1日上涨概率': "{:.2%}", '未来3日上涨概率': "{:.2%}", '未来5日上涨概率': "{:.2%}"})
        .format({'未来1日平均涨幅': "{:.3%}", '未来3日平均涨幅': "{:.3%}", '未来5日平均涨幅': "{:.3%}"})
        .format({'资金流入阈值': '>{:.0f}'})
        )
print(data)
# 结果存为excel表
data.to_excel('北向资金结果.xlsx', index=False)
# 结果分析
# 从上面的迷你条形图可以看到，在北向资金流入的阈值为正数的情况下，基本在后面的1天，3天，5
# 天都是有较大的概率上涨的，而且平均收益都为正数。其实算是一个很有效的策略了。
#
# 需要说明的是流入阈值大于100
# 的时候，在A股历史上也只出现过42次，未来一天的上涨概率不算很大。我能想到的解释是北向资金的大幅流入都是市场恐慌的时候，市场恐慌的时候砸盘很严重，但是也是北向资金最为贪婪的时候，它们会买入很多筹码，在市场还未见底的情况左侧低吸，虽然未来一两天市场还是会继续跌，但是这也方便买入了更多的筹码。这进一步说明了北向资金的‘’预见性‘’能力。
# 长期分析
# 思路和前面差不多，只不过计算的是10天后，30天后，60天后的平均涨跌幅。
df1 = (df.assign(北向资金总净流入=lambda df: df.沪股通净流入 + df.深股通净流入)
       .drop(columns=['沪股通净流入', '深股通净流入'])
       .assign(未来10日涨跌幅=lambda df: df['沪深300收盘价'].shift(-10) / df['沪深300收盘价'] - 1)
       .assign(未来30日涨跌幅=lambda df: df['沪深300收盘价'].shift(-30) / df['沪深300收盘价'] - 1)
       .assign(未来60日涨跌幅=lambda df: df['沪深300收盘价'].shift(-60) / df['沪深300收盘价'] - 1)
       .dropna()
       )
print(df1)
result = pd.DataFrame()
for flow in [0, 5, 10, 20, 30, 50, 80, 100]:
    t_df = df1[df1['北向资金总净流入'] > flow]
    result.loc[flow, '出现次数'] = t_df.shape[0]

    for i in [10, 30, 60]:
        result.loc[flow, f'未来{i}日上涨次数'] = t_df[t_df[f'未来{i}日涨跌幅'] > 0].shape[0]
        result.loc[flow, f'未来{i}日平均涨幅'] = t_df[f'未来{i}日涨跌幅'].mean()
result['未来10日上涨概率'] = result['未来10日上涨次数'] / result['出现次数']
result['未来30日上涨概率'] = result['未来30日上涨次数'] / result['出现次数']
result['未来60日上涨概率'] = result['未来60日上涨次数'] / result['出现次数']
data = (result.reindex(columns=['出现次数', '未来10日上涨次数', '未来10日上涨概率', '未来10日平均涨幅', '未来30日上涨次数',
                                '未来30日上涨概率', '未来30日平均涨幅', '未来60日上涨次数', '未来60日上涨概率', '未来60日平均涨幅'])
        .rename_axis("资金流入阈值")  # 索引重命名
        .reset_index()
        .style.bar(color='#5CADAD', subset=['未来10日上涨概率', '未来30日上涨概率', '未来60日上涨概率'], vmin=0.4, vmax=0.6)
        .bar(color='violet', subset=['未来10日平均涨幅', '未来30日平均涨幅', '未来60日平均涨幅'], vmin=0.004, vmax=0.02)

        .format({'出现次数': "{:.0f}", '未来10日上涨次数': "{:.0f}", '未来30日上涨次数': "{:.0f}", '未来60日上涨次数': "{:.0f}"})
        .format({'未来10日上涨概率': "{:.2%}", '未来30日上涨概率': "{:.2%}", '未来60日上涨概率': "{:.2%}"})
        .format({'未来10日平均涨幅': "{:.3%}", '未来30日平均涨幅': "{:.3%}", '未来60日平均涨幅': "{:.3%}"})
        .format({'资金流入阈值': '>{:.0f}'})
        )
print(data)
