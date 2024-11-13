# 导入 efinance 如果没有安装则需要通过执行命令: pip install efinance 来安装
import efinance as ef
# 股票代码
stock_code = '600519'
# 数据间隔时间为 1 分钟
freq = 1
# 获取最新一个交易日的分钟级别股票行情数据
stock_list = ['钱江摩托','水星家纺']

for i in stock_list:
    df = ef.stock.get_quote_history(i, klt=freq)
    # 将数据存储到 csv 文件中
    df.to_csv(f'{i}.csv', encoding='utf-8-sig', index=None)
    print(f'股票: {i} 的行情数据已存储到文件: {i}.csv 中！')