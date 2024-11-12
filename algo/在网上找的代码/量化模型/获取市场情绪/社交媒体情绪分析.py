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
