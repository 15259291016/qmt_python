import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tushare as ts

# 设置 Tushare Pro API 密钥
ts.set_token('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')
pro = ts.pro_api()

def get_stock_data(stock_code, start_date, end_date):
    """
    获取股票日行情数据
    :param stock_code: 股票代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 股票日行情数据 DataFrame
    """
    df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.sort_values('trade_date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def calculate_keltner_channels(df, period=20, multiplier=2):
    """
    计算金肯特纳线
    :param df: 股票数据 DataFrame
    :param period: 移动平均窗口大小
    :param multiplier: 倍数因子
    :return: 包含金肯特纳线的 DataFrame
    """
    # 计算典型价格
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3

    # 计算移动平均线
    df['ema'] = df['typical_price'].ewm(span=period, adjust=False).mean()

    # 计算真实范围 (TR)
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = np.abs(df['high'] - df['close'].shift())
    df['low_close'] = np.abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)

    # 计算平均真实范围 (ATR)
    df['atr'] = df['tr'].ewm(span=period, adjust=False).mean()

    # 计算金肯特纳线上轨和下轨
    df['upper_band'] = df['ema'] + multiplier * df['atr']
    df['lower_band'] = df['ema'] - multiplier * df['atr']

    return df

def generate_signals(df):
    """
    生成交易信号
    :param df: 包含金肯特纳线的 DataFrame
    :return: 包含交易信号的 DataFrame
    """
    # 初始化信号列
    df['signal'] = 0

    # 生成买入信号
    df.loc[df['close'] < df['lower_band'], 'signal'] = 1

    # 生成卖出信号
    df.loc[df['close'] > df['upper_band'], 'signal'] = -1

    # 删除多余的列
    df.drop(columns=['high_low', 'high_close', 'low_close', 'tr', 'typical_price'], inplace=True)

    return df

def plot_keltner_channels(df, stock_name):
    """
    绘制金肯特纳线和交易信号
    :param df: 包含金肯特纳线和信号的 DataFrame
    :param stock_name: 股票名称
    """
    plt.figure(figsize=(14, 7))
    plt.plot(df['trade_date'], df['close'], label='Close Price', color='blue')
    plt.plot(df['trade_date'], df['upper_band'], label='Upper Band', color='red', linestyle='--')
    plt.plot(df['trade_date'], df['ema'], label='EMA', color='green')
    plt.plot(df['trade_date'], df['lower_band'], label='Lower Band', color='red', linestyle='--')

    # 标记买入和卖出信号
    buy_signals = df[df['signal'] == 1]
    sell_signals = df[df['signal'] == -1]

    plt.scatter(buy_signals['trade_date'], buy_signals['close'], label='Buy Signal', marker='^', color='green', alpha=1)
    plt.scatter(sell_signals['trade_date'], sell_signals['close'], label='user_strategy Signal', marker='v', color='red', alpha=1)

    plt.title(f'Keltner Channels for {stock_name}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

def keltner_channels_strategy(stock_code, start_date, end_date, period=20, multiplier=2):
    """
    金肯特纳交易系统策略
    :param stock_code: 股票代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param period: 移动平均窗口大小
    :param multiplier: 倍数因子
    """
    # 获取股票数据
    df = get_stock_data(stock_code, start_date, end_date)

    # 计算金肯特纳线
    df = calculate_keltner_channels(df, period, multiplier)

    # 生成交易信号
    df = generate_signals(df)

    # 绘制图表
    stock_name = stock_code.split('.')[0]
    plot_keltner_channels(df, stock_name)

# 示例调用
keltner_channels_strategy('algo/tactics/000001.csv', '20240101', '20250101', period=20, multiplier=2)
