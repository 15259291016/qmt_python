
# 导入 efinance 如果没有安装则需要通过执行命令: pip install efinance 来安装
import efinance as ef
import time
from datetime import datetime
# 股票代码
stock_code = '603444'
# 数据间隔时间为 1 分钟
freq = 1
status = {stock_code: 0}
while 1:
    # 获取最新一个交易日的分钟级别股票行情数据
    df = ef.stock.get_quote_history(
        stock_code, klt=freq)
    # 现在的时间
    now = str(datetime.today()).split('.')[0]
    # 将数据存储到 csv 文件中
    df.to_csv(f'{stock_code}.csv', encoding='utf-8-sig', index=None)
    print(f'已在 {now}, 将股票: {stock_code} 的行情数据存储到文件: {stock_code}.csv 中！')
    if len(df) == status[stock_code]:
        print(f'{stock_code} 已收盘')
        break
    status[stock_code] = len(df)
    print('暂停 60 秒')
    time.sleep(60)
    print('-'*10)

print('全部股票已收盘')