import pandas as pd
import numpy as np

# =====================
# 均线信号
# =====================
def add_ma_signals(df, short=5, long=20, price_col='close'):
    """
    计算均线及金叉/死叉信号
    :param df: DataFrame，需包含price_col
    :param short: 短期均线周期
    :param long: 长期均线周期
    :param price_col: 价格列名
    :return: 增加ma_short, ma_long, golden_cross, death_cross列
    """
    df[f'ma{short}'] = df[price_col].rolling(short).mean()
    df[f'ma{long}'] = df[price_col].rolling(long).mean()
    df['golden_cross'] = (df[f'ma{short}'] > df[f'ma{long}']) & (df[f'ma{short}'].shift(1) <= df[f'ma{long}'].shift(1))
    df['death_cross'] = (df[f'ma{short}'] < df[f'ma{long}']) & (df[f'ma{short}'].shift(1) >= df[f'ma{long}'].shift(1))
    return df

# =====================
# MACD信号
# =====================
def add_macd_signals(df, price_col='close', fast=12, slow=26, signal=9):
    """
    计算MACD及金叉/死叉信号
    :param df: DataFrame，需包含price_col
    :param fast: 快线周期
    :param slow: 慢线周期
    :param signal: 信号线周期
    :return: 增加DIF, DEA, MACD, macd_golden, macd_death列
    """
    exp1 = df[price_col].ewm(span=fast, adjust=False).mean()
    exp2 = df[price_col].ewm(span=slow, adjust=False).mean()
    df['DIF'] = exp1 - exp2
    df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    df['macd_golden'] = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
    df['macd_death'] = (df['DIF'] < df['DEA']) & (df['DIF'].shift(1) >= df['DEA'].shift(1))
    return df

# =====================
# 布林带信号
# =====================
def add_bollinger_bands(df, price_col='close', window=20, num_std=2):
    """
    计算布林带上下轨
    :param df: DataFrame，需包含price_col
    :param window: 均线窗口
    :param num_std: 标准差倍数
    :return: 增加mid, upper, lower列
    """
    df['mid'] = df[price_col].rolling(window).mean()
    df['std'] = df[price_col].rolling(window).std()
    df['upper'] = df['mid'] + num_std * df['std']
    df['lower'] = df['mid'] - num_std * df['std']
    return df

# =====================
# 压力位/支撑位
# =====================
def add_support_resistance(df, high_col='high', low_col='low', window=20):
    """
    计算区间高低点压力位/支撑位
    :param df: DataFrame，需包含high_col, low_col
    :param window: 区间长度
    :return: 增加resistance, support列
    """
    df['resistance'] = df[high_col].rolling(window).max()
    df['support'] = df[low_col].rolling(window).min()
    return df

# =====================
# RSI信号
# =====================
def add_rsi(df, price_col='close', period=14):
    """
    计算RSI指标
    :param df: DataFrame，需包含price_col
    :param period: RSI周期
    :return: 增加RSI列
    """
    delta = df[price_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# =====================
# 一键添加全部信号
# =====================
def add_all_signals(df):
    df = add_ma_signals(df)
    df = add_macd_signals(df)
    df = add_bollinger_bands(df)
    df = add_support_resistance(df)
    df = add_rsi(df)
    return df 