# 获取资金流向数据
def get_money_flow(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    money_flow = info.get('totalNetVolume', 0)
    return money_flow

# 示例：获取苹果公司的资金流向
money_flow = get_money_flow(symbol)
print(f'Money Flow: {money_flow}')
