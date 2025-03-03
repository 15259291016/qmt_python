# coding=utf-8
import time
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant
import random
import config.ConfigServer as Cs
from xtquant import xtdata
from datetime import datetime
import easyquotation
import collections
import pandas as pd
import threading
import pywencai as pywc
from utils import synchronous_dependency
from fastapiapp import start_fastapi

configData = Cs.returnConfigData()
quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']
# miniQMT安装路径
path = configData["QMT_PATH"][0]
# QMT账号
account = configData["account"][0]

def stock_names_to_list(stock_names:list[str]):
    csv_file_path = './data/股票列表.csv'    # 替换为您的CSV文件路径
    df = pd.read_csv(csv_file_path)
    result = []
    for name in stock_names:
        result.append(df['ts_code'][df['name'] == name].tolist()[0].split(".")[0])
    return result

class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        print("connection lost")

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        print("on order callback:")
        print(order.stock_code, order.order_status, order.order_sysid)

    def on_stock_asset(self, asset):
        """
        资金变动推送
        :param asset: XtAsset对象
        :return:
        """
        print("on asset callback")
        print(asset.account_id, asset.cash, asset.total_asset)

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        print("on trade callback")
        print(trade.account_id, trade.stock_code, trade.order_id)

    def on_stock_position(self, position):
        """
        持仓变动推送
        :param position: XtPosition对象
        :return:
        """
        print("on position callback")
        print(position.stock_code, position.volume)

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        print("on order_error callback")
        print(order_error.order_id, order_error.error_id, order_error.error_msg)

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        print("on cancel_error callback")
        print(cancel_error.order_id, cancel_error.error_id, cancel_error.error_msg)

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        print("on_order_stock_async_response")
        print(response.account_id, response.order_id, response.seq)

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        print("on_account_status")
        print(status.account_id, status.account_type, status.status)


def connect():
    global session_id

    # 重连时需要更换session_id
    session_id += 1
    xt_trader = XtQuantTrader(path, session_id)
    # 创建资金账号为1000000365的证券账号对象
    callback = MyXtQuantTraderCallback()
    xt_trader.register_callback(callback)
    # 启动交易线程
    xt_trader.start()
    # 建立交易连接，返回0表示连接成功
    connect_result = xt_trader.connect()
    if connect_result == 0:
        return xt_trader, True
    else:
        return None, False
# 定义一个类 创建类的实例 作为状态的容器
class _a():
    pass
A = _a()
A.bought_list = []
A.data_cache = {}
A.update_bought_list_num = 0
#___________________________________________________________
def update_bought_list():
    full_data = xtdata.get_full_tick(code_list)
    #检测如果当前价格已经等于涨停价就加入A.bought_list中
    for stock in code_list:
        print(stock)
        # if full_data[stock]['lastPrice'] == loaded_dict[stock]:
            # A.bought_list.append(stock)



# code_list = xtdata.get_stock_list_in_sector('沪深A股')

# 数据缓存：存储每个股票的最近40个数据

# ['time', 'lastPrice', 'open', 'high', 'low', 'lastClose', 'amount', 'volume', 'pvolume', 'stockStatus', 'openInt', 'transactionNum', 'lastSettlementPrice', 'settlementPrice', 'pe', 'askPrice', 'bidPrice', 'askVol', 'bidVol', 'volRatio', 'speed1Min', 'speed5Min']
# 更新缓存中的数据（只保留最近40个数据）
def update_cache(stock, new_data):
    if stock not in A.data_cache:
        # 如果股票没有数据缓存，初始化一个空的队列
        A.data_cache[stock] = collections.deque(maxlen=40)  # 保留最近40条数据
    
    # 添加新的数据记录
    A.data_cache[stock].append(new_data)
df_dict = {
    'tick':{},
    "sh":{},
}

sh_thread = None
def watch_sh_by_stocks_names(stock_names: list[str], interval, df_dict):
    stock_code_list = stock_names_to_list(stock_names)
    stock_e_c_name_dict = {stock_names[i]:stock_code_list[i] for i in range(len(stock_code_list))}
    while True:
        stock_dde_info = pywc.get(query=f"{stock_names} 散户指标")
        info_dict = [stock_dde_info[key] for key in stock_dde_info.keys()][0].T.to_dict()
        for key in info_dict:
            try:
                df_dict["sh"][stock_e_c_name_dict[info_dict[key]['名称']]] = info_dict[key]['dde散户数量']
            except Exception as e:
                print(e)
                continue
        # [info_dict[key] for key in info_dict]
        # sh_num = float(stock_dde_info["barline3"]["dde散户数量"].iloc[-1])
        # print(info_dict)
        # print(df_dict["sh"])
        print("updated")
        time.sleep(interval)
        
if sh_thread is None:
    sh_thread = threading.Thread(target=watch_sh_by_stocks_names, args=(['嵘泰股份', '远程股份', '吉比特','春风动力', '可孚医疗','华北制药', '比亚迪', '巨轮智能'], 6*10, df_dict))
    sh_thread.start()  
    
def on_tick(data):
    stock_code_list = []
    # 查询账户资产信息
    # print(data)
    # {'605133.SH': {'time': 1740970227000,
    # 'lastPrice': 26.71, 'open': 26.52, 'high': 26.84, 'low': 26.09,
    # 'lastClose': 26.19, 'amount': 48391700.0, 'volume': 18228, 'pvolume': 1822800, 'stockStatus': 3,
    # 'openInt': 13, 'transactionNum': 0, 'lastSettlementPrice': 26.19, 'settlementPrice': 0.0, 'pe': 0.0,
    # 'askPrice': [26.71, 26.72, 26.73, 26.740000000000002, 26.75], 'bidPrice': [26.7, 26.68, 26.67, 26.66, 26.63],
    # 'askVol': [27, 3, 1, 5, 17], 'bidVol': [13, 7, 55, 44, 79], 'volRatio': 0.0, 'speed1Min': 0.0, 'speed5Min': 0.0}}
    asset = xt_trader.query_stock_asset(acc)
    # if asset:
    #     print(f"可用金额: {asset.cash}")
    #     print(f"冻结金额: {asset.frozen_cash}")
    #     print(f"总资产: {asset.total_asset}")
    # else:
    #     print("无法获取账户资产信息")

    # 查询持仓信息
    positions = xt_trader.query_stock_positions(acc)
    if positions:
        # print("持仓股票列表：")
        for position in positions:
            stock_code_list.append(position.stock_code[:-3])
            print(f"{position.stock_code}, 仓: {position.volume}, 本: {position.avg_price}, now: {data[position.stock_code]['lastPrice']:0.2f}")
    else:
        print("当前没有持仓股票")
        cjbs = 0
        
    stock_code_list = stock_names_to_list(['嵘泰股份'])
    for stock_code in stock_code_list:
        df_dict['tick'][stock_code] = pd.DataFrame()
    stock_data = quotation.real(stock_code_list)
    rename_mapping = {
        'PE': 'pe',
        'PB': 'pb',
        '涨跌(%)': '涨跌百分比',
        '价格/成交量(手)/成交额': '价格成交量成交额',
        '成交量(手)': '成交量手',
        '成交额(万)': '成交额万',
        '市盈(动)': '市盈动',
        '市盈(静)': '市盈静'
    }
    for stock_code in stock_code_list:
        renamed_data = {rename_mapping.get(k, k): v for k, v in stock_data[stock_code].items()}
        for i in renamed_data.keys():
            renamed_data[i] = [renamed_data[i]]
        renamed_data["unknown"] = [1]
        ef = pd.DataFrame(renamed_data)
        ef['rolling_max'] = ef['涨跌百分比']
        ef['rolling_min'] = ef['涨跌百分比'].rolling(window=100, min_periods=1).min()
        if len(df_dict['tick'][stock_code])<=10:
            ef['signal_sell'] = "00"
            ef['signal_buy'] = "00"
            df_dict['tick'][stock_code] = pd.concat([df_dict['tick'][stock_code], ef], ignore_index=True)
        else:
            ef['signal_sell'] = 'sell' if df_dict['tick'][stock_code]['rolling_max'].rolling(window=100, min_periods=1).max().max() - ef['涨跌百分比'].iloc[-1] >= 1.5 else "00"
            ef['signal_buy'] = 'buy' if ef['涨跌百分比'].iloc[-1] - df_dict['tick'][stock_code]['rolling_min'].rolling(window=100, min_periods=1).min().min() >= 1.5 else "00"
            df_dict['tick'][stock_code] = pd.concat([df_dict['tick'][stock_code], ef], ignore_index=True)
        print(f'{ef["name"].iloc[-1]}:{ef["now"].iloc[-1]}\t||{ef["涨跌百分比"].iloc[-1]}-{ef["量比"].iloc[-1]}-{ef["均价"].iloc[-1]}' +
                f'-{df_dict["tick"][stock_code]["rolling_max"].rolling(window=100, min_periods=1).max().max()},' +
                f'{df_dict["tick"][stock_code]["rolling_min"].rolling(window=100, min_periods=1).min().min()}\t{ef["signal_sell"].iloc[-1]}-{ef["signal_buy"].iloc[-1]}' +
                f'\t{df_dict["sh"][stock_code] if stock_code in df_dict["sh"] else 0}' +
                f'\t\t{"高" if ef["now"].iloc[-1] > ef["均价"].iloc[-1] else "低"}:' +
                f'{(ef["now"].iloc[-1] - ef["均价"].iloc[-1]):.2f}:' + 
                f'{(float((ef["now"].iloc[-1] - ef["均价"].iloc[-1])) / ef["now"].iloc[-1])*100:.2f}%')
    print('-'*100)
    
    now = datetime.now().strftime("%H:%M")
    #每次运行剔除已经涨停的票
    if A.update_bought_list_num == 0 and now >= '09:25':
        update_bought_list()
        A.update_bought_list_num = 1

    for stock, stock_data in data.items():
        if (stock not in code_list )or (stock in A.bought_list):
            continue
        # 更新缓存数据以便计算因子
        update_cache(stock, stock_data)
        # print(stock,stock_data)
        lastprice = stock_data['lastPrice']

        # up_limit_price = loaded_dict[stock]
        up_limit_price = lastprice * 1.1

        factor1 = lastprice >= up_limit_price
        if factor1 and now <= '10:00':
            print(stock,'达到涨停价')
            factor3 = calculate_factors(stock)
            if factor3:
                print(stock,'符合打板条件')
                stock_count = buy_values / lastprice
                # 取整到最接近的 100 的倍数
                a = 1/0
                buy_volume = round(stock_count / 100) * 100
                print(stock,'买入数量',buy_volume)
        
                async_seq = xt_trader.order_stock_async(acc, stock, xtconstant.STOCK_BUY, buy_volume, xtconstant.LATEST_PRICE, up_limit_price, '打板策略')
                A.bought_list.append(stock)

if __name__ == "__main__":
    xtdata.enable_hello = False
    code_list = []
    acc = StockAccount(account, 'STOCK')
    session_id = int(time.time())
    xt_trader = XtQuantTrader(path, session_id)
    callback = MyXtQuantTraderCallback()
    xt_trader.register_callback(callback)
    xt_trader.start()
    # 建立交易连接，返回0表示连接成功
    connect_result = xt_trader.connect()
    print('建立交易连接，返回0表示连接成功', connect_result)
    # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
    subscribe_result = xt_trader.subscribe(acc)
    # 查询账户资产信息
    asset = xt_trader.query_stock_asset(acc)
    if asset:
        print(f"可用金额: {asset.cash}")
        print(f"冻结金额: {asset.frozen_cash}")
        print(f"总资产: {asset.total_asset}")
    else:
        print("无法获取账户资产信息")

    # 查询持仓信息
    positions = xt_trader.query_stock_positions(acc)
    if positions:
        print("持仓股票列表：")
        for position in positions:
            code_list.append(position.stock_code)
    else:
        print("当前没有持仓股票")
    xtdata.subscribe_whole_quote(code_list, callback=on_tick)
    synchronous_dependency.update_requirements()
    fastapi_thread = threading.Thread(target=start_fastapi)
    fastapi_thread.daemon = True  # 设置为守护线程
    fastapi_thread.start()
    xt_trader.run_forever()