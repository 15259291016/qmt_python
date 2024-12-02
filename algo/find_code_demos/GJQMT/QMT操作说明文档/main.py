# coding=utf-8
import time
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant
import random




# # 创建session_id
session_id = int(random.randint(100000, 999999))
# # 创建交易对象
# xt_trader = XtQuantTrader(mini_qmt_path, session_id)
# # 启动交易对象
# xt_trader.start()
# # 连接客户端
# connect_result = xt_trader.connect()
#
# if connect_result == 0:
#     print('连接成功')
# # 创建账号对象
# acc = StockAccount(account)
# # 订阅账号
# xt_trader.subscribe(acc)
# # 下单
# res = xt_trader.order_stock(acc, stock_code='600000.SH', order_type=xtconstant.STOCK_BUY, order_volume=100, price_type=xtconstant.FIX_PRICE, price=7.44)
#
# res
class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        print("connection lost")

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        print("on order callback:")
        print(order.stock_code, order.order_status, order.order_sysid)

    def on_stock_asset(self, asset):
        """
        资金变动推送
        :param asset: XtAsset对象
        :return:
        """
        print("on asset callback")
        print(asset.account_id, asset.cash, asset.total_asset)

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        print("on trade callback")
        print(trade.account_id, trade.stock_code, trade.order_id)

    def on_stock_position(self, position):
        """
        持仓变动推送
        :param position: XtPosition对象
        :return:
        """
        print("on position callback")
        print(position.stock_code, position.volume)

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        print("on order_error callback")
        print(order_error.order_id, order_error.error_id, order_error.error_msg)

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        print("on cancel_error callback")
        print(cancel_error.order_id, cancel_error.error_id, cancel_error.error_msg)

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        print("on_order_stock_async_response")
        print(response.account_id, response.order_id, response.seq)

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        print("on_account_status")
        print(status.account_id, status.account_type, status.status)
# miniQMT安装路径
path = r'H:\Program Files (x86)\国金证券QMT交易端\userdata_mini'
# QMT账号
account = '8881667160'
# if __name__ == "__main__":


#
#     xt_trader = XtQuantTrader(path, session_id)
#     # 创建资金账号为1000000365的证券账号对象
#     acc = StockAccount(account)
#     # 创建交易回调类对象，并声明接收回调
#     callback = MyXtQuantTraderCallback()
#     xt_trader.register_callback(callback)
#     # 启动交易线程
#     xt_trader.start()
#     # 建立交易连接，返回0表示连接成功
#     connect_result = xt_trader.connect()
#     if connect_result != 0:
#         import sys
#         sys.exit('链接失败，程序即将退出 %d'%connect_result)


def connect():
    global session_id

    # 重连时需要更换session_id
    session_id += 1
    xt_trader = XtQuantTrader(path, session_id)
    # 创建资金账号为1000000365的证券账号对象
    callback = MyXtQuantTraderCallback()
    xt_trader.register_callback(callback)
    # 启动交易线程
    xt_trader.start()
    # 建立交易连接，返回0表示连接成功
    connect_result = xt_trader.connect()
    if connect_result == 0:
        return xt_trader, True
    else:
        return None, False


if __name__ == "__main__":
    xt_trader, success = connect()
    acc = StockAccount(account)
    while 1:
        if xt_trader is None:
            print('开始重连交易接口')
            xt_trader, success = connect()
            if success:
                print('交易接口重连成功')
        # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
        subscribe_result = xt_trader.subscribe(acc)
        if subscribe_result != 0:
            print('账号订阅失败 %d'%subscribe_result)
        print(subscribe_result)
        stock_code = '600000.SH'  # 参数占位用，任意股票代码都可以
        volume = 200  # 参数占位用，任意数量
        # 使用指定价下单，接口返回订单编号，后续可以用于撤单操作以及查询委托状态
        # fix_result_order_id = xt_trader.order_stock(acc, stock_code, xtconstant.CREDIT_DIRECT_CASH_REPAY, volume, xtconstant.FIX_PRICE, repay_money, 'strategy_name', 'remark')
        time.sleep(3)
