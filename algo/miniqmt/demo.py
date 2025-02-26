import random

from xtquant.xttype import StockAccount
from xtquant.xttrader import XtQuantTrader
from xtquant import xtconstant

# miniQMT安装路径
mini_qmt_path = r'H:\Program Files (x86)\国金证券QMT交易端\userdata_mini'
# QMT账号
account = '8881667160'
# 创建session_id
session_id = int(random.randint(100000, 999999))
# 创建交易对象
xt_trader = XtQuantTrader(mini_qmt_path, session_id)
# 启动交易对象
xt_trader.start()
# 连接客户端
connect_result = xt_trader.connect()

if connect_result == 0:
    print('连接成功')
# 创建账号对象
acc = StockAccount(account)
# 订阅账号
xt_trader.subscribe(acc)
# 下单
res = xt_trader.order_stock(acc, stock_code='600000.SH', order_type=xtconstant.STOCK_BUY, order_volume=100, price_type=xtconstant.FIX_PRICE, price=7.44)

print(res)