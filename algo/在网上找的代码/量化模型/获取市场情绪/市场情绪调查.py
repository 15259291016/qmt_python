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
