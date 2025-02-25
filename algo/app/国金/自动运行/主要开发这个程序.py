# encoding:gbk
'''
�����������趨�ý��׵Ĺ�Ʊ���ӣ�Ȼ�����ָ����CCIָ�����жϳ���ͳ���
���г���ͳ�������ʱ�����������趨�õĹ�Ʊ����
'''
import pandas as pd
import numpy as np
import talib
import requests
import json
from xtquant import xtdata

account = 'xxx'
max_rate = 0.5
url = "http://127.0.0.1:8000"

accountObj = {'code_list': ('002933.SZ'),  #
				'trading_snapshot': [],  #
				'orders': {},  #
				'deals': {},  #
				'positions': {},  #
				'accounts': {},  #
				'financial_status': 0.0,  #
				'amount': 0,  #
				'bidVol': 0,  # ������
				'sell_ask': 0,  # ������
				'buy_ask': 0,  # ������
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


def moving_average(prices, period):
	"""
	�����ƶ�ƽ���ߵĺ���
	"""
	if len(prices) < period:
		return np.zeros(period)
	else:
		return np.mean(prices[-period:], axis=0)


def calculateMACD(close_prices):
	ema12 = close_prices.ewm(span=12).mean()
	ema26 = close_prices.ewm(span=26).mean()
	diff = ema12 - ema26
	dea = diff.ewm(span=9).mean()
	macd = (diff - dea) * 2
	return macd


class timeDecided:
	def __init__(self):
		self.min_price_list = []
		self.min_big_price_list = []
		self.Fmin_price_list = []
		self.Fmin_big_price_list = []
		self.all_price_list = []
		self.all_big_price_list = []
		self.period = 20
		self.prices_sell = []  # ƽ����
		self.prices_buy = []  # ƽ����
		# RSI���ǿ��ָ��
		self.RSI_period = 14
		self.RSI_data_sell = []
		self.RSI_data_buy = []

	def addObj(self, priceObj):
		self.all_price_list.append(priceObj)
		code = list(priceObj.keys())[0]
		# ��ȱһ������ѹ���Ĺ���
		sell_ask = sum(priceObj[code]['askPrice'])
		buy_ask = sum(priceObj[code]['bidPrice'])

		# RSI
		if len(self.RSI_data_sell) > self.RSI_period:
			del self.RSI_data_sell[0]
			del self.RSI_data_buy[0]
		else:
			self.RSI_data_sell.append(sell_ask)
			self.RSI_data_buy.append(buy_ask)

		if len(self.prices_sell) > self.period and len(self.prices_buy) > self.period:
			del self.prices_sell[0]
			del self.prices_buy[0]
		else:
			self.prices_sell.append(sell_ask)
			self.prices_buy.append(buy_ask)

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
		transaction_volume = (priceObj[code]["amount"] - accountObj["amount"]) * priceObj[code]["lastPrice"] / 10000  # ��
		if (priceObj[code]["amount"] - accountObj["amount"]) / 100 > 18000:
			self.min_big_price_list.append(10)
			self.Fmin_big_price_list.append(10)
			self.all_big_price_list.append(10)
		elif (priceObj[code]["amount"] - accountObj["amount"]) / 100 > 10000:
			self.min_big_price_list.append(5)
			self.Fmin_big_price_list.append(5)
			self.all_big_price_list.append(5)
		elif (priceObj[code]["amount"] - accountObj["amount"]) / 100 > 6000:
			self.min_big_price_list.append(4)
			self.Fmin_big_price_list.append(4)
			self.all_big_price_list.append(4)
		elif (priceObj[code]["amount"] - accountObj["amount"]) / 100 > 3000:
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
		print(f'���ӷ���:{sum(self.min_big_price_list)},����ӷ���:{sum(self.Fmin_big_price_list)}')
		sell = moving_average(self.prices_sell, self.period)
		buy = moving_average(self.prices_buy, self.period)
		print(f'moving-----sell:{sell}-----buy:{buy}')

		# RSI
		# rsi_sell = talib.RSI(self.RSI_data_sell, self.RSI_period)
		# rsi_buy = talib.RSI(self.RSI_data_buy, self.RSI_period)
		# print(f'RSI-----rsi_sell{rsi_sell}------rsi_buy{rsi_buy}')

		if sum(self.min_big_price_list) > 13 and sum(self.min_big_price_list[int(len(self.min_big_price_list) / 2):]) > 18:
			if sum(self.Fmin_big_price_list) > 25:
				return True
		if sum(self.min_big_price_list) > 50 and sum(self.Fmin_big_price_list) > 150:
			return True
		return False


class a():
	pass


def on_data(datas):
	for stock_code in datas:
		print(stock_code, datas[stock_code])


def on_disconnected(self):
	"""
	���ӶϿ�
	:return:
	"""
	print("���ӶϿ�")


def on_stock_order(self, order):
	"""
	ί�лر�����
	:param order: XtOrder����
	:return:
	"""
	print("ί�лر�����:")
	print(order.stock_code, order.order_status, order.order_sysid)


def on_stock_asset(self, asset):
	"""
	�ʽ�䶯����
	:param asset: XtAsset����
	:return:
	"""
	print("�ʽ�䶯����")
	print(asset.account_id, asset.cash, asset.total_asset)


def on_stock_position(self, position):
	"""
	�ֱֲ䶯����
	:param position: XtPosition����
	:return:
	"""
	print("�ֱֲ䶯����")
	print(position.stock_code, position.volume)


def on_order_error(self, order_error):
	"""
	ί��ʧ������
	:param order_error:XtOrderError ����
	:return:
	"""
	print("ί��ʧ������")
	print(order_error.order_id, order_error.error_id, order_error.error_msg)


def on_cancel_error(self, cancel_error):
	"""
	����ʧ������
	:param cancel_error: XtCancelError ����
	:return:
	"""
	print("����ʧ������")
	print(cancel_error.order_id, cancel_error.error_id, cancel_error.error_msg)


def on_order_stock_async_response(self, response):
	"""
	�첽�µ��ر�����
	:param response: XtOrderResponse ����
	:return:
	"""
	print("�첽�µ��ر�����")
	print(response.account_id, response.order_id, response.seq)


def on_account_status(self, status):
	"""
	:param response: XtAccountStatus ����
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
	orders, deals, positions, accounts = query_info(C)  # ��ѯ�˻���Ϣ
	C.set_account = account


# orders:
# print(f'{accountObj["position"]["m_strInstrumentName"]}:{accountObj["position"]["m_nVolume"]}')
def postsell(orders, deals, positions, accounts):
	# orders
	order_list = []
	for order in orders:
		o = {}
		o['m_strInstrumentID'] = order.m_strInstrumentID
		o['m_strInstrumentName'] = order.m_strInstrumentName
		o['m_nOffsetFlag'] = order.m_nOffsetFlag  # ����
		o['m_nVolumeTotalOriginal'] = order.m_nVolumeTotalOriginal  # ί������
		o['m_dTradedPrice'] = order.m_dTradedPrice  # �ɽ�����
		o['m_nVolumeTraded'] = order.m_nVolumeTraded  # �ɽ�����
		o['m_dTradeAmount'] = order.m_dTradeAmount  # �ɽ����
		# print(o)
		order_list.append(o)
	# deals
	deal_list = []
	for deal in deals:
		o = {}
		o['m_strInstrumentID'] = deal.m_strInstrumentID
		o['m_strInstrumentName'] = deal.m_strInstrumentName
		o['m_nOffsetFlag'] = deal.m_nOffsetFlag  # ����
		o['m_dPrice'] = deal.m_dPrice  # �ɽ��۸�
		o['m_nVolume'] = deal.m_nVolume  # �ɽ�����
		o['m_dTradeAmount'] = deal.m_dTradeAmount  # �ɽ����
		# print(o)
		deal_list.append(o)
	# positions
	position_list = []
	for position in positions:
		o = {}
		o['m_strInstrumentID'] = position.m_strInstrumentID
		o['m_strInstrumentName'] = position.m_strInstrumentName
		o['m_nVolume'] = position.m_nVolume  # �ֲ���
		o['m_nCanUseVolume'] = position.m_nCanUseVolume  # ��������
		o['m_dOpenPrice'] = position.m_dOpenPrice  # �ɱ���
		o['m_dInstrumentValue'] = position.m_dInstrumentValue  # ��ֵ
		o['m_dPositionCost'] = position.m_dPositionCost  # �ֲֳɱ�
		o['m_dPositionProfit'] = position.m_dPositionProfit  # ӯ��
		# print(o)
		position_list.append(o)
	# accounts
	account_list = []
	for account in accounts:
		o = {}
		o['m_dBalance'] = account.m_dBalance  # ���ʲ�
		o['m_dAssureAsset'] = account.m_dAssureAsset  # ���ʲ�
		o['m_dInstrumentValue'] = account.m_dInstrumentValue  # ����ֵ
		o['m_dAvailable'] = account.m_dAvailable  # ���ý��
		o['m_dPositionProfit'] = account.m_dPositionProfit  # ӯ��
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
	orders, deals, positions, accounts = query_info(C)  # ��ѯ�˻���Ϣ

	accountObj['all_bullet'] = accounts[0].m_dBalance
	accountObj['bullet'] = accounts[0].m_dAvailable
	accountObj['max_use_bullet'] = accounts[0].m_dBalance * max_rate
	# print('accountObj:'+str(accountObj['code_list']))
	result = postsell(orders, deals, positions, accounts)
	# ���㱱��������
	north_finance_info = C.get_north_finance_change('1m')
	north_finance_info_value = C.get_north_finance_change('1m')[list(C.get_north_finance_change('1m').keys())[0]]
	all_buy = float(north_finance_info_value['hgtNorthBuyMoney'] + north_finance_info_value['hgtSouthBuyMoney'] + north_finance_info_value['sgtNorthBuyMoney'] + north_finance_info_value['sgtSouthBuyMoney']) / 100000000
	all_sell = float(north_finance_info_value['hgtNorthSellMoney'] + north_finance_info_value['hgtSouthSellMoney'] + north_finance_info_value['sgtNorthSellMoney'] + north_finance_info_value['sgtSouthSellMoney']) / 100000000

	# ������̳ɽ���
	A_all = 0
	for code in ['000001.SH', '399001.SZ']:
		tick = C.get_full_tick([code])
		A_all = A_all + tick[code]['amount']
	print("-" * 170)
	print(f'������:{all_buy}��-----������:{all_sell}----�ɽ���:{A_all / 100000000}')
	if accountObj["financial_status"] != 0:
		print(f'���̱䶯��{A_all / 100000000 - accountObj["financial_status"]:.2f}��,�ٷֱ�:{(A_all / 100000000) / (accountObj["financial_status"]) / 100:.2f}%')
	accountObj['financial_status'] = A_all / 100000000
	transaction_volume = (tick[code]["amount"] - accountObj["amount"]) * tick[code]["lastPrice"] / 10000  # ��
	# accountObj["positions"]['m_dInstrumentValue']		# ����
	# accountObj['code_list'] = eval(getbuy_codes().text)
	print(accountObj["positions"])
	if accountObj["positions"]['m_strInstrumentName'] == 'GC007': return 				# �������ǹ�ծ��ʲô������
	code = gp_type_szsh(accountObj["positions"]['m_strInstrumentID'])
	tick = C.get_full_tick(code)
	if tick[code]["amount"] != 0:
		print(f'�ɱ���:{accountObj["positions"]["m_dOpenPrice"]:.2f}--------- ������{((tick[code]["amount"] - accountObj["amount"]) / 100) / tick[code]["amount"] * 100:.4f}%')
		print(f'��:{tick[code]["askPrice"]}----{tick[code]["askVol"]}---- ��:{sum(tick[code]["askVol"])} ----���:{[str(tick[code]["askPrice"][i] * tick[code]["askVol"][i] * 100 / 10000) + "��" for i in range(len(tick[code]["askPrice"]))]}----��:{sum([tick[code]["askPrice"][i] * tick[code]["askVol"][i] * 100 / 10000 for i in range(len(tick[code]["askPrice"]))]):.2f}��')
		print(f'��:{tick[code]["bidPrice"]}----{tick[code]["bidVol"]}---- ��:{sum(tick[code]["bidVol"])} ----���:{[str(tick[code]["bidPrice"][i] * tick[code]["bidVol"][i] * 100 / 10000) + "��" for i in range(len(tick[code]["bidPrice"]))]}----��:{sum([tick[code]["bidPrice"][i] * tick[code]["bidVol"][i] * 100 / 10000 for i in range(len(tick[code]["bidPrice"]))]):.2f}��')
	if accountObj['amount'] != 0:
		(tick[code]["amount"] - accountObj["amount"]) * tick[code]["lastPrice"] / 10000
		print(f"open:{tick[code]['open']}----high:{tick[code]['high']}----low:{tick[code]['low']}----lastClose:{tick[code]['lastClose']}")
		decider1.addObj(tick)
		print(f'�ɱ���:{accountObj["positions"]["m_dOpenPrice"]:.2f}----���ɳɽ�����{(tick[code]["amount"] - accountObj["amount"]) / 100}�� ---- ���ɳɽ��{(tick[code]["amount"] - accountObj["amount"]) * tick[code]["lastPrice"] / 10000:.4f} ��  ������{((tick[code]["amount"] - accountObj["amount"]) / 100) / tick[code]["amount"] * 100:.4f}%')
		predict = decider1.predict()
		print_str = str(predict) if predict is False else str(predict) + "!!!!!!!!!!!"
		print(print_str)
		if (tick[code]["amount"] - accountObj["amount"]) / 100 > 8000:
			if accountObj["bidVol"] > sum(tick[code]["bidVol"]) * 1.5:
				print("�������ָ����̣����������������������ã��������������������ã������������������������������������������������ã�������������������������������")
				print(tick[code]['lastPrice'] * (tick[code]["amount"] - accountObj["amount"]) / 10000)
			else:
				print("�������ָ磡���������������������ָ��𣡣���������������������������������������������������������������������������������������������")
				print(tick[code]['lastPrice'] * (tick[code]["amount"] - accountObj["amount"]) / 10000)
			# SELL----------------------------------------------------------------------------------------------------------------------------------

			if sum(tick[code]['askVol']) * 100 >= accountObj['positions']['m_nVolume']:
				accountObj['positions']['m_nVolume']  # �ֹ�����
				print(f"����:{accountObj['positions']['m_nVolume']}")
				passorder(24, 1101, account, code, 5, -1, accountObj['positions']['m_nVolume'], C)  # 23�� # 24��
		elif (tick[code]["amount"] - accountObj["amount"]) / 100 > 5000:
			if accountObj["bidVol"] > sum(tick[code]["bidVol"]) * 1.5:
				print("����ǧ��~~~���̣����������������������ã��������������������ã������������������������������������������������ã�������������������������������")
			else:
				print("����ǧ��~~~����  ע�Ⲩ��--------------------------~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

		if sum(tick[code]["askVol"]) * 4 < sum(tick[code]["bidVol"]):
			print("�շ������������-----------------------�ɼۿ���������")  # ����ʧ��
		elif sum(tick[code]["bidVol"]) * 4 < sum(tick[code]["askVol"]):
			print("�нӷ������������------------------��������------------�����Ƕ��ڸߡ��͵�")  # ����ʧ��
		accountObj["bidVol"] = sum(tick[code]["bidVol"])
	accountObj["amount"] = tick[code]["amount"]


# for code in ['000001.SH', '399001.SZ']:
#	passorder(23, 1101, account, code, 5, -1, accountObj['max_use_bullet'], C)  # 23�� # 24��
#	tick = C.get_full_tick([code])
#	print(tick[code])
#	print(f'����:{code},����:{accountObj["max_use_bullet"]}')


def after_init(C):
	# # ʹ��smart_algo_passorder �µ�
	# print("ʹ��smart_algo_passorder �µ�")
	pass


def query_info(C):
	"""
	�û�����
	"""
	account = 'xxx'
	orders = get_trade_detail_data(account, 'stock', 'order')
	# for o in orders:
	#	print(f'��Ʊ����: {o.m_strInstrumentID}, �г�����: {o.m_strExchangeID}, ֤ȯ����: {o.m_strInstrumentName}, ��������: {o.m_nOffsetFlag}',
	#	f'ί������: {o.m_nVolumeTotalOriginal}, �ɽ�����: {o.m_dTradedPrice}, �ɽ�����: {o.m_nVolumeTraded}, �ɽ����:{o.m_dTradeAmount}')

	deals = get_trade_detail_data(account, 'stock', 'deal')
	# for dt in deals:
	#	print(f'��Ʊ����: {dt.m_strInstrumentID}, �г�����: {dt.m_strExchangeID}, ֤ȯ����: {dt.m_strInstrumentName}, ��������: {dt.m_nOffsetFlag}',
	#	f'�ɽ��۸�: {dt.m_dPrice}, �ɽ�����: {dt.m_nVolume}, �ɽ����: {dt.m_dTradeAmount}')

	positions = get_trade_detail_data(account, 'stock', 'position')
	# for dt in positions:
	#	print(f'��Ʊ����: {dt.m_strInstrumentID}, �г�����: {dt.m_strExchangeID}, ֤ȯ����: {dt.m_strInstrumentName}, �ֲ���: {dt.m_nVolume}, ��������: {dt.m_nCanUseVolume}',
	#	f'�ɱ���: {dt.m_dOpenPrice:.2f}, ��ֵ: {dt.m_dInstrumentValue:.2f}, �ֲֳɱ�: {dt.m_dPositionCost:.2f}, ӯ��: {dt.m_dPositionProfit:.2f}')

	accounts = get_trade_detail_data(account, 'stock', 'account')
	# for dt in accounts:
	#	print(f'���ʲ�: {dt.m_dBalance:.2f}, ���ʲ�: {dt.m_dAssureAsset:.2f}, ����ֵ: {dt.m_dInstrumentValue:.2f}',
	#	f'�ܸ�ծ: {dt.m_dTotalDebit:.2f}, ���ý��: {dt.m_dAvailable:.2f}, ӯ��: {dt.m_dPositionProfit:.2f}',
	#	f'')

	# orders:
	for order in orders:
		o = {}
		o['m_strInstrumentID'] = order.m_strInstrumentID
		o['m_strInstrumentName'] = order.m_strInstrumentName if order.m_strInstrumentName is not None else order.m_strInstrumentName
		o['m_nOffsetFlag'] = order.m_nOffsetFlag  # ����
		o['m_nVolumeTotalOriginal'] = order.m_nVolumeTotalOriginal  # ί������
		o['m_dTradedPrice'] = order.m_dTradedPrice  # �ɽ�����
		o['m_nVolumeTraded'] = order.m_nVolumeTraded  # �ɽ�����
		o['m_dTradeAmount'] = order.m_dTradeAmount  # �ɽ����
		accountObj["orders"] = o
	# deals:
	for deal in deals:
		o = {}
		o['m_strInstrumentID'] = deal.m_strInstrumentID
		o['m_strInstrumentName'] = deal.m_strInstrumentName
		o['m_nOffsetFlag'] = deal.m_nOffsetFlag  # ����
		o['m_dPrice'] = deal.m_dPrice  # �ɽ��۸�
		o['m_nVolume'] = deal.m_nVolume  # �ɽ�����
		o['m_dTradeAmount'] = deal.m_dTradeAmount  # �ɽ����
		if deal.m_nOffsetFlag == 48:
			accountObj['code_list'] = [gp_type_szsh(deal.m_strInstrumentID)]
		# accountObj['code_list'].__add__(deal.m_strInstrumentID)
		else:
			accountObj['code_list'] = tuple(list(accountObj['code_list']).remove(deal.m_strInstrumentID)) if deal.m_strInstrumentID in list(accountObj['code_list']) else accountObj['code_list']
		accountObj["deals"] = o
	o = {}
	o['m_strInstrumentID'] = positions[0].m_strInstrumentID
	o['m_strInstrumentName'] = positions[0].m_strInstrumentName
	o['m_nVolume'] = positions[0].m_nVolume  # �ֲ���
	o['m_nCanUseVolume'] = positions[0].m_nCanUseVolume  # ��������
	o['m_dOpenPrice'] = positions[0].m_dOpenPrice  # �ɱ���
	o['m_dInstrumentValue'] = positions[0].m_dInstrumentValue  # ��ֵ
	o['m_dPositionCost'] = positions[0].m_dPositionCost  # �ֲֳɱ�
	o['m_dPositionProfit'] = positions[0].m_dPositionProfit  # ӯ��
	# print(f'position:{o}')
	accountObj["positions"] = o
	# accounts:
	for account in accounts:
		o = {}
		o['m_dBalance'] = account.m_dBalance  # ���ʲ�
		o['m_dAssureAsset'] = account.m_dAssureAsset  # ���ʲ�
		o['m_dInstrumentValue'] = account.m_dInstrumentValue  # ����ֵ
		o['m_dAvailable'] = account.m_dAvailable  # ���ý��
		o['m_dPositionProfit'] = account.m_dPositionProfit  # ӯ��
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
	print('�ʽ��˺�״̬�仯����:')
	print(show_data(accountInfo))


def deal_callback(ContextInfo, dealInfo):
	print(show_data(dealInfo))
