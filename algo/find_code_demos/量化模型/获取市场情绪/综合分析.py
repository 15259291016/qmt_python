# 综合市场情绪评分
def combine_sentiments(rsi, macd, average_sentiment, money_flow, average_bullish, average_bearish, average_neutral):
    # 这里只是一个简单的加权平均示例，可以根据实际情况调整权重
    rsi_score = (rsi.mean() - 50) / 50  # RSI在50以上为正向，50以下为负向
    macd_score = macd.mean()  # MACD正值为正向，负值为负向
    twitter_score = average_sentiment
    money_flow_score = money_flow / 1e9  # 标准化资金流向
    aaii_score = (average_bullish - average_bearish) / 100  # 正向情绪减去负向情绪

    combined_score = (rsi_score + macd_score + twitter_score + money_flow_score + aaii_score) / 5
    return combined_score


# 示例：计算综合市场情绪评分
combined_score = combine_sentiments(
    df['RSI'],
    df['MACD'],
    average_sentiment,
    money_flow,
    average_bullish,
    average_bearish,
    average_neutral
)

print(f'Combined Market Sentiment Score: {combined_score}')
