import tushare as ts
import datetime

pro = ts.pro_api('gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482')
today = datetime.datetime.today().strftime('%Y%m%d')
start = (datetime.datetime.today() - datetime.timedelta(days=30)).strftime('%Y%m%d')

# 获取沪深300和中证1000指数近30日收盘价
hs300 = pro.index_daily(ts_code='000300.SH', start_date=start, end_date=today)
zz1000 = pro.index_daily(ts_code='000852.SH', start_date=start, end_date=today)

# 按日期升序排列，便于逐日计算涨跌幅
hs300 = hs300.sort_values('trade_date').reset_index(drop=True)
zz1000 = zz1000.sort_values('trade_date').reset_index(drop=True)

# 只保留最近11个交易日（用于计算10天的涨跌幅）
hs300 = hs300.tail(11).reset_index(drop=True)
zz1000 = zz1000.tail(11).reset_index(drop=True)

print("日期\t\t大盘涨跌幅\t小盘涨跌幅\t主导风格")
for i in range(1, 11):
    date = hs300.loc[i, 'trade_date']
    hs300_return = (hs300.loc[i, 'close'] - hs300.loc[i-1, 'close']) / hs300.loc[i-1, 'close'] * 100
    zz1000_return = (zz1000.loc[i, 'close'] - zz1000.loc[i-1, 'close']) / zz1000.loc[i-1, 'close'] * 100
    if hs300_return > zz1000_return:
        leader = '大盘主导'
    elif hs300_return < zz1000_return:
        leader = '小盘主导'
    else:
        leader = '持平'
    print(f"{date}\t{hs300_return:.2f}%\t\t{zz1000_return:.2f}%\t\t{leader}")
