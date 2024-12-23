# coding:utf-8
import time, datetime, traceback, sys
from xtquant import xtdata
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant


# 定义一个类 创建类的实例 作为状态的容器
class _a():
    pass


A = _a()
A.bought_list = []
A.hsa = xtdata.get_stock_list_in_sector('沪深A股')


def interact():
    """执行后进入repl模式"""
    import code
    code.InteractiveConsole(locals=globals()).interact()


xtdata.download_sector_data()


def f(data):
    print(data)
    now = datetime.datetime.now()
    for stock in data:
        if stock not in A.hsa:
            continue
        cuurent_price = data[stock][0]['close']
        pre_price = data[stock][0]['preClose']
        ratio = cuurent_price / pre_price - 1 if pre_price > 0 else 0
        if ratio > 0.09 and stock not in A.bought_list:
            print(f"{now} 最新价 买入 {stock} 100股")
            async_seq = xt_trader.order_stock_async(acc, stock, xtconstant.STOCK_BUY, 100, xtconstant.LATEST_PRICE, -1,
                                                    'strategy_name', stock)
            A.bought_list.append(stock)


class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        print(datetime.datetime.now(), '连接断开回调')

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        print(datetime.datetime.now(), '委托回调', order.order_remark)

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        print(datetime.datetime.now(), '成交回调', trade.order_remark)

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        # print("on order_error callback")
        # print(order_error.order_id, order_error.error_id, order_error.error_msg)
        print(f"委托报错回调 {order_error.order_remark} {order_error.error_msg}")

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        print(datetime.datetime.now(), sys._getframe().f_code.co_name)

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        print(f"异步委托回调 {response.order_remark}")

    def on_cancel_order_stock_async_response(self, response):
        """
        :param response: XtCancelOrderResponse 对象
        :return:
        """
        print(datetime.datetime.now(), sys._getframe().f_code.co_name)

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        print(datetime.datetime.now(), sys._getframe().f_code.co_name)


if __name__ == '__main__':
    print("start")
    # 指定客户端所在路径, 券商端指定到 userdata_mini文件夹
    # 注意：如果是连接投研端进行交易，文件目录需要指定到f"{安装目录}\userdata"
    path = r'D:\qmt\投研\迅投极速交易终端睿智融科版\userdata'
    # 生成session id 整数类型 同时运行的策略不能重复
    session_id = int(time.time())
    xt_trader = XtQuantTrader(path, session_id)
    # 开启主动请求接口的专用线程 开启后在on_stock_xxx回调函数里调用XtQuantTrader.query_xxx函数不会卡住回调线程，但是查询和推送的数据在时序上会变得不确定
    # 详见: http://docs.thinktrader.net/vip/pages/ee0e9b/#开启主动请求接口的专用线程
    # xt_trader.set_relaxed_response_order_enabled(True)

    # 创建资金账号为 800068 的证券账号对象 股票账号为STOCK 信用CREDIT 期货FUTURE
    acc = StockAccount('2000128', 'STOCK')
    # 创建交易回调类对象，并声明接收回调
    callback = MyXtQuantTraderCallback()
    xt_trader.register_callback(callback)
    # 启动交易线程
    xt_trader.start()
    # 建立交易连接，返回0表示连接成功
    connect_result = xt_trader.connect()
    print('建立交易连接，返回0表示连接成功', connect_result)
    # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
    subscribe_result = xt_trader.subscribe(acc)
    print('对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功', subscribe_result)

    #订阅的品种列表
    code_list = ['600000.SH', '000001.SZ']

    for code in code_list:
        xtdata.subscribe_quote(code, '1d', callback = f)

    # 阻塞主线程退出
    xt_trader.run_forever()
    # 如果使用vscode pycharm等本地编辑器 可以进入交互模式 方便调试 （把上一行的run_forever注释掉 否则不会执行到这里）
    interact()


