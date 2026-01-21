'''
原生python，流通市值
'''
from xtquant import xtdata


stock = "601916.SH"
ticks = xtdata.get_full_tick([stock])
price = ticks[stock]["lastPrice"]
FloatVolume = xtdata.get_instrument_detail(stock)['FloatVolume'] # 流通股本
# 流通市值 = 最新价 * 流通股本
res = price * FloatVolume
print(f"{stock}流通市值为{res}")