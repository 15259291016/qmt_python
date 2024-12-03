# 思想指导:
# 1、先定方向：
#      方向不需要很明确，但是要有一个大致的方向，分辨出一个股票的阶段，是上涨还是下跌，是横盘还是震荡。股票的价格是高位还是低位，高位低位是根据当前价格角度来看的，也就是说
#      每天、每周、每月、都需要根据当前的价格来给一个评价。
# 2、确定指标：
# 3、确定参数：
# 4、确定数据：
# 5、确定算法：
# 6、确定输出：
# 7、确定存储：
# 8、确定执行：
# 9、确定监控：
# 10、确定优化：
# 11、确定结束：

import pywencai as wc
import pandas as pd
# https://zhuanlan.zhihu.com/p/678521592
import akshare as ak
from akshare import stock_zh_a_hist

# res = wc.get(query='法尔胜', )
# print(res)

stock_history = stock_zh_a_hist(symbol='603444', period="daily", start_date="20180301", adjust="")
print(stock_history)

df = pd.DataFrame(stock_history)
df['日期'] = pd.to_datetime(df['日期'])

# 1、大致方向

# 计算五日均线
# df['开盘五日均线'] = df['开盘'].rolling(window=5).mean()
# df['收盘五日均线'] = df['收盘'].rolling(window=5).mean()
# df['最高五日均线'] = df['最高'].rolling(window=5).mean()
# df['最低五日均线'] = df['最低'].rolling(window=5).mean()
# df['成交量五日均线'] = df['成交量'].rolling(window=5).mean()
# df['成交额五日均线'] = df['成交额'].rolling(window=5).mean()
# df['振幅五日均线'] = df['振幅'].rolling(window=5).mean()
# df['涨跌幅五日均线'] = df['涨跌幅'].rolling(window=5).mean()
# df['涨跌额五日均线'] = df['涨跌额'].rolling(window=5).mean()
# df['换手率五日均线'] = df['换手率'].rolling(window=5).mean()

# 输出结果
# print(df[[
#     '日期', '开盘', '开盘五日均线','收盘','收盘五日均线','最高',
#     '最高五日均线','最低','最低五日均线','成交量','成交量五日均线',
#     '成交额','成交额五日均线','振幅','振幅五日均线','涨跌幅','涨跌幅五日均线',
#     '涨跌额','涨跌额五日均线','换手率','换手率五日均线']])