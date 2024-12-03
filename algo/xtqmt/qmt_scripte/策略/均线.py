import easyquotation
import tushare as ts
import pandas as pd

# 设置 Tushare API Token
ts.set_token('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')
pro = ts.pro_api()


# 1、获取A股市场所以股票代码
# 2、获取A股市场股票近两年历史数据
# 3、计算均线
# 4、计算布林线
# 5、计算MACD
# 6、计算KDJ线

# 示例：获取股票代码为 '000001.SZ' 的历史数据
stock_code = '000001.SZ'
start_date = '20230101'
end_date = '20241231'

# 获取某只股票的历史数据
def get_historical_data(stock_code, start_date, end_date):
    df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
    return df

# 计算均线
def calculate_5_day_moving_average(df, days:list[int] = [5]) -> pd.DataFrame:
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values(by='trade_date')
    for day in days:
        df[f'{day}_day_ma'] = df['close'].rolling(window=day).mean()
    return df

# 计算筹码集中度
def calculate_chips_concentration(df, period:str = '20230930'):
    # 假设我们使用前十大股东持股比例来计算筹码集中度
    top_10_holders = pro.top10_holders(ts_code=stock_code, period=period)
    top_10_holders['hold_ratio'] = top_10_holders['hold_ratio'] / 100.0
    concentration = top_10_holders['hold_ratio'].sum()
    return concentration

# 计算获利比例
def calculate_profit_ratio(df, current_price):
    df['profit'] = (current_price - df['close']) / df['close']
    profit_ratio = (df['profit'] > 0).mean() * 100
    return profit_ratio

# 计算筹码成本
def calculate_chips_cost(df):
    # 计算每日的成交金额
    df['amount'] = df['close'] * df['vol']  # 成交金额 = 收盘价 * 成交量
    # 计算总成交金额和总成交量
    total_amount = df['amount'].sum()
    total_volume = df['vol'].sum()
    # 计算平均成本
    chips_cost = total_amount / total_volume
    return chips_cost


df = get_historical_data(stock_code, start_date, end_date)

try:
    df_stock_info = pro.stock_basic(ts_code=stock_code, fields='ts_code,name,total_share')
    df_stock_info.to_csv("df_stock_info.csv")
except Exception as e:
    print(e)
    df_stock_info = pd.read_csv("df_stock_info.csv", index_col=0)


# 获取该股票的十大股东信息
df_top_holders = pro.top10_holders(ts_code=stock_code, start_date=start_date, end_date=end_date)
print(df_top_holders)

# 假设总股本为 total_share，前十大股东持有股份总数为 top_10_holdings
total_share = df_stock_info['total_share'].iloc[0]
top_10_holdings = df_top_holders['hold_amount'].sum()

# 估算散户持有的股份总数
retail_holdings = total_share - top_10_holdings

# 假设平均每个散户持有1000股（这个数值可以根据实际情况调整）
average_shares_per_retail_investor = 1000

# 估算散户数量
estimated_retail_investors = retail_holdings // average_shares_per_retail_investor

print(f"总股本: {total_share}")
print(f"前十大股东持有股份总数: {top_10_holdings}")
print(f"散户持有股份总数: {retail_holdings}")
print(f"估计散户数量: {estimated_retail_investors}")

df_with_ma = calculate_5_day_moving_average(df, [5,10,20,30])
print(df_with_ma)

# 获取当前价格（假设使用最新一天的收盘价）
current_price = df['close'].iloc[0]

# 计算筹码集中度
chips_concentration = calculate_chips_concentration(df, '20240930')

# 计算获利比例
profit_ratio = calculate_profit_ratio(df, current_price)

# 计算筹码成本
chips_cost = calculate_chips_cost(df)

print(f"筹码集中度: {chips_concentration:.2f}%")
print(f"获利比例: {profit_ratio:.2f}%")
print(f"筹码成本: {chips_cost:.2f}")
print(f"当前价格: {current_price:.2f}")
print(f"5日均线: {df_with_ma['5_day_ma'].iloc[-1]:.2f}")
print(f"10日均线: {df_with_ma['10_day_ma'].iloc[-1]:.2f}")
print(f"20日均线: {df_with_ma['20_day_ma'].iloc[-1]:.2f}")
print(f"30日均线: {df_with_ma['30_day_ma'].iloc[-1]:.2f}")