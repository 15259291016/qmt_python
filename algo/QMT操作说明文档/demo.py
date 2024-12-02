# 816c0405e78be6a45fd9ae1a262666d8b0da7dc7
import xtquant.xtdata as xtd

def on_tick(symbol, tick_data):
    print(f"Received tick data for {symbol}: {tick_data}")

# 设置 API 密钥
xtd.set_token('your_api_key')

# 订阅实时 Tick 数据
xtd.subscribe_quote('SHSE.600000', callback=on_tick)

# 获取历史 Tick 数据
start_time = '2023-01-01 09:30:00'
end_time = '2023-01-01 15:00:00'
ticks = xtd.get_ticks('SHSE.600000', start_time=start_time, end_time=end_time)
print(ticks)