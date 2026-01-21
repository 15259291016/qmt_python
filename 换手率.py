from xtquant import xtdata
stock = "601166.SH"

tick = xtdata.get_full_tick([stock])[stock]
info = xtdata.get_instrument_detail(stock)

vol = tick["volume"] 
total_volume = info["TotalVolume"]
turnover_rate = vol* 100/total_volume