import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_stock_data(file_path):
    """
    加载股票价格数据
    :param file_path: 数据文件路径
    :return: 股票数据 DataFrame
    """
    df = pd.read_csv(file_path)
    df['日期'] = pd.to_datetime(df['日期'])
    df.set_index('日期', inplace=True)
    return df

def calculate_moving_averages(df, periods=[5, 10, 20]):
    """
    计算均线
    :param df: 股票数据 DataFrame
    :param periods: 均线周期列表
    :return: 包含均线数据的 DataFrame
    """
    for period in periods:
        df[f'MA{period}'] = df['收盘'].rolling(window=period, min_periods=1).mean()
    return df

def calculate_slope(series, periods=5):
    """
    计算均线斜率
    :param series: 均线数据 Series
    :param periods: 斜率计算周期
    :return: 均线斜率 Series
    """
    slope = series.diff(periods=periods) / periods
    return slope

def generate_signals(df, periods=[5, 10, 20], slope_periods=5):
    """
    生成交易信号
    :param df: 包含均线数据的 DataFrame
    :param periods: 均线周期列表
    :param slope_periods: 斜率计算周期
    :return: 包含交易信号的 DataFrame
    """
    # 计算均线和斜率
    df = calculate_moving_averages(df, periods)
    for ma in [f'MA{p}' for p in periods]:
        df[f'{ma}_slope'] = calculate_slope(df[ma], periods=slope_periods)

    # 判断均线排列状态
    df['ma_rank'] = np.nan
    for i in range(len(df)):
        current_moving_averages = [df.loc[df.index[i], f'MA{p}'] for p in periods]
        current_moving_averages = [ma for ma in current_moving_averages if not np.isnan(ma)]
        sorted_moving_averages = sorted(current_moving_averages)

        # 多头排列：MA5 > MA10 > MA20
        if current_moving_averages == sorted(current_moving_averages, reverse=True):
            df.loc[df.index[i], 'ma_rank'] = 1
        # 空头排列：MA5 < MA10 < MA20
        elif current_moving_averages == sorted(current_moving_averages):
            df.loc[df.index[i], 'ma_rank'] = -1
        else:
            df.loc[df.index[i], 'ma_rank'] = 0

    # 生成交易信号
    df['signal'] = 0  # 初始化信号列
    for i in range(len(df)):
        if df.loc[df.index[i], 'ma_rank'] == 1 and df.loc[df.index[i], f'MA{periods[0]}_slope'] > 0:
            df.loc[df.index[i], 'signal'] = 1  # 买入信号
        elif df.loc[df.index[i], 'ma_rank'] == -1 and df.loc[df.index[i], f'MA{periods[0]}_slope'] < 0:
            df.loc[df.index[i], 'signal'] = -1  # 卖出信号

    return df

def calculate_volume(df, periods=20):
    """
    计算均线期数内的平均成交量
    :param df: 股票数据 DataFrame
    :param periods: 期数
    :return: 包含平均成交量的 DataFrame
    """
    df['avg_volume'] = df['成交量'].rolling(window=periods, min_periods=1).mean()
    return df

def recommend_stocks(df):
    """
    生成荐股信号
    :param df: 包含交易信号和均线数据的 DataFrame
    :return: 股票荐股信号 DataFrame
    """
    df['recommend'] = ''

    for i in range(len(df)):
        if df.loc[df.index[i], 'signal'] == 1:
            df.loc[df.index[i], 'recommend'] = 'BUY'
        elif df.loc[df.index[i], 'signal'] == -1:
            df.loc[df.index[i], 'recommend'] = 'SELL'
        else:
            df.loc[df.index[i], 'recommend'] = '-'

    return df

def plot_signals(df, stock_name, periods=[5, 10, 20]):
    """
    绘制股票价格和均线，以及交易信号
    :param df: 包含均线数据和信号的 DataFrame
    :param stock_name: 股票名称
    :param periods: 均线周期列表
    """
    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df['收盘'], label='Close Price', color='blue')

    # 绘制均线
    for period in periods:
        plt.plot(df.index, df[f'MA{period}'], label=f'MA{period}')

    # 绘制交易信号
    buy_signals = df[df['recommend'] == 'BUY']
    sell_signals = df[df['recommend'] == 'SELL']

    plt.scatter(buy_signals.index, buy_signals['收盘'], label='Buy Signal', marker='^', color='green', alpha=1)
    plt.scatter(sell_signals.index, sell_signals['收盘'], label='user_strategy Signal', marker='v', color='red', alpha=1)

    plt.title(f'Moving Average Strategy for {stock_name}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

def calculate_stock_returns(df):
    """
    计算股票收益
    :param df: 股票数据 DataFrame
    :return: 包含股票收益的 DataFrame
    """
    df['return'] = df['收盘'].pct_change()
    df['strategy_return'] = df['return'] * df['signal'].shift(1)
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod()
    return df

def mean_reversion_strategy(data_file):
    """
    均线排列交易系统策略
    :param data_file: 数据文件路径
    """
    # 加载数据
    df = load_stock_data(data_file)

    # 计算均线和交易信号
    df = generate_signals(df, periods=[5, 10, 20], slope_periods=5)

    # 计算平均成交量
    df = calculate_volume(df, periods=20)

    # 生成荐股信号
    df = recommend_stocks(df)

    # 绘制图表
    stock_name = data_file.split('.')[0]
    plot_signals(df, stock_name, periods=[5, 10, 20])

    # 计算股票收益
    df = calculate_stock_returns(df)

    # 输出结果
    print(df[['收盘', 'MA5', 'MA10', 'MA20', 'signal', 'recommend', 'return', 'strategy_return', 'cumulative_return']].tail(20))

# 示例调用
mean_reversion_strategy('algo/tactics/000001.csv')
