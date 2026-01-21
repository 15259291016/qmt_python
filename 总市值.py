'''
原生python，总市值
'''
from xtquant import xtdata


stock = "601916.SH"
ticks = xtdata.get_full_tick([stock])
price = ticks[stock]["lastPrice"]
TotalVolume = xtdata.get_instrument_detail(stock)['TotalVolume'] # 总股本
# 总市值 = 最新价 * 总股本
res = price * TotalVolume
print(f"{stock}总股本为{TotalVolume},总市值为{res}")