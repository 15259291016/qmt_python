# encoding:gbk
'''
本策略事先设定好交易的股票篮子，然后根据指数的CCI指标来判断超买和超卖
当有超买和超卖发生时，交易事先设定好的股票篮子
'''
import pandas as pd
import numpy as np
import talib
import redis
import time

opr = {
			'buy': 23,
			'sell': 24
		}

def init(ContextInfo):
	account = '8881667160'
	ContextInfo.set_account(account)
	# ---------------------------------------只会在会回测中运行---------------------------------------
	ContextInfo.start = '2023-11-15 10:00:00'
	ContextInfo.end = '2024-01-05 14:30:00'
	ContextInfo.capital = 160000
	# 设置滑点
	ContextInfo.set_slippage(1,0.01)
	# 设定策略回测各种手续费率
	# commissionType:
	# 0按比例
	# 1按每手
	# ContextInfo.set_commission(commissionType, commissionList)
	# commissionList = [open_tax, close_tax,open_commission, close_commission, close_tdaycommission, min_commission]
	# 设定买入印花税为 0，卖出印花税为 0.0001，开仓手续费和平仓（平昨）手续费均为万三，平仓手续费为0，最小手续费为5
	commissionList = [0, 0.0001, 0.0003, 0.0003, 0, 5]
	ContextInfo.set_commission(0, commissionList)
	# ---------------------------------------只会在会回测中运行---------------------------------------
	redis_client = redis.Redis(host='localhost', port=6379,db=1,password='123456')
	data = redis_client.get('data:2024-01-05拉升通道')
	# hs300成分股中sh和sz市场各自流通市值最大的前3只股票
	stockpool = eval(str(data)[2:-1])
	ContextInfo.set_universe(stockpool)		# 设定股票池
	ContextInfo.trade_code_list = stockpool
	print(ContextInfo.trade_code_list)
	ContextInfo.set_universe(ContextInfo.trade_code_list)

	ContextInfo.buy = False
	ContextInfo.sell = True

def handlebar(ContextInfo):
	# 计算当前主图的cci
	# 获取最新流通股本
	print('获取最新流通股本:'+ContextInfo.get_last_volume('000002.SZ'))
	# 获取当前K线对应的时间戳
	index = ContextInfo.barpos
	print('获取当前K线对应的时间戳'+ContextInfo.get_bar_timetag(index))
	print(get_result_records('buys', index,ContextInfo))
	# 获取当前主图品种最新分笔对应的时间的时间戳
	print('获取当前主图品种最新分笔对应的时间的时间戳'+ContextInfo.get_tick_timetag())
	realtime = ContextInfo.get_bar_timetag(index)
	print('获取指数成份股'+ContextInfo.get_sector('000300.SH', realtime))
	# indexcode：string，指数代码，形式如,'stockcode.market'，如'000300.SH'
	# stockcode：string，股票代码，形式如'stockcode.market'，如'600004.SH'
	print('获取某只股票在某指数中的绝对权重'+ContextInfo.get_weight_in_index('000300.SH', '000002.SZ'))
	# print(f'当前的周期是：{ContextInfo.period}')
	print('获取无风险利率'+ContextInfo.get_risk_free_rate(index))
	mkdict =  ContextInfo.get_market_data(['high','low','close'], count=int(period)+1)
	highs = np.array(mkdict['high'])
	lows = np.array(mkdict['low'])
	closes = np.array(mkdict['close'])
	cci_list = talib.CCI(highs,lows,closes,timeperiod=int(period))
	now_cci = cci_list[-1]
	ContextInfo.paint("CCI", now_cci, -1,0,'noaxis')
	if len(cci_list)<2:
		return 
	
	buy_condition = cci_list[-2]<buy_value<=now_cci and ContextInfo.buy
	sell_condition = cci_list[-2]>buy_value>=now_cci and ContextInfo.sell
	
	if buy_condition:
		ContextInfo.buy = False
		ContextInfo.sell = True
		for stock in ContextInfo.trade_code_list:
			order_lots(stock, 10, ContextInfo, ContextInfo.accID)
	elif sell_condition:
		ContextInfo.buy = True
		ContextInfo.sell = False
		for stock in ContextInfo.trade_code_list:
			order_lots(stock, -10, ContextInfo, ContextInfo.accID)

	df = ContextInfo.get_market_data(['close'], stock_code=ContextInfo.get_universe(), skip_paused=True, period='1d', count='1d', dividend_type='front')
	print(df)
	#print(ContextInfo.barpos)
	#for stock in ContextInfo.trade_code_list:
	#	passorder(23, 1101, ContextInfo.accID, stock, 5, -1, 100, ContextInfo)  # 23买 # 24卖
	Result = ContextInfo.get_full_tick(['600000.SH', '000001.SZ'])
	print(Result)
	print(ContextInfo.get_north_finance_change('1d'))
	print('获取指定市场的最新时间'+get_market_time("SH"))

