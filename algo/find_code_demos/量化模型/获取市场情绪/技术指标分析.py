import pandas as pd
import numpy as np
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

# 获取股票数据
def get_stock_data(symbol, start_date, end_date):
    df = pdr.get_data_yahoo(symbol, start=start_date, end=end_date)
    return df

# 计算RSI
def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 计算MACD
def compute_macd(data, short_window=12, long_window=26, signal_window=9):
    ema_short = data['Close'].ewm(span=short_window, adjust=False).mean()
    ema_long = data['Close'].ewm(span=long_window, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    macd_hist = macd - signal
    return macd, signal, macd_hist

# 示例：获取苹果公司股票数据
symbol = 'AAPL'
start_date = '2023-01-01'
end_date = '2023-12-31'

df = get_stock_data(symbol, start_date, end_date)

# 计算RSI和MACD
df['RSI'] = compute_rsi(df)
df['MACD'], df['Signal'], df['MACD_Hist'] = compute_macd(df)

print(df.tail())
