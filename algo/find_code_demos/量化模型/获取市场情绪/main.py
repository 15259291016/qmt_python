import pandas as pd
import numpy as np
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()
# 技术指标分析
print("技术指标分析\n")
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
# 社交媒体情绪分析
print("社交媒体情绪分析\n")
import tweepy
from textblob import TextBlob

# Twitter API密钥
consumer_key = 'YOUR_CONSUMER_KEY'
consumer_secret = 'YOUR_CONSUMER_SECRET'
access_token = 'YOUR_ACCESS_TOKEN'
access_token_secret = 'YOUR_ACCESS_TOKEN_SECRET'

# 设置Twitter API客户端
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# 获取推文并进行情感分析
def get_twitter_sentiment(query, count=100):
    tweets = api.search(q=query, lang='en', count=count)
    sentiments = []
    for tweet in tweets:
        text = tweet.text
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        sentiments.append(sentiment)
    return sentiments

# 示例：获取关于苹果公司的推文
query = 'Apple stock'
sentiments = get_twitter_sentiment(query)

# 计算平均情感分数
average_sentiment = sum(sentiments) / len(sentiments)
print(f'Average Sentiment: {average_sentiment}')
# 资金流向分析
print("资金流向分析\n")
# 获取资金流向数据
def get_money_flow(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    money_flow = info.get('totalNetVolume', 0)
    return money_flow

# 示例：获取苹果公司的资金流向
money_flow = get_money_flow(symbol)
print(f'Money Flow: {money_flow}')
# 市场情绪调查
print("市场情绪调查\n")
# 读取AAII Sentiment Survey数据
def read_aaii_survey(file_path):
    df = pd.read_csv(file_path)
    return df

# 示例：读取AAII Sentiment Survey数据
file_path = 'aaii_sentiment_survey.csv'
aaii_df = read_aaii_survey(file_path)

# 计算最近一周的平均情绪
recent_week = aaii_df.iloc[-7:]
average_bullish = recent_week['Bullish'].mean()
average_bearish = recent_week['Bearish'].mean()
average_neutral = recent_week['Neutral'].mean()

print(f'Average Bullish: {average_bullish}')
print(f'Average Bearish: {average_bearish}')
print(f'Average Neutral: {average_neutral}')
