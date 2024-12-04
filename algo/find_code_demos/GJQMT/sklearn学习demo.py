# encoding:gbk
'''
本策略事先设定好交易的股票篮子，然后根据指数的CCI指标来判断超买和超卖
当有超买和超卖发生时，交易事先设定好的股票篮子
'''
import pandas as pd
import numpy as np
import talib
import requests
import json
from xtquant import xtdata

account = '8881667160'
max_rate = 0.5
url = "http://127.0.0.1:8000"

accountObj = {'code_list': ('002933.SZ'),  #
              'trading_snapshot': [],  #
              'orders': {},  #
              'deals': {},  #
              'positions': {},  #
              'accounts': {},  #
              'financial_status': 0.0,
              'amount': 0,
              'bidVol': 0,  # 购买手
              'sell_ask': 0,  # 购买手
              'buy_ask': 0,  # 购买手
              }


def gp_type_szsh(code):
    if code.find('60', 0, 3) == 0:
        code = code + '.SH'
    elif code.find('688', 0, 4) == 0:
        code = code + '.SH'
    elif code.find('900', 0, 4) == 0:
        code = code + '.SH'
    elif code.find('00', 0, 3) == 0:
        code = code + '.SZ'
    elif code.find('300', 0, 4) == 0:
        code = code + '.SZ'
    elif code.find('200', 0, 4) == 0:
        code = code + '.SZ'
    return code


class timeDecided:
    def __init__(self):
        self.min_price_list = []
        self.min_big_price_list = []
        self.Fmin_price_list = []
        self.Fmin_big_price_list = []
        self.all_price_list = []
        self.all_big_price_list = []

    def addObj(self, priceObj):
        self.all_price_list.append(priceObj)
        code = list(priceObj.keys())[0]
        # 还缺一个看大单压顶的功能
        sell_ask = sum(priceObj[code]['askPrice'])
        buy_ask = sum(priceObj[code]['bidPrice'])
        if len(self.min_price_list) < 23:
            self.min_price_list.append(priceObj)
        else:
            del self.min_price_list[0]
            del self.min_big_price_list[0]
            self.min_price_list.append(priceObj)
        if len(self.Fmin_price_list) < 115:
            self.Fmin_price_list.append(priceObj)
        else:
            del self.Fmin_price_list[0]
            del self.Fmin_big_price_list[0]
            self.Fmin_price_list.append(priceObj)
        # code = accountObj['code_list']
        print(f'sell_ask:{sell_ask}')
        print(f'buy_ask:{buy_ask}')
        transaction_volume = (priceObj[code]["amount"] - accountObj["amount"]) * priceObj[code]["lastPrice"] / 10000  # 万
        if (priceObj[code]["amount"] - accountObj["amount"]) / 100 > 18000 and buy_ask > accountObj['buy_ask']:
            self.min_big_price_list.append(10)
            self.Fmin_big_price_list.append(10)
            self.all_big_price_list.append(10)
        elif (priceObj[code]["amount"] - accountObj["amount"]) / 100 > 10000 and buy_ask > accountObj['buy_ask']:
            self.min_big_price_list.append(5)
            self.Fmin_big_price_list.append(5)
            self.all_big_price_list.append(5)
        elif (priceObj[code]["amount"] - accountObj["amount"]) / 100 > 6000 and buy_ask > accountObj['buy_ask']:
            self.min_big_price_list.append(4)
            self.Fmin_big_price_list.append(4)
            self.all_big_price_list.append(4)
        elif (priceObj[code]["amount"] - accountObj["amount"]) / 100 > 3000 and buy_ask > accountObj['buy_ask']:
            self.min_big_price_list.append(3)
            self.Fmin_big_price_list.append(3)
            self.all_big_price_list.append(3)
        else:
            self.min_big_price_list.append(0)
            self.Fmin_big_price_list.append(0)
            self.all_big_price_list.append(0)
        accountObj['sell_ask'] = sell_ask
        accountObj['buy_ask'] = sell_ask

    def predict(self):
        if sum(self.min_big_price_list) > 13 and sum(self.min_big_price_list[int(len(self.min_big_price_list) / 2):]) > 18:
            if sum(self.Fmin_big_price_list) > 25:
                return True
        return False


class a():
    pass


def on_data(datas):
    for stock_code in datas:
        print(stock_code, datas[stock_code])


def on_disconnected(self):
    """
    连接断开
    :return:
    """
    print("连接断开")


def on_stock_order(self, order):
    """
    委托回报推送
    :param order: XtOrder对象
    :return:
    """
    print("委托回报推送:")
    print(order.stock_code, order.order_status, order.order_sysid)


def on_stock_asset(self, asset):
    """
    资金变动推送
    :param asset: XtAsset对象
    :return:
    """
    print("资金变动推送")
    print(asset.account_id, asset.cash, asset.total_asset)


def on_stock_position(self, position):
    """
    持仓变动推送
    :param position: XtPosition对象
    :return:
    """
    print("持仓变动推送")
    print(position.stock_code, position.volume)


def on_order_error(self, order_error):
    """
    委托失败推送
    :param order_error:XtOrderError 对象
    :return:
    """
    print("委托失败推送")
    print(order_error.order_id, order_error.error_id, order_error.error_msg)


def on_cancel_error(self, cancel_error):
    """
    撤单失败推送
    :param cancel_error: XtCancelError 对象
    :return:
    """
    print("撤单失败推送")
    print(cancel_error.order_id, cancel_error.error_id, cancel_error.error_msg)


def on_order_stock_async_response(self, response):
    """
    异步下单回报推送
    :param response: XtOrderResponse 对象
    :return:
    """
    print("异步下单回报推送")
    print(response.account_id, response.order_id, response.seq)


def on_account_status(self, status):
    """
    :param response: XtAccountStatus 对象
    :return:
    """
    print("on_account_status")
    print(status.account_id, status.account_type, status.status)


decider1 = timeDecided()


def init(C):
    '''
    First:
        Gain the account fund
    '''
    orders, deals, positions, accounts = query_info(C)  # 查询账户信息


# orders:
# print(f'{accountObj["position"]["m_strInstrumentName"]}:{accountObj["position"]["m_nVolume"]}')
def postsell(orders, deals, positions, accounts):
    # orders
    order_list = []
    for order in orders:
        o = {}
        o['m_strInstrumentID'] = order.m_strInstrumentID
        o['m_strInstrumentName'] = order.m_strInstrumentName
        o['m_nOffsetFlag'] = order.m_nOffsetFlag  # 卖卖
        o['m_nVolumeTotalOriginal'] = order.m_nVolumeTotalOriginal  # 委托数量
        o['m_dTradedPrice'] = order.m_dTradedPrice  # 成交均价
        o['m_nVolumeTraded'] = order.m_nVolumeTraded  # 成交数量
        o['m_dTradeAmount'] = order.m_dTradeAmount  # 成交金额
        # print(o)
        order_list.append(o)
    # deals
    deal_list = []
    for deal in deals:
        o = {}
        o['m_strInstrumentID'] = deal.m_strInstrumentID
        o['m_strInstrumentName'] = deal.m_strInstrumentName
        o['m_nOffsetFlag'] = deal.m_nOffsetFlag  # 卖卖
        o['m_dPrice'] = deal.m_dPrice  # 成交价格
        o['m_nVolume'] = deal.m_nVolume  # 成交数量
        o['m_dTradeAmount'] = deal.m_dTradeAmount  # 成交金额
        # print(o)
        deal_list.append(o)
    # positions
    position_list = []
    for position in positions:
        o = {}
        o['m_strInstrumentID'] = position.m_strInstrumentID
        o['m_strInstrumentName'] = position.m_strInstrumentName
        o['m_nVolume'] = position.m_nVolume  # 持仓量
        o['m_nCanUseVolume'] = position.m_nCanUseVolume  # 可用数量
        o['m_dOpenPrice'] = position.m_dOpenPrice  # 成本价
        o['m_dInstrumentValue'] = position.m_dInstrumentValue  # 市值
        o['m_dPositionCost'] = position.m_dPositionCost  # 持仓成本
        o['m_dPositionProfit'] = position.m_dPositionProfit  # 盈亏
        # print(o)
        position_list.append(o)
    # accounts
    account_list = []
    for account in accounts:
        o = {}
        o['m_dBalance'] = account.m_dBalance  # 总资产
        o['m_dAssureAsset'] = account.m_dAssureAsset  # 净资产
        o['m_dInstrumentValue'] = account.m_dInstrumentValue  # 总市值
        o['m_dAvailable'] = account.m_dAvailable  # 可用金额
        o['m_dPositionProfit'] = account.m_dPositionProfit  # 盈亏
        # print(o)
        account_list.append(o)
    demo_url = url + '/sell'
    res = requests.post(demo_url, data=json.dumps({"orders": order_list, 'deals': deal_list, "positions": position_list, "accounts": account_list}))
    return res


def getbuy_codes():
    demo_url = url + '/buy'
    res = requests.get(demo_url)
    return res


def handlebar(C):
    if not C.is_last_bar():
        return
    orders, deals, positions, accounts = query_info(C)  # 查询账户信息

    accountObj['all_bullet'] = accounts[0].m_dBalance
    accountObj['bullet'] = accounts[0].m_dAvailable
    accountObj['max_use_bullet'] = accounts[0].m_dBalance * max_rate
    # print('accountObj:'+str(accountObj['code_list']))
    result = postsell(orders, deals, positions, accounts)
    # 计算北向总买卖
    north_finance_info = C.get_north_finance_change('1m')
    north_finance_info_value = C.get_north_finance_change('1m')[list(C.get_north_finance_change('1m').keys())[0]]
    all_buy = float(north_finance_info_value['hgtNorthBuyMoney'] + north_finance_info_value['hgtSouthBuyMoney'] + north_finance_info_value['sgtNorthBuyMoney'] + north_finance_info_value['sgtSouthBuyMoney']) / 100000000
    all_sell = float(north_finance_info_value['hgtNorthSellMoney'] + north_finance_info_value['hgtSouthSellMoney'] + north_finance_info_value['sgtNorthSellMoney'] + north_finance_info_value['sgtSouthSellMoney']) / 100000000

    # 计算大盘成交额
    A_all = 0
    for code in ['000001.SH', '399001.SZ']:
        tick = C.get_full_tick([code])
        A_all = A_all + tick[code]['amount']
    print("-" * 170)
    print(f'总买入:{all_buy}亿-----总卖出:{all_sell}----成交额:{A_all / 100000000}')
    if accountObj["financial_status"] != 0:
        print(f'大盘变动：{A_all / 100000000 - accountObj["financial_status"]:.2f}亿,百分比:{(A_all / 100000000) / (accountObj["financial_status"]) / 100:.2f}%')
    accountObj['financial_status'] = A_all / 100000000
    transaction_volume = (tick[code]["amount"] - accountObj["amount"]) * tick[code]["lastPrice"] / 10000  # 万
    # accountObj["positions"]['m_dInstrumentValue']		# 体量
    # accountObj['code_list'] = eval(getbuy_codes().text)
    code = gp_type_szsh(accountObj["positions"]['m_strInstrumentID'])
    tick = C.get_full_tick([code])
    print(f'成本价:{accountObj["positions"]["m_dOpenPrice"]:.2f}--------- 换手率{((tick[code]["amount"] - accountObj["amount"]) / 100) / tick[code]["amount"] * 100:.4f}%')
    print(f'卖:{tick[code]["askPrice"]}----{tick[code]["askVol"]}---- 手:{sum(tick[code]["askVol"])} ----金额:{[str(tick[code]["askPrice"][i] * tick[code]["askVol"][i] * 100 / 10000) + "万" for i in range(len(tick[code]["askPrice"]))]}----总:{sum([tick[code]["askPrice"][i] * tick[code]["askVol"][i] * 100 / 10000 for i in range(len(tick[code]["askPrice"]))]):.2f}万')
    print(f'买:{tick[code]["bidPrice"]}----{tick[code]["bidVol"]}---- 手:{sum(tick[code]["bidVol"])} ----金额:{[str(tick[code]["bidPrice"][i] * tick[code]["bidVol"][i] * 100 / 10000) + "万" for i in range(len(tick[code]["bidPrice"]))]}----总:{sum([tick[code]["bidPrice"][i] * tick[code]["bidVol"][i] * 100 / 10000 for i in range(len(tick[code]["bidPrice"]))]):.2f}万')
    if accountObj['amount'] != 0:
        (tick[code]["amount"] - accountObj["amount"]) * tick[code]["lastPrice"] / 10000
        print(f"open:{tick[code]['open']}----high:{tick[code]['high']}----low:{tick[code]['low']}----lastClose:{tick[code]['lastClose']}")
        decider1.addObj(tick)
        print(f'成本价:{accountObj["positions"]["m_dOpenPrice"]:.2f}----个股成交量：{(tick[code]["amount"] - accountObj["amount"]) / 100}手 ---- 个股成交额：{(tick[code]["amount"] - accountObj["amount"]) * tick[code]["lastPrice"] / 10000:.4f} 万  换手率{((tick[code]["amount"] - accountObj["amount"]) / 100) / tick[code]["amount"] * 100:.4f}%')
        predict = decider1.predict()
        print_str = str(predict) if predict is False else str(predict) + "!!!!!!!!!!!"
        print(print_str)
        if (tick[code]["amount"] - accountObj["amount"]) / 100 > 8000:
            if accountObj["bidVol"] > sum(tick[code]["bidVol"]) * 1.5:
                print("出现万手哥砸盘！！！！！！！！！！不好！！！！！！！！！不好！！！！！！！！！！！！！！！！！！！！！！！不好！！！！！！！！！！！！！！！！")
                print(tick[code]['lastPrice'] * (tick[code]["amount"] - accountObj["amount"]) / 10000)
            else:
                print("出现万手哥！！！！！！！！！！万手哥点火！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！")
                print(tick[code]['lastPrice'] * (tick[code]["amount"] - accountObj["amount"]) / 10000)
            # SELL----------------------------------------------------------------------------------------------------------------------------------

            if sum(tick[code]['askVol']) * 100 >= accountObj['positions']['m_nVolume']:
                accountObj['positions']['m_nVolume']  # 持股数量
                print(f"卖出:{accountObj['positions']['m_nVolume']}")
                passorder(24, 1101, account, code, 5, -1, accountObj['positions']['m_nVolume'], C)  # 23买 # 24卖
        elif (tick[code]["amount"] - accountObj["amount"]) / 100 > 5000:
            if accountObj["bidVol"] > sum(tick[code]["bidVol"]) * 1.5:
                print("出现千手~~~砸盘！！！！！！！！！！不好！！！！！！！！！不好！！！！！！！！！！！！！！！！！！！！！！！不好！！！！！！！！！！！！！！！！")
            else:
                print("出现千手~~~交易  注意波动--------------------------~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

        if sum(tick[code]["askVol"]) * 4 < sum(tick[code]["bidVol"]):
            print("空方力量大幅减少-----------------------股价可能往上走")  # 部分失真
        elif sum(tick[code]["bidVol"]) * 4 < sum(tick[code]["askVol"]):
            print("承接方力量大幅减少------------------谨慎下砸------------可能是短期高、低点")  # 部分失真
        accountObj["bidVol"] = sum(tick[code]["bidVol"])
    accountObj["amount"] = tick[code]["amount"]


# for code in ['000001.SH', '399001.SZ']:
#	passorder(23, 1101, account, code, 5, -1, accountObj['max_use_bullet'], C)  # 23买 # 24卖
#	tick = C.get_full_tick([code])
#	print(tick[code])
#	print(f'买入:{code},数量:{accountObj["max_use_bullet"]}')


def after_init(C):
    # # 使用smart_algo_passorder 下单
    # print("使用smart_algo_passorder 下单")
    pass


def query_info(C):
    """
    用户管理
    """
    account = '8881667160'
    orders = get_trade_detail_data(account, 'stock', 'order')
    # for o in orders:
    #	print(f'股票代码: {o.m_strInstrumentID}, 市场类型: {o.m_strExchangeID}, 证券名称: {o.m_strInstrumentName}, 买卖方向: {o.m_nOffsetFlag}',
    #	f'委托数量: {o.m_nVolumeTotalOriginal}, 成交均价: {o.m_dTradedPrice}, 成交数量: {o.m_nVolumeTraded}, 成交金额:{o.m_dTradeAmount}')

    deals = get_trade_detail_data(account, 'stock', 'deal')
    # for dt in deals:
    #	print(f'股票代码: {dt.m_strInstrumentID}, 市场类型: {dt.m_strExchangeID}, 证券名称: {dt.m_strInstrumentName}, 买卖方向: {dt.m_nOffsetFlag}',
    #	f'成交价格: {dt.m_dPrice}, 成交数量: {dt.m_nVolume}, 成交金额: {dt.m_dTradeAmount}')

    positions = get_trade_detail_data(account, 'stock', 'position')
    # for dt in positions:
    #	print(f'股票代码: {dt.m_strInstrumentID}, 市场类型: {dt.m_strExchangeID}, 证券名称: {dt.m_strInstrumentName}, 持仓量: {dt.m_nVolume}, 可用数量: {dt.m_nCanUseVolume}',
    #	f'成本价: {dt.m_dOpenPrice:.2f}, 市值: {dt.m_dInstrumentValue:.2f}, 持仓成本: {dt.m_dPositionCost:.2f}, 盈亏: {dt.m_dPositionProfit:.2f}')

    accounts = get_trade_detail_data(account, 'stock', 'account')
    # for dt in accounts:
    #	print(f'总资产: {dt.m_dBalance:.2f}, 净资产: {dt.m_dAssureAsset:.2f}, 总市值: {dt.m_dInstrumentValue:.2f}',
    #	f'总负债: {dt.m_dTotalDebit:.2f}, 可用金额: {dt.m_dAvailable:.2f}, 盈亏: {dt.m_dPositionProfit:.2f}',
    #	f'')

    # orders:
    for order in orders:
        o = {}
        o['m_strInstrumentID'] = order.m_strInstrumentID
        o['m_strInstrumentName'] = order.m_strInstrumentName
        o['m_nOffsetFlag'] = order.m_nOffsetFlag  # 卖卖
        o['m_nVolumeTotalOriginal'] = order.m_nVolumeTotalOriginal  # 委托数量
        o['m_dTradedPrice'] = order.m_dTradedPrice  # 成交均价
        o['m_nVolumeTraded'] = order.m_nVolumeTraded  # 成交数量
        o['m_dTradeAmount'] = order.m_dTradeAmount  # 成交金额
        accountObj["orders"] = o
    # deals:
    for deal in deals:
        o = {}
        o['m_strInstrumentID'] = deal.m_strInstrumentID
        o['m_strInstrumentName'] = deal.m_strInstrumentName
        o['m_nOffsetFlag'] = deal.m_nOffsetFlag  # 卖卖
        o['m_dPrice'] = deal.m_dPrice  # 成交价格
        o['m_nVolume'] = deal.m_nVolume  # 成交数量
        o['m_dTradeAmount'] = deal.m_dTradeAmount  # 成交金额
        if deal.m_nOffsetFlag == 48:
            accountObj['code_list'] = [gp_type_szsh(deal.m_strInstrumentID)]
        # accountObj['code_list'].__add__(deal.m_strInstrumentID)
        else:
            accountObj['code_list'] = tuple(list(accountObj['code_list']).remove(deal.m_strInstrumentID)) if deal.m_strInstrumentID in list(accountObj['code_list']) else accountObj['code_list']
        accountObj["deals"] = o
    # positions:
    for position in positions:
        o = {}
        o['m_strInstrumentID'] = position.m_strInstrumentID
        o['m_strInstrumentName'] = position.m_strInstrumentName
        o['m_nVolume'] = position.m_nVolume  # 持仓量
        o['m_nCanUseVolume'] = position.m_nCanUseVolume  # 可用数量
        o['m_dOpenPrice'] = position.m_dOpenPrice  # 成本价
        o['m_dInstrumentValue'] = position.m_dInstrumentValue  # 市值
        o['m_dPositionCost'] = position.m_dPositionCost  # 持仓成本
        o['m_dPositionProfit'] = position.m_dPositionProfit  # 盈亏
        accountObj["positions"] = o

    # accounts:
    for account in accounts:
        o = {}
        o['m_dBalance'] = account.m_dBalance  # 总资产
        o['m_dAssureAsset'] = account.m_dAssureAsset  # 净资产
        o['m_dInstrumentValue'] = account.m_dInstrumentValue  # 总市值
        o['m_dAvailable'] = account.m_dAvailable  # 可用金额
        o['m_dPositionProfit'] = account.m_dPositionProfit  # 盈亏
        accountObj["accounts"] = o

    return orders, deals, positions, accounts


def show_data(data):
    tdata = {}
    for ar in dir(data):
        if ar[:2] != 'm_': continue
        try:
            tdata[ar] = data.__getattribute__(ar)
        except:
            tdata[ar] = '<CanNotConvert>'
    return tdata


def account_callback(ContextInfo, accountInfo):
    print('资金账号状态变化主推:')
    print(show_data(accountInfo))

