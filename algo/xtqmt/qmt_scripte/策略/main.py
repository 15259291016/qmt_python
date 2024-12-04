# 1、获取A股市场所以股票代码
# 2、获取A股市场股票近两年历史数据
# 3、计算均线
# 4、计算布林线
# 5、计算MACD
# 6、计算KDJ线

# 定义起始和结束代码
start_code = '0000'
end_code = '3999'

# 生成股票代码范围
stock_codes = [f'{i:04d}' for i in range(int(start_code[2:]), int(end_code[2:]) + 1)]

# 打印股票代码
print(stock_codes)

import pandas_datareader as pdr
import pandas as pd

# 获取A股市场所有股票近两年的历史数据
data = pdr.get_data_yahoo('沪深300', start='2022-01-01', end='2023-12-31')

# 将数据转换为DataFrame
df = pd.DataFrame(data)

# 打印数据
print(df)