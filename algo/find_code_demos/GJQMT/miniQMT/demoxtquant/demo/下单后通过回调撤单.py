import pandas as pd
import numpy as np
import datetime
from xtquant import xtdata,xttrader
from xtquant.xttype import StockAccount
from xtquant import xtconstant
from xtquant.xttrader import XtQuantTraderCallback
import sys
import time


"""
异步下单委托流程为
1.order_stock_async发出委托
2.回调on_order_stock_async_response收到回调信息
3.回调on_stock_order收到委托信息
4.回调cancel_order_stock_sysid_async发出异步撤单指令
5.回调on_cancel_order_stock_async_response收到撤单回调信息
6.回调on_stock_order收到委托信息
"""
strategy_name = "委托撤单测试"

class MyXtQuantTraderCallback(XtQuantTraderCallback):
    # 用于接收回调信息的类
    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        # 属性赋值
        account_type = order.account_type  # 账号类型
        account_id = order.account_id  # 资金账号
        stock_code = order.stock_code  # 证券代码，例如"600000.SH"
        order_id = order.order_id  # 订单编号
        order_sysid = order.order_sysid  # 柜台合同编号
        order_time = order.order_time  # 报单时间
        order_type = order.order_type  # 委托类型，参见数据字典
        order_volume = order.order_volume  # 委托数量
        price_type = order.price_type  # 报价类型，该字段在返回时为柜台返回类型，不等价于下单传入的price_type，枚举值不一样功能一样，参见数据字典
        price = order.price  # 委托价格
        traded_volume = order.traded_volume  # 成交数量
        traded_price = order.traded_price  # 成交均价
        order_status = order.order_status  # 委托状态，参见数据字典
        status_msg = order.status_msg  # 委托状态描述，如废单原因
        strategy_name = order.strategy_name  # 策略名称
        order_remark = order.order_remark  # 委托备注
        direction = order.direction  # 多空方向，股票不适用；参见数据字典
        offset_flag = order.offset_flag  # 交易操作，用此字段区分股票买卖，期货开、平仓，期权买卖等；参见数据字典

        # 打印输出
        print(f"""
        =============================
                委托信息
        =============================
        账号类型: {order.account_type}, 
        资金账号: {order.account_id},
        证券代码: {order.stock_code},
        订单编号: {order.order_id}, 
        柜台合同编号: {order.order_sysid},
        报单时间: {order.order_time},
        委托类型: {order.order_type},
        委托数量: {order.order_volume},
        报价类型: {order.price_type},
        委托价格: {order.price},
        成交数量: {order.traded_volume},
        成交均价: {order.traded_price},
        委托状态: {order.order_status},
        委托状态描述: {order.status_msg},
        策略名称: {order.strategy_name},
        委托备注: {order.order_remark},
        多空方向: {order.direction},
        交易操作: {order.offset_flag}
        """)
        if order.strategy_name == strategy_name:
            # 该委托是由本策略发出
            ssid = order.order_sysid
            status = order.order_status
            market = order.stock_code.split(".")[1]
            # print(ssid)
            if ssid and status in [50,55]:
                ## 使用cancel_order_stock_sysid_async时，投研端market参数可以填写为0，券商端按实际情况填写
                print(xt_trade.cancel_order_stock_sysid_async(account,0,ssid))

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        print(datetime.datetime.now(), '成交回调', trade.order_remark,trade.stock_code,trade.traded_volume,trade.offset_flag)

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        
        print(datetime.datetime.now(),'异步下单编号为：',response.seq)

    def on_cancel_order_stock_async_response(self, response):
        """
        异步撤单回报
        :param response: XtCancelOrderResponse 对象
        :return:
        """
        account_type = response.account_type # 账号类型
        account_id = response.account_id  # 资金账号
        order_id = response.order_id  # 订单编号
        order_sysid = response.order_sysid  # 柜台委托编号
        cancel_result = response.cancel_result  # 撤单结果
        seq = response.seq  # 异步撤单的请求序号

        print(f"""
            ===========================
                   异步撤单回调信息
            ===========================
            账号类型: {response.account_type}, 
            资金账号: {response.account_id},
            订单编号: {response.order_id}, 
            柜台委托编号: {response.order_sysid},
            撤单结果: {response.cancel_result},
            异步撤单的请求序号: {response.seq}""")
        pass


callback = MyXtQuantTraderCallback()
# 填投研端的期货账号
account = StockAccount("1000024",account_type = "FUTURE")
# 填写投研端的股票账号
# account = StockAccount("2000567")
# 填投研端的userdata路径,miniqmt指定到userdata_mini
xt_trade = xttrader.XtQuantTrader(r"C:\Program Files\测试1\迅投极速交易终端睿智融科版\userdata",int(time.time()))
# 注册接受回调
xt_trade.register_callback(callback) 
# 启动交易线程
xt_trade.start()
# 链接交易
connect_result = xt_trade.connect()
# 订阅账号信息，接受这个账号的回调，回调是账号维度的
subscribe_result = xt_trade.subscribe(account)
print(subscribe_result)


code = "rb2410.SF"
# code = "000001.SZ"

tick = xtdata.get_full_tick([code])[code]

last_price = tick["lastPrice"] # 最新价

ask_price = round(tick["askPrice"][0],3) # 卖方1档价
bid_price = round(tick["bidPrice"][4],3) # 买方5档价

symbol_info = xtdata.get_instrument_detail(code)

up_limit = symbol_info["UpStopPrice"]
down_limit = symbol_info["DownStopPrice"]

lots = 1
res_id = xt_trade.order_stock_async(account, code, xtconstant.FUTURE_OPEN_LONG, lots, xtconstant.FIX_PRICE, down_limit, strategy_name, "跌停价/固定手数")


# lots = 100
# res_id = xt_trade.order_stock_async(account, code, xtconstant.STOCK_BUY, lots, xtconstant.FIX_PRICE, bid_price, strategy_name, "跌停价/固定手数")


xtdata.run()




