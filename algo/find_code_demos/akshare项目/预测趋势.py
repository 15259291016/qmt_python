# # https://cloud.tencent.com/developer/article/1838621
# 一段时间内股票价格的变化是多少?
# 股票的平均日回报率是多少?
# 各种股票的移动平均线是多少?
# 不同股票之间的相关性是什么?
# 我们投资某只股票的风险是多少?
# 我们如何预测未来的股票行为呢?(使用LSTM预测贵州茅台的收盘价)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
plt.style.use("fivethirtyeight")
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# %matplotlib inline
from datetime import datetime
from akshare import stock_zh_a_hist


def get_data(code):
    end = datetime.now()
    start = datetime(end.year - 1, end.month, end.day).strftime('%Y-%m-%d').replace('-', '')
    end = end.strftime('%Y-%m-%d').replace('-', '')
    # 登陆系统
    stock = stock_zh_a_hist(symbol=code.split('.')[1], period="daily", start_date=start, end_date=end, adjust="")

    # 对列进行重新排序设置成OHLC
    stock_history = stock[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
    # 设置以日期为索引
    # stock_history['日期'] = stock_history['日期'].map(lambda x: datetime.strptime(x, '%Y-%m-%d'))
    _res = stock_history.set_index('日期')
    res = _res.applymap(lambda x: float(x))
    return res


liquor_list = ['sh.600519', 'sz.000858',
               'sz.002304', 'sh.600809']
# 贵州茅台，五粮液， 洋河股份，山西汾酒
company_data = {'maotai': None,
                'wuliangye': None,
                'yanghe': None,
                'fenjiu': None}
company_name = ['maotai', 'wuliangye', 'yanghe', 'fenjiu']
for name, code in zip(company_name, liquor_list):
    company_data[name] = get_data(code)

# 需要批量赋值的变量名称
# company_list = ['maotai','wuliangye','yanghe','fenjiu']
# for company, com_name in zip(company_list, company_name):
#     company["company_name"] = com_name
# 将四支股票数据进行纵向合并
df = pd.concat(company_data, axis=0)
df.tail(10)

# plt.figure(figsize=(15, 6))
# plt.subplots_adjust(top=1.25, bottom=1.2)
for i, company in enumerate(company_data, 1):
    plt.subplot(2, 2, i)
    company_data[company]['收盘'].plot()
    plt.ylabel('收盘')
    plt.xlabel(None)
    plt.title(f"Closing Price of {company_name[i - 1]}")
plt.tight_layout()
# plt.show()

plt.figure(figsize=(15, 7))
plt.subplots_adjust(top=1.25, bottom=1.2)
for i, company in enumerate(company_data, 1):
    plt.subplot(2, 2, i)
    company_data[company]['成交量'].plot()
    plt.ylabel('成交量')
    plt.xlabel(None)
    plt.title(f"Sales Volume for {company_name[i - 1]}")
plt.tight_layout()
# plt.show()
# 设置移动天数
ma_day = [10, 20, 50]
for ma in ma_day:
    for company in company_data:
        column_name = f"MA for {ma} days"
        company_data[company][column_name] = company_data[company]['收盘'].rolling(ma).mean()

fig, axes = plt.subplots(nrows=2, ncols=2)
fig.set_figheight(8)
fig.set_figwidth(15)
company_data['maotai'][['收盘', 'MA for 10 days', 'MA for 20 days', 'MA for 50 days']].plot(ax=axes[0, 0])
axes[0, 0].set_title('贵州茅台')

company_data['wuliangye'][['收盘', 'MA for 10 days', 'MA for 20 days', 'MA for 50 days']].plot(ax=axes[0, 1])
axes[0, 1].set_title('五粮液')

company_data['yanghe'][['收盘', 'MA for 10 days', 'MA for 20 days', 'MA for 50 days']].plot(ax=axes[1, 0])
axes[1, 0].set_title('洋河股份')

company_data['fenjiu'][['收盘', 'MA for 10 days', 'MA for 20 days', 'MA for 50 days']].plot(ax=axes[1, 1])
axes[1, 1].set_title('山西汾酒')
fig.tight_layout()

for company in company_data:
    company_data[company]['Daily Return'] = company_data[company]['收盘'].pct_change()
# 画出日收益率
fig, axes = plt.subplots(nrows=2, ncols=2)
fig.set_figheight(8)
fig.set_figwidth(15)
company_data['maotai']['Daily Return'].plot(ax=axes[0, 0], legend=True, linestyle='--', marker='o')
axes[0, 0].set_title('贵州茅台')
company_data['wuliangye']['Daily Return'].plot(ax=axes[0, 1], legend=True, linestyle='--', marker='o')
axes[0, 1].set_title('五粮液')
company_data['yanghe']['Daily Return'].plot(ax=axes[1, 0], legend=True, linestyle='--', marker='o')
axes[1, 0].set_title('洋河股份')
company_data['fenjiu']['Daily Return'].plot(ax=axes[1, 1], legend=True, linestyle='--', marker='o')
axes[1, 1].set_title('山西汾酒')
fig.tight_layout()

# 注意这里使用了dropna()，否则seaborn无法读取NaN值
plt.figure(figsize=(12, 7))
company_name_c = ['贵州茅台', '五粮液', '洋河股份', '山西汾酒']
for i, company in enumerate(company_data, 1):
    plt.subplot(2, 2, i)
    sns.distplot(company_data[company]['Daily Return'].dropna(), bins=100, color='purple')
    plt.ylabel('Daily Return')
    plt.title(f'{company_name_c[i - 1]}')
# 也可以这样绘制
# maotai['Daily Return'].hist()
plt.tight_layout()

index = company_data['maotai'].index
closing_df = pd.DataFrame()
for company, company_n in zip(company_data, company_name_c):
    temp_df = pd.DataFrame(index=company_data[company].index, data=company_data[company]['收盘'].values, columns=[company_n])
    closing_df = pd.concat([closing_df, temp_df], axis=1)
# 看看数据
# closing_df.head()
#
# liquor_rets = closing_df.pct_change()
# liquor_rets.head()
#
# # sns.jointplot('maotai', 'maotai',
# #               tech_rets, kind='scatter',
# #               color='seagreen')
#
# sns.jointplot('贵州茅台', '五粮液',
#               liquor_rets, kind='scatter')
#
# sns.pairplot(liquor_rets, kind='reg')
#
# # 通过命名为returns_fig来设置我们的图形，
# # 在DataFrame上调用PairPLot
# return_fig = sns.PairGrid(liquor_rets.dropna())
# # 使用map_upper，我们可以指定上面的三角形是什么样的。
# return_fig.map_upper(plt.scatter, color='purple')
# # 我们还可以定义图中较低的三角形，
# # 包括绘图类型(kde)或颜色映射(blueppurple)
# return_fig.map_lower(sns.kdeplot, cmap='cool_d')
# # 最后，我们将把对角线定义为每日收益的一系列直方图
# return_fig.map_diag(plt.hist, bins=30)
#
# returns_fig = sns.PairGrid(closing_df)
# returns_fig.map_upper(plt.scatter, color='purple')
# returns_fig.map_lower(sns.kdeplot, cmap='cool_d')
# returns_fig.map_diag(plt.hist, bins=30)
#
# # 让我们用sebron来做一个每日收益的快速相关图
# sns.heatmap(liquor_rets.corr(),
#             annot=True, cmap='summer')
#
# sns.heatmap(closing_df.corr(),
#             annot=True, cmap='summer')
#
# # 让我们首先将一个新的DataFrame定义为原始liquor_rets的 DataFrame的压缩版本
# rets = liquor_rets.dropna()
# area = np.pi * 20
# plt.figure(figsize=(10, 7))
# plt.scatter(rets.mean(), rets.std(), s=area)
# plt.xlabel('预期回报', fontsize=18)
# plt.ylabel('风险', fontsize=18)
#
# for label, x, y in zip(rets.columns, rets.mean(), rets.std()):
#     if label == '山西汾酒':
#         xytext = (-50, -50)
#     else:
#         xytext = (50, 50)
#     plt.annotate(label, xy=(x, y), xytext=xytext,
#                  textcoords='offset points',
#                  ha='right', va='bottom', fontsize=15,
#                  arrowprops=dict(arrowstyle='->',
#                                  color='gray',
#                                  connectionstyle='arc3,rad=-0.3'))

# 获取股票报价
df = company_data['maotai'].loc[:, ['开盘', '最高', '最低', '收盘', '成交量']]
df.head()

plt.figure(figsize=(16, 6))
plt.title('历史收盘价', fontsize=20)
plt.plot(df['开盘'])
plt.xlabel('日期', fontsize=18)
plt.ylabel('收盘价 RMB (¥)', fontsize=18)
plt.show()

# 创建一个只有收盘价的新数据帧
data = df.filter(['收盘'])
# 将数据帧转换为numpy数组
dataset = data.values
# 获取要对模型进行训练的行数
training_data_len = int(np.ceil(len(dataset) * .95))
# 数据标准化
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)
# 创建训练集，训练标准化训练集
train_data = scaled_data[0:int(training_data_len), :]
# 将数据拆分为x_train和y_train数据集
x_train = []
y_train = []
for i in range(60, len(train_data)):
    x_train.append(train_data[i - 60:i, 0])
    y_train.append(train_data[i, 0])
    if i <= 61:
        print(x_train)
        print(y_train)
# 将x_train和y_train转换为numpy数组
x_train, y_train = np.array(x_train), np.array(y_train)
# Reshape数据
x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

# pip install keras

from keras.models import Sequential
from keras.layers import Dense, LSTM

# 建立LSTM模型
model = Sequential()
model.add(LSTM(128, return_sequences=True, input_shape=(x_train.shape[1], 1)))
model.add(LSTM(64, return_sequences=False))
model.add(Dense(25))
model.add(Dense(1))
# 编译模型
model.compile(optimizer='adam', loss='mean_squared_error')
# 训练模型
model.fit(x_train, y_train, batch_size=1, epochs=10)

# 创建测试数据集
# 创建一个新的数组，包含从索引的缩放值
test_data = scaled_data[training_data_len - 60:, :]
# 创建数据集x_test和y_test
x_test = []
y_test = dataset[training_data_len:, :]
for i in range(60, len(test_data)):
    x_test.append(test_data[i - 60:i, 0])
# 将数据转换为numpy数组
x_test = np.array(x_test)
# 重塑的数据
x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))
# 得到模型的预测值
predictions = model.predict(x_test)
predictions = scaler.inverse_transform(predictions)
# 得到均方根误差(RMSE)
rmse = np.sqrt(np.mean(((predictions - y_test) ** 2)))

train = data[:training_data_len]
valid = data[training_data_len:]
valid['Predictions'] = predictions
plt.figure(figsize=(16, 6))
plt.title('models')
plt.xlabel('date', fontsize=18)
plt.ylabel('close price RMB (¥)', fontsize=18)
plt.plot(train['收盘'])
plt.plot(valid[['收盘', 'Predictions']])
plt.legend(['train price', 'true price', 'predict price'], loc='upper left')
plt.show()
print(valid)
