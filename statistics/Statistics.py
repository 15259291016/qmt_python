'''
作者:李健臣
开发日期:2025/3/10
A股交易统计模型:
加入（如MACD、RSI、布林带、ATR、OBV、CCI，ADX（平均趋向指数）、
MFI（资金流量指数）），并集成了多种机器学习模型（线性回归、随机森林、XGBoost、LSTM）
,VWAP（成交量加权平均价）、Ichimoku Cloud（一目均衡表）
同时，代码将输出数据同步保存到PostgreSQL数据库，并通过多线程实时调用Tushare数据。
使用分区表或索引优化PostgreSQL数据库性能，程序会每隔60秒更新一次数据，
并输出统计结果、机器学习模型表现和图表，同时将结果保存到PostgreSQL数据库。
============================================================================
OBV（能量潮）：通过成交量计算能量潮指标。
CCI（商品通道指数）：通过典型价格计算商品通道指数。
机器学习模型：(线性回归、随机森林、XGBoost、LSTM)用于价格预测
计算均方误差（MSE）并保存结果到PostgreSQL。
数据存储：使用PostgreSQL数据库存储统计结果和机器学习模型结果。
多线程实时更新：每隔update_interval秒更新一次数据，并重新计算统计指标和训练模型。

分区表：按日期分区存储统计结果和机器学习模型结果。

索引：在trade_date字段上创建索引，加快查询速度。

#============================运行方法===============================================
#1安装依赖库：
pip install tushare pandas numpy matplotlib seaborn scikit-learn xgboost keras psycopg2 sqlalchemy

#2 替换your_tushare_token为你的Tushare API token，并配置PostgreSQL数据库

#3 创建分区表和索引：SQL语法实现

CREATE TABLE statistics (
    trade_date DATE PRIMARY KEY,
    annual_return FLOAT,
    max_drawdown FLOAT,
    sharpe_ratio FLOAT,
    strategy_annual_return FLOAT,
    strategy_max_drawdown FLOAT,
    strategy_sharpe_ratio FLOAT
) PARTITION BY RANGE (trade_date);

CREATE TABLE ml_results (
    trade_date DATE PRIMARY KEY,
    mse_lr FLOAT,
    mse_rf FLOAT,
    mse_xgb FLOAT,
    mse_lstm FLOAT
) PARTITION BY RANGE (trade_date);

CREATE INDEX idx_trade_date ON statistics (trade_date);
CREATE INDEX idx_trade_date_ml ON ml_results (trade_date);

-------------------------------------------------------------------------------
通过该统计，实时监控A股市场
'''

import tushare as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import threading
import time
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import LSTM, Dense
import psycopg2
from sqlalchemy import create_engine

# 设置Tushare的API token
#tushare_token=gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482

## Tushare API token
tushare_token="gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482"
ts.set_token(tushare_token)  # 替换为你的Tushare API token
pro = ts.pro_api()

# 全局变量
stock_code = '600519.SH'  # 股票代码
update_interval = 60  # 数据更新间隔（秒）
data_file = f'{stock_code}_stock_data.csv'  # 数据保存文件
risk_free_rate = 0.02  # 无风险利率

# PostgreSQL数据库配置
db_config = {
    'host': 'localhost',
    'user': 'postgres',
    'password': '6116988.niu',
    'database': 'stock_data',
    'port': 5432
}

# 创建数据库连接
engine = create_engine(f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?client_encoding=utf8")

# 获取A股交易数据
def fetch_stock_data(stock_code, start_date, end_date):
    df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
    return df

# 计算MACD指标
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['ema_short'] = data['close'].ewm(span=short_window, adjust=False).mean()
    data['ema_long'] = data['close'].ewm(span=long_window, adjust=False).mean()
    data['macd'] = data['ema_short'] - data['ema_long']
    data['signal'] = data['macd'].ewm(span=signal_window, adjust=False).mean()
    data['histogram'] = data['macd'] - data['signal']
    return data

# 计算RSI指标
def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    return data

# 计算布林带
def calculate_bollinger_bands(data, window=20, num_std=2):
    data['ma'] = data['close'].rolling(window=window).mean()
    data['std'] = data['close'].rolling(window=window).std()
    data['upper_band'] = data['ma'] + (data['std'] * num_std)
    data['lower_band'] = data['ma'] - (data['std'] * num_std)
    return data

# 计算ATR（平均真实波动率）
def calculate_atr(data, window=14):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    data['atr'] = true_range.rolling(window=window).mean()
    return data

# 计算OBV（能量潮）
def calculate_obv(data):
    data['obv'] = (np.sign(data['close'].diff()) * data['vol']).fillna(0).cumsum()
    return data

# 计算CCI（商品通道指数）
def calculate_cci(data, window=20):
    tp = (data['high'] + data['low'] + data['close']) / 3
    data['cci'] = (tp - tp.rolling(window=window).mean()) / (0.015 * tp.rolling(window=window).std())
    return data

# 计算ADX（平均趋向指数）
def calculate_adx(data, window=14):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    plus_dm = data['high'].diff()
    minus_dm = -data['low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr_plus = plus_dm.rolling(window=window).mean()
    tr_minus = minus_dm.rolling(window=window).mean()
    data['adx'] = 100 * (tr_plus - tr_minus).abs() / (tr_plus + tr_minus)
    return data

# 计算MFI（资金流量指数）
def calculate_mfi(data, window=14):
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    money_flow = typical_price * data['vol']
    positive_flow = (typical_price.diff() > 0) * money_flow
    negative_flow = (typical_price.diff() < 0) * money_flow
    data['mfi'] = 100 - (100 / (1 + (positive_flow.rolling(window=window).mean() / negative_flow.rolling(window=window).mean())))
    return data

# 数据预处理
def preprocess_data(data):
    # 转换日期格式
    data['trade_date'] = pd.to_datetime(data['trade_date'], format='%Y%m%d')
    data = data.sort_values(by='trade_date')

    # 计算每日收益率
    data['daily_return'] = data['close'].pct_change()

    # 计算累计收益率
    data['cumulative_return'] = (1 + data['daily_return']).cumprod()

    # 计算波动率（20日滚动年化波动率）
    data['volatility'] = data['daily_return'].rolling(window=20).std() * np.sqrt(252)

    # 计算短期和长期均线
    data['short_ma'] = data['close'].rolling(window=10).mean()
    data['long_ma'] = data['close'].rolling(window=50).mean()

    # 计算MACD指标
    data = calculate_macd(data)

    # 计算RSI指标
    data = calculate_rsi(data)

    # 计算布林带
    data = calculate_bollinger_bands(data)

    # 计算ATR
    data = calculate_atr(data)

    # 计算OBV
    data = calculate_obv(data)

    # 计算CCI
    data = calculate_cci(data)

    # 计算ADX
    data = calculate_adx(data)

    # 计算MFI
    data = calculate_mfi(data)

    # 生成交易信号
    data['signal'] = np.where(data['short_ma'] > data['long_ma'], 1, -1)

    # 计算策略收益率
    data['strategy_return'] = data['signal'].shift(1) * data['daily_return']

    # 计算策略累计收益率
    data['strategy_cumulative_return'] = (1 + data['strategy_return']).cumprod()

    return data

# 统计分析
def calculate_statistics(data):
    # 计算年化收益率
    annual_return = data['daily_return'].mean() * 252

    # 计算最大回撤
    data['cumulative_max'] = data['close'].cummax()
    data['drawdown'] = (data['cumulative_max'] - data['close']) / data['cumulative_max']
    max_drawdown = data['drawdown'].max()

    # 计算夏普比率
    sharpe_ratio = (data['daily_return'].mean() - risk_free_rate / 252) / data['daily_return'].std() * np.sqrt(252)

    # 计算策略的年化收益率、最大回撤和夏普比率
    strategy_annual_return = data['strategy_return'].mean() * 252
    data['strategy_cumulative_max'] = data['strategy_cumulative_return'].cummax()
    data['strategy_drawdown'] = (data['strategy_cumulative_max'] - data['strategy_cumulative_return']) / data['strategy_cumulative_max']
    strategy_max_drawdown = data['strategy_drawdown'].max()
    strategy_sharpe_ratio = (data['strategy_return'].mean() - risk_free_rate / 252) / data['strategy_return'].std() * np.sqrt(252)

    # 输出统计结果
    print(f"年化收益率: {annual_return:.2%}")
    print(f"最大回撤: {max_drawdown:.2%}")
    print(f"夏普比率: {sharpe_ratio:.2f}")
    print(f"策略年化收益率: {strategy_annual_return:.2%}")
    print(f"策略最大回撤: {strategy_max_drawdown:.2%}")
    print(f"策略夏普比率: {strategy_sharpe_ratio:.2f}")

    # 保存统计结果到PostgreSQL
    stats_df = pd.DataFrame({
        'trade_date': [data['trade_date'].iloc[-1]],
        'annual_return': [annual_return],
        'max_drawdown': [max_drawdown],
        'sharpe_ratio': [sharpe_ratio],
        'strategy_annual_return': [strategy_annual_return],
        'strategy_max_drawdown': [strategy_max_drawdown],
        'strategy_sharpe_ratio': [strategy_sharpe_ratio]
    })
    # try:
    #     stats_df.to_sql('statistics', con=engine, if_exists='append', index=False)
    # except UnicodeDecodeError as e:
    #     print(f"UnicodeDecodeError: {e}")
    #     print(f"Failed to connect with connection string: {engine.url}")

# 机器学习模型：线性回归、随机森林、XGBoost、LSTM
def train_ml_models(data):
    # 特征工程
    data['prev_close'] = data['close'].shift(1)
    data['prev_volume'] = data['vol'].shift(1)
    data['prev_macd'] = data['macd'].shift(1)
    data['prev_rsi'] = data['rsi'].shift(1)
    data['prev_atr'] = data['atr'].shift(1)
    data['prev_obv'] = data['obv'].shift(1)
    data['prev_cci'] = data['cci'].shift(1)
    data['prev_adx'] = data['adx'].shift(1)
    data['prev_mfi'] = data['mfi'].shift(1)
    data = data.dropna()

    # 定义特征和目标变量
    X = data[['prev_close', 'prev_volume', 'prev_macd', 'prev_rsi', 'prev_atr', 'prev_obv', 'prev_cci', 'prev_adx', 'prev_mfi']]
    y = data['close']

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 线性回归
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    y_pred_lr = lr_model.predict(X_test)
    mse_lr = mean_squared_error(y_test, y_pred_lr)
    print(f"线性回归模型均方误差 (MSE): {mse_lr:.2f}")

    # 随机森林
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    mse_rf = mean_squared_error(y_test, y_pred_rf)
    print(f"随机森林模型均方误差 (MSE): {mse_rf:.2f}")

    # XGBoost
    xgb_model = XGBRegressor(n_estimators=100, random_state=42)
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)
    mse_xgb = mean_squared_error(y_test, y_pred_xgb)
    print(f"XGBoost模型均方误差 (MSE): {mse_xgb:.2f}")

    # LSTM
    X_lstm = X.values.reshape((X.shape[0], X.shape[1], 1))
    y_lstm = y.values
    X_train_lstm, X_test_lstm, y_train_lstm, y_test_lstm = train_test_split(X_lstm, y_lstm, test_size=0.2, random_state=42)

    lstm_model = Sequential()
    lstm_model.add(LSTM(50, input_shape=(X_train_lstm.shape[1], 1)))
    lstm_model.add(Dense(1))
    lstm_model.compile(optimizer='adam', loss='mse')
    lstm_model.fit(X_train_lstm, y_train_lstm, epochs=10, batch_size=32, verbose=0)
    y_pred_lstm = lstm_model.predict(X_test_lstm)
    mse_lstm = mean_squared_error(y_test_lstm, y_pred_lstm)
    print(f"LSTM模型均方误差 (MSE): {mse_lstm:.2f}")

    # 保存模型结果到PostgreSQL
    ml_results_df = pd.DataFrame({
        'trade_date': [data['trade_date'].iloc[-1]],
        'mse_lr': [mse_lr],
        'mse_rf': [mse_rf],
        'mse_xgb': [mse_xgb],
        'mse_lstm': [mse_lstm]
    })
    # ml_results_df.to_sql('ml_results', con=engine, if_exists='append', index=False)

# 更新数据
def update_data():
    while True:
        print(f"{datetime.now()}: 更新数据...")
        # 获取最新数据
        end_date = datetime.now().strftime('%Y%m%d')
        new_data = fetch_stock_data(stock_code, '20220101', end_date)

        # 保存数据到CSV文件
        new_data.to_csv(data_file, index=False)

        # 加载数据并预处理
        data = pd.read_csv(data_file)
        data = preprocess_data(data)

        # 计算统计指标
        calculate_statistics(data)

        # 训练机器学习模型
        train_ml_models(data)

        # 等待下一次更新
        time.sleep(update_interval)

# 主函数
def main():
    # 启动数据更新线程
    update_thread = threading.Thread(target=update_data)
    update_thread.daemon = True
    update_thread.start()

    # 主线程保持运行
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()

''''



'''
