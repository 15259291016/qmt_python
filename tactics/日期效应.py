import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dateutil import rrule
from datetime import datetime, timedelta

def get_holiday_list(start_date, end_date):
    """
    获取节日日期列表
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 节日日期列表
    """
    # 示例：春节和国庆节
    holidays = []
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    # 春节（每年 2 月 1 日至 2 月 10 日）
    for dt in rrule.rrule(rrule.YEARLY, dtstart=start, until=end, bymonth=2, bymonthday=1):
        holidays.append(dt.date())

    # 国庆节（每年 10 月 1 日至 10 月 10 日）
    for dt in rrule.rrule(rrule.YEARLY, dtstart=start, until=end, bymonth=10, bymonthday=1):
        holidays.append(dt.date())

    return holidays

def generate_holiday_effect_signals(df, holidays, window=5):
    """
    生成日期效应交易信号
    :param df: 股票数据 DataFrame
    :param holidays: 节日日期列表
    :param window: 时间窗口（天数）
    :return: 包含交易信号的 DataFrame
    """
    df['holiday_effect'] = 0
    df['distance_to_holiday'] = None

    for index, row in df.iterrows():
        current_date = index.date()
        min_distance = np.inf
        closest_holiday = None

        for holiday in holidays:
            delta = (holiday - current_date).days
            if abs(delta) < min_distance:
                min_distance = abs(delta)
                closest_holiday = holiday

        df.at[index, 'distance_to_holiday'] = min_distance

        # 如果距离节日小于窗口天数，生成买入信号
        if min_distance <= window:
            df.at[index, 'holiday_effect'] = 1
        else:
            df.at[index, 'holiday_effect'] = -1

    return df

def backtest_strategy(df):
    """
    回测日期效应策略
    :param df: 包含交易信号的 DataFrame
    :return: 回测结果
    """
    df['return'] = df['收盘'].pct_change()
    df['strategy_return'] = df['return'] * df['holiday_effect'].shift(1)
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod()

    # 计算性能指标
    total_return = df['cumulative_return'].iloc[-1] - 1
    volatility = df['strategy_return'].std() * np.sqrt(252)
    sharpe_ratio = total_return / volatility

    return {
        'total_return': total_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio
    }

def plot_results(df):
    """
    绘制回测结果
    :param df: 回测数据 DataFrame
    """
    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df['收盘'], label='Close Price', color='blue')
    plt.plot(df.index, df['cumulative_return'] * df['收盘'].iloc[0], label='Strategy Return', color='red')

    # 标记买入和卖出信号
    buy_signals = df[df['holiday_effect'] == 1]
    sell_signals = df[df['holiday_effect'] == -1]

    plt.scatter(buy_signals.index, buy_signals['收盘'], label='Buy Signal', marker='^', color='green', alpha=1)
    plt.scatter(sell_signals.index, sell_signals['收盘'], label='user_strategy Signal', marker='v', color='red', alpha=1)

    plt.title('Holiday Effect Strategy Backtest')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

def holiday_effect_strategy(data_file, start_date, end_date, window=5):
    """
    日期效应策略
    :param data_file: 数据文件路径
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param window: 时间窗口（天数）
    """
    # 加载数据
    df = pd.read_csv(data_file)
    df['日期'] = pd.to_datetime(df['日期'])
    df.set_index('日期', inplace=True)
    df.sort_index(inplace=True)

    # 获取节日日期列表
    holidays = get_holiday_list(start_date, end_date)

    # 生成交易信号
    df = generate_holiday_effect_signals(df, holidays, window)

    # 回测策略
    results = backtest_strategy(df)
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Volatility: {results['volatility']:.2%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")

    # 绘制结果
    plot_results(df)

# 示例调用
holiday_effect_strategy('algo/tactics/000001.csv', '2024-01-01', '2025-01-01', window=5)
