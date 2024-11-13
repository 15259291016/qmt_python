from akshare import stock_zh_a_hist
import akshare as ak

# stock = stock_zh_a_hist(symbol='603444', period="daily", start_date="20220301", end_date='20231225', adjust="")
# 股票市场总貌
stock_sse_summary_df = ak.stock_sse_summary()
print(stock_sse_summary_df)
