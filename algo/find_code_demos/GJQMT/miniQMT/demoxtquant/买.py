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
from collections import deque

account = '8881667160'
max_rate = 0.5
url = "http://127.0.0.1:9000"

accountObj = {
			'code_list': ('002933.SZ'),  #
			'trading_snapshot': [],  #
			'orders': {},  #
			'deals': {},  #
			'positions': {},  #
			'accounts': {},  #
			'financial_status': 0.0,  #
			'amount': 0,  #
			'bidVol': 0,  # 购买手
			'sell_ask': 0,  # 购买手
			'buy_ask': 0,  # 购买手
			}

class RealTimeTechnicalIndicators:
	def __init__(self, initial_data):
		self.data = initial_data
		self.windows = {
			'cci': deque(maxlen=14),
			'bollinger_bands': deque(maxlen=20),
			'macd': {
				'fast_ema': deque(maxlen=12),
				'slow_ema': deque(maxlen=26),
				'signal_ema': deque(maxlen=9)
			},
			'kdj': deque(maxlen=9),
			'rsi': deque(maxlen=14),
			'roc': deque(maxlen=12),
			'obv': deque(maxlen=1000),  # 你可以根据需要调整长度
			'dmi': {
				'tr': deque(maxlen=14),
				'plus_dm': deque(maxlen=14),
				'minus_dm': deque(maxlen=14)
			},
			'atr': deque(maxlen=14),
			'wr': deque(maxlen=14),
			'psy': deque(maxlen=12),
			'sar': {
				'high': deque(maxlen=1000),
				'low': deque(maxlen=1000),
				'sar': deque(maxlen=1000),
				'ep': deque(maxlen=1000),
				'af': deque(maxlen=1000)
			},
			'mfi': deque(maxlen=14),
			'adl': deque(maxlen=1000)
		}

	def update_data(self, new_data):
		"""
		更新数据并重新计算所有指标
		:param new_data: 新的数据点，字典格式 { 'High': value, 'Low': value, 'Close': value, 'Volume': value }
		"""
		self.data = self.data.append(new_data, ignore_index=True)
		self._update_windows(new_data)
		self.cci()
		self.bollinger_bands()
		self.macd()
		self.kdj()
		self.rsi()
		self.roc()
		self.obv()
		self.dmi()
		self.atr()
		self.wr()
		self.psy()
		self.sar()
		self.mfi()
		self.adl()

	def _update_windows(self, new_data):
		"""
		更新所有滚动窗口
		"""
		self.windows['cci'].append((new_data['High'], new_data['Low'], new_data['Close']))
		self.windows['bollinger_bands'].append(new_data['Close'])
		self.windows['macd']['fast_ema'].append(new_data['Close'])
		self.windows['macd']['slow_ema'].append(new_data['Close'])
		self.windows['macd']['signal_ema'].append(new_data['Close'])
		self.windows['kdj'].append((new_data['High'], new_data['Low'], new_data['Close']))
		self.windows['rsi'].append(new_data['Close'])
		self.windows['roc'].append(new_data['Close'])
		self.windows['obv'].append((new_data['Close'], new_data['Volume']))
		self.windows['dmi']['tr'].append((new_data['High'], new_data['Low'], new_data['Close']))
		self.windows['dmi']['plus_dm'].append((new_data['High'], new_data['Low'], new_data['Close']))
		self.windows['dmi']['minus_dm'].append((new_data['High'], new_data['Low'], new_data['Close']))
		self.windows['atr'].append((new_data['High'], new_data['Low'], new_data['Close']))
		self.windows['wr'].append((new_data['High'], new_data['Low'], new_data['Close']))
		self.windows['psy'].append(new_data['Close'])
		self.windows['sar']['high'].append(new_data['High'])
		self.windows['sar']['low'].append(new_data['Low'])
		self.windows['sar']['sar'].append(0)  # 初始值
		self.windows['sar']['ep'].append(new_data['Close'])
		self.windows['sar']['af'].append(0.02)  # 初始加速因子
		self.windows['mfi'].append((new_data['High'], new_data['Low'], new_data['Close'], new_data['Volume']))
		self.windows['adl'].append((new_data['Close'], new_data['Low'], new_data['High'], new_data['Volume']))

	def cci(self, timeperiod=14, constant=0.015):
		typical_prices = [(h + l + c) / 3 for h, l, c in self.windows['cci']]
		mean_typical_price = np.mean(typical_prices)
		mean_deviation = np.mean([np.abs(tp - mean_typical_price) for tp in typical_prices])
		self.data.loc[self.data.index[-1], 'CCI'] = (typical_prices[-1] - mean_typical_price) / (constant * mean_deviation)

	def bollinger_bands(self, timeperiod=20, nbdevup=2, nbdevdn=2):
		rolling_mean = np.mean(self.windows['bollinger_bands'])
		rolling_std = np.std(self.windows['bollinger_bands'])
		self.data.loc[self.data.index[-1], 'Upper_Band'] = rolling_mean + (rolling_std * nbdevup)
		self.data.loc[self.data.index[-1], 'Lower_Band'] = rolling_mean - (rolling_std * nbdevdn)
		self.data.loc[self.data.index[-1], 'Middle_Band'] = rolling_mean

	def macd(self, fastperiod=12, slowperiod=26, signalperiod=9):
		ema_fast = pd.Series(self.windows['macd']['fast_ema']).ewm(span=fastperiod, adjust=False).mean().iloc[-1]
		ema_slow = pd.Series(self.windows['macd']['slow_ema']).ewm(span=slowperiod, adjust=False).mean().iloc[-1]
		macd_line = ema_fast - ema_slow
		signal_line = pd.Series(self.windows['macd']['signal_ema']).ewm(span=signalperiod, adjust=False).mean().iloc[-1]
		self.data.loc[self.data.index[-1], 'MACD'] = macd_line
		self.data.loc[self.data.index[-1], 'Signal'] = signal_line
		self.data.loc[self.data.index[-1], 'Hist'] = macd_line - signal_line

	def kdj(self, n=9, m1=3, m2=3):
		high_list = [h for h, l, c in self.windows['kdj']]
		low_list = [l for h, l, c in self.windows['kdj']]
		close_list = [c for h, l, c in self.windows['kdj']]
		rsv = (close_list[-1] - min(low_list)) / (max(high_list) - min(low_list)) * 100
		k = rsv if len(self.data) <= n else self.data['K'].iloc[-2] * (m1 - 1) / m1 + rsv / m1
		d = k if len(self.data) <= n else self.data['D'].iloc[-2] * (m2 - 1) / m2 + k / m2
		j = 3 * k - 2 * d
		self.data.loc[self.data.index[-1], 'K'] = k
		self.data.loc[self.data.index[-1], 'D'] = d
		self.data.loc[self.data.index[-1], 'J'] = j

	def rsi(self, timeperiod=14):
		closes = list(self.windows['rsi'])
		gains = [c - closes[i-1] if c > closes[i-1] else 0 for i, c in enumerate(closes)][1:]
		losses = [closes[i-1] - c if c < closes[i-1] else 0 for i, c in enumerate(closes)][1:]
		avg_gain = np.mean(gains)
		avg_loss = np.mean(losses)
		rs = avg_gain / avg_loss if avg_loss != 0 else 0
		self.data.loc[self.data.index[-1], 'RSI'] = 100 - (100 / (1 + rs))

	def roc(self, timeperiod=12):
		closes = list(self.windows['roc'])
		self.data.loc[self.data.index[-1], 'ROC'] = (closes[-1] - closes[-timeperiod-1]) / closes[-timeperiod-1] * 100

	def obv(self):
		closes = [c for c, v in self.windows['obv']]
		volumes = [v for c, v in self.windows['obv']]
		obv = [volumes[0]]
		for i in range(1, len(closes)):
			if closes[i] > closes[i-1]:
				obv.append(obv[-1] + volumes[i])
			elif closes[i] < closes[i-1]:
				obv.append(obv[-1] - volumes[i])
			else:
				obv.append(obv[-1])
		self.data.loc[self.data.index[-1], 'OBV'] = obv[-1]

	def dmi(self, timeperiod=14):
		highs = [h for h, l, c in self.windows['dmi']['tr']]
		lows = [l for h, l, c in self.windows['dmi']['tr']]
		closes = [c for h, l, c in self.windows['dmi']['tr']]
		high_diff = np.diff(highs)
		low_diff = -np.diff(lows)
		
		plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
		minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
		
		tr = np.maximum(np.maximum(np.diff(highs), np.abs(np.diff(lows))), np.abs(np.diff(closes)))
		
		atr = np.mean(tr)
		plus_di = 100 * (np.sum(plus_dm) / atr)
		minus_di = 100 * (np.sum(minus_dm) / atr)
		
		adx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
		
		self.data.loc[self.data.index[-1], '+DI'] = plus_di
		self.data.loc[self.data.index[-1], '-DI'] = minus_di
		self.data.loc[self.data.index[-1], 'ADX'] = adx

	def atr(self, timeperiod=14):
		highs = [h for h, l, c in self.windows['atr']]
		lows = [l for h, l, c in self.windows['atr']]
		closes = [c for h, l, c in self.windows['atr']]
		
		tr = np.maximum(np.maximum(np.diff(highs), np.abs(np.diff(lows))), np.abs(np.diff(closes)))
		self.data.loc[self.data.index[-1], 'ATR'] = np.mean(tr)

	def wr(self, timeperiod=14):
		highs = [h for h, l, c in self.windows['wr']]
		lows = [l for h, l, c in self.windows['wr']]
		closes = [c for h, l, c in self.windows['wr']]
		
		highest_high = max(highs)
		lowest_low = min(lows)
		self.data.loc[self.data.index[-1], 'WR'] = -100 * ((highest_high - closes[-1]) / (highest_high - lowest_low))

	def psy(self, timeperiod=12):
		closes = list(self.windows['psy'])
		positive_close = sum(1 for c in closes if c > closes[closes.index(c)-1])
		self.data.loc[self.data.index[-1], 'PSY'] = positive_close / timeperiod * 100

	def sar(self, acceleration=0.02, maximum=0.2):
		highs = list(self.windows['sar']['high'])
		lows = list(self.windows['sar']['low'])
		sar = list(self.windows['sar']['sar'])
		ep = list(self.windows['sar']['ep'])
		af = list(self.windows['sar']['af'])
		
		if highs[-1] > ep[-1]:
			ep[-1] = highs[-1]
			af[-1] = min(af[-1] + acceleration, maximum)
			sar[-1] = max(sar[-2] + af[-1] * (ep[-1] - sar[-2]), min(lows[:-1]))
		else:
			ep[-1] = lows[-1]
			af[-1] = acceleration
			sar[-1] = min(sar[-2] + af[-1] * (ep[-1] - sar[-2]), max(highs[:-1]))
		
		self.data.loc[self.data.index[-1], 'SAR'] = sar[-1]

	def mfi(self, timeperiod=14):
		highs = [h for h, l, c, v in self.windows['mfi']]
		lows = [l for h, l, c, v in self.windows['mfi']]
		closes = [c for h, l, c, v in self.windows['mfi']]
		volumes = [v for h, l, c, v in self.windows['mfi']]
		
		typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
		money_flows = [tp * v for tp, v in zip(typical_prices, volumes)]
		
		positive_flow = sum(mf for tp, mf in zip(typical_prices, money_flows) if tp > typical_prices[typical_prices.index(tp)-1])
		negative_flow = sum(mf for tp, mf in zip(typical_prices, money_flows) if tp < typical_prices[typical_prices.index(tp)-1])
		
		money_ratio = positive_flow / negative_flow if negative_flow != 0 else 0
		self.data.loc[self.data.index[-1], 'MFI'] = 100 - (100 / (1 + money_ratio))

	def adl(self):
		closes = [c for c, l, h, v in self.windows['adl']]
		lows = [l for c, l, h, v in self.windows['adl']]
		highs = [h for c, l, h, v in self.windows['adl']]
		volumes = [v for c, l, h, v in self.windows['adl']]
		
		mf = [(c - l - (h - c)) / (h - l) * v for c, l, h, v in zip(closes, lows, highs, volumes)]
		self.data.loc[self.data.index[-1], 'ADL'] = sum(mf)


	def gp_type_szsh(self,code):
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


	def moving_average(self,prices, period):
		"""
		定义移动平均线的函数
		"""
		if len(prices) < period:
			return np.zeros(period)
		else:
			return np.mean(prices[-period:], axis=0)


	def calculateMACD(self,close_prices):
	
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
		self.prices_sell = []  # 平均线
		self.prices_buy = []  # 平均线
		# RSI相对强弱指数
		self.RSI_period = 14
		self.RSI_data_sell = []
		self.RSI_data_buy = []

	def addObj(self, priceObj):
		self.all_price_list.append(priceObj)
		code = list(priceObj.keys())[0]
		# 还缺一个看大单压顶的功能
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
		transaction_volume = (priceObj[code]["amount"] - accountObj["amount"]) * priceObj[code]["lastPrice"] / 10000  # 万
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
		print(f'分钟分数:{sum(self.min_big_price_list)},五分钟分数:{sum(self.Fmin_big_price_list)}')
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
	定义移动平均线的函数
	"""
	if len(prices) < period:
		return np.zeros(period)
	else:
		return np.mean(prices[-period:], axis=0)
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
r = RealTimeTechnicalIndicators([])

def init(C):
	'''
	First:
		Gain the account fund
	'''
	orders, deals, positions, accounts = query_info(C)  # 查询账户信息
	C.set_account = account


# orders:
# print(f'{accountObj["position"]["m_strInstrumentName"]}:{accountObj["position"]["m_nVolume"]}')
def postsell(orders, deals, positions, accounts, current_amount, northbound_inflow, northbound_outflow,all):
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
	res = requests.post(demo_url, data=json.dumps({"orders": order_list, 'deals': deal_list, "positions": position_list, "accounts": account_list,"current_amount":current_amount,
	"northbound_inflow":northbound_inflow,"northbound_outflow":northbound_outflow,"all":all}))
	return res

def getbuy_codes():
	demo_url = url + '/buy'
	res = requests.get(demo_url)
	return res


def handlebar(C):
	#print(C.get_market_data(['open','high','low','close','volume','amount','settle'],['300629.SZ'],'20220101','20241025',True,'1d','none'))
	if not C.is_last_bar():
		return
	
	orders, deals, positions, accounts = query_info(C)  # 查询账户信息

	accountObj['all_bullet'] = accounts[0].m_dBalance
	accountObj['bullet'] = accounts[0].m_dAvailable
	accountObj['max_use_bullet'] = accounts[0].m_dBalance * max_rate
	# print('accountObj:'+str(accountObj['code_list']))

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
	result = postsell(orders, deals, positions, accounts, transaction_volume, all_buy, all_sell, A_all / 100000000)
	if accountObj["positions"] == {}:
		return
	code = r.gp_type_szsh(accountObj["positions"]['m_strInstrumentID'])
	tick = C.get_full_tick([code])
	print(tick)
	if tick=={}:
		return 
		
		
	if tick[code]["amount"] != 0:
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
		o['m_strInstrumentName'] = order.m_strInstrumentName if order.m_strInstrumentName is not None else order.m_strInstrumentName
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
	if len(positions) <1:
		return orders, deals, positions, accounts
	o = {}
	o['m_strInstrumentID'] = positions[0].m_strInstrumentID
	o['m_strInstrumentName'] = positions[0].m_strInstrumentName
	o['m_nVolume'] = positions[0].m_nVolume  # 持仓量
	o['m_nCanUseVolume'] = positions[0].m_nCanUseVolume  # 可用数量
	o['m_dOpenPrice'] = positions[0].m_dOpenPrice  # 成本价
	o['m_dInstrumentValue'] = positions[0].m_dInstrumentValue  # 市值
	o['m_dPositionCost'] = positions[0].m_dPositionCost  # 持仓成本
	o['m_dPositionProfit'] = positions[0].m_dPositionProfit  # 盈亏
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


def deal_callback(ContextInfo, dealInfo):
	print(show_data(dealInfo))


