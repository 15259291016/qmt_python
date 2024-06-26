#coding:gbk
import time, datetime

class a():
	pass
A = a()

def init(C):
	A.hsa = C.get_stock_list_in_sector('沪深A股')
	A.vol_dict = {}
	for stock in A.hsa:
		A.vol_dict[stock] = C.get_last_volume(stoA.bought_list = []
	C.run_time("f", "1nSecond", "2019-10-14 13:20:00")

def f(C):
	t0 = time.time()
	now = datetime.datetime.now()
	full_tick = C.get_full_tick(A.hsa)
	total_market_value = 0
	total_ratio = 0
	count = 0
	for stock in A.hsa:
		ratio = full_tick[stock]['lastPrice'] / full_tick[stock]['lastClose'] - 1
		if ratio > 0.09 and stock not in A.bought_list:
			msg = f"{now} {stock} {C.get_stock_name(stock)} 当前涨幅 {ratio} 大于5% 买入100股"
			#下单示例 安全起见处于注释状态 需要实际测试下单时可以放开
			#passorder(23, 1101, account, stock, 5, -1, 100, '示例策略', 2, msg, C)
			A.bought_list.append(stock)
		market_value = full_tick[stock]['lastPrice'] * A.vol_dict[stock]
		total_ratio += ratio * market_value
		total_market_value += market_value
		count += 1
	total_ratio /= total_market_value
	total_ratio *= 100
	print(f'{now} 当前A股加权涨幅 {round(total_ratio, 2)}% 函数运行耗时{round(time.time()- t0, 5)}秒')
