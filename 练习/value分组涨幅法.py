import pandas as pd
import tushare as ts
from datetime import datetime, timedelta

# 初始化Tushare
pro = ts.pro_api('gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482')

# 1. 获取所有A股的市值
stock_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name')
daily_basic = pro.daily_basic(trade_date=datetime.now().strftime('%Y%m%d'), fields='ts_code,total_mv')

# 合并股票基本信息和市值
df = pd.merge(stock_basic, daily_basic, on='ts_code')
df = df.rename(columns={'total_mv': 'market_cap'})  # 市值单位：ten bilian yuan

# 2. 获取近一个月的涨跌幅
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
start_str = start_date.strftime('%Y%m%d')
end_str = end_date.strftime('%Y%m%d')

pct_chg_list = []
for code in df['ts_code']:
    try:
        daily = pro.daily(ts_code=code, start_date=start_str, end_date=end_str)
        if len(daily) > 0:
            pct_chg = (daily.iloc[0]['close'] - daily.iloc[-1]['close']) / daily.iloc[-1]['close'] * 100
            pct_chg_list.append(pct_chg)
        else:
            pct_chg_list.append(None)
    except Exception as e:
        pct_chg_list.append(None)

df['pct_chg'] = pct_chg_list

# 3. 按市值排序分组
df = df.dropna(subset=['market_cap', 'pct_chg'])
df = df.sort_values('market_cap')
n = len(df)
small = df.iloc[:n//3]
mid = df.iloc[n//3:2*n//3]
large = df.iloc[2*n//3:]

print('小盘平均涨幅:', small['pct_chg'].mean())
print('中盘平均涨幅:', mid['pct_chg'].mean())
print('大盘平均涨幅:', large['pct_chg'].mean())
