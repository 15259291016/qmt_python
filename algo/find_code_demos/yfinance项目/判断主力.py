import tushare as ts
import pandas as pd
import datetime

# 设置 Tushare API Token
ts.set_token('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')
pro = ts.pro_api()

# 判断过去3个月是否有主力资金介入
def is_main_force_involved(ticker, volume_threshold=2.0, inflow_threshold=0.5):
    """
    判断股票在过去3个月内是否有主力资金介入
    :param ticker: 股票代码（例如："600519.SH"）
    :param volume_threshold: 成交量放大倍数阈值（默认2.0倍）
    :param inflow_threshold: 主力资金净流入占比阈值（默认0.5%）
    :return: 返回是否有主力资金介入的判断结果
    """
    # 计算日期范围
    end_date = datetime.datetime.now().strftime('%Y%m%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y%m%d')
    
    # 获取股票日线数据
    stock_data = pro.daily(ts_code=ticker, start_date=start_date, end_date=end_date)
    stock_data = stock_data.sort_values('trade_date', ascending=True).reset_index(drop=True)
    
    if stock_data.empty:
        print("未获取到数据，请检查股票代码和日期范围。")
        return False
    
    # 计算成交量的均值
    stock_data['volume_ma'] = stock_data['vol'].rolling(window=5).mean()  # 5日均量
    
    # 判断是否有成交量放大
    stock_data['volume_spike'] = stock_data['vol'] > volume_threshold * stock_data['volume_ma']
    
    # 判断是否有价格大幅上涨
    stock_data['price_increase'] = stock_data['close'] > stock_data['open']  # 当日收盘价高于开盘价
    
    # 获取资金流向数据（大单净流入）
    # 注意：Tushare 的资金流向数据需要付费权限，这里假设你已经获取了相关数据
    # 如果没有资金流向数据，可以跳过这部分
    try:
        money_flow = pro.moneyflow(ts_code=ticker, start_date=start_date, end_date=end_date)
        money_flow = money_flow.sort_values('trade_date', ascending=True).reset_index(drop=True)
        
        # 合并资金流向数据
        stock_data = pd.merge(stock_data, money_flow[['trade_date', 'buy_lg_amount']], on='trade_date', how='left')
        stock_data['main_force_inflow'] = stock_data['buy_lg_amount'] > (stock_data['vol'] * stock_data['close'] * inflow_threshold / 100)
    except Exception as e:
        print(f"无法获取资金流向数据：{e}")
        stock_data['main_force_inflow'] = False  # 如果没有资金流向数据，默认无主力资金介入
    
    # 判断是否有主力介入的信号
    stock_data['main_force_signal'] = stock_data['volume_spike'] & stock_data['price_increase'] & stock_data['main_force_inflow']
    
    # 输出结果
    if stock_data['main_force_signal'].any():
        print(f"股票 {ticker} 在过去3个月内可能存在主力资金介入。")
        # 输出具体日期
        main_force_dates = stock_data[stock_data['main_force_signal']]['trade_date']
        print("主力介入的日期：")
        for date in main_force_dates:
            print(date)
        return True
    else:
        print(f"股票 {ticker} 在过去3个月内未发现明显的主力资金介入信号。")
        return False

# 示例：判断某只股票在过去3个月内是否有主力资金介入
ticker = "605133.SH"  # 贵州茅台（A股）
is_main_force_involved(ticker)