'''
///自动买入
///负责调用选股模块的结果，并通过 xtquant 接口执行交易
'''

# auto_trading.py
import threading
import time
from xtquant import xtdata, xttrader, xtconstant

from utils.callback import MyXtQuantTraderCallback
from user_strategy.selection import StockSelector
from utils.date_util import get_today_trade_day


class AutoTrader:
    def __init__(self, tushare_token, xt_user, xt_trader, end_date):
        self.stock_selector = StockSelector(token=tushare_token, end_date=end_date)
        self.trader = xt_trader
        self.xt_user = xt_user

    def execute_trades(self, stocks):
        """执行交易"""
        for stock in stocks:
            try:
                # 获取当前价格
                tick_info = xtdata.get_full_tick([stock])
                if stock in tick_info and 'lastPrice' in tick_info[stock]:
                    price = tick_info[stock]['lastPrice']
                    # 下单
                    asset = self.trader.query_stock_asset(self.xt_user)
                    print(f"现金:{asset.cash}")
                    buy_volume = int(asset.cash * 0.1 / (price * 100)) * 100
                    if buy_volume > 100:
                        # order = self.trader.order_stock_async(stock, price, 100)  # 假设每次买入100股
                        self.trader.order_stock_async(self.xt_user, stock, xtconstant.STOCK_BUY, buy_volume,
                                                      xtconstant.LATEST_PRICE, price, '打板策略')
                        print(f"已下单：{stock}，价格：{price}，数量：100")
                else:
                    print(f"无法获取股票 {stock} 的最新价格")
            except Exception as e:
                print(f"交易股票 {stock} 时出错: {e}")

    def daily_trading(self):
        """每日交易逻辑"""
        while True:
            # 获取选股结果
            top_stocks = self.stock_selector.get_top_stocks(top_n=20)
            stock_codes = top_stocks['ts_code'].tolist()
            print("今日推荐股票：", stock_codes)

            # 执行交易
            self.execute_trades(stock_codes)

            # 每天执行一次
            time.sleep(86400)

    def start(self):
        # 启动交易线程
        trading_thread = threading.Thread(target=self.daily_trading)
        trading_thread.daemon = True
        trading_thread.start()

        # 主线程保持运行
        while True:
            time.sleep(1)


def run_strategy(acc, xt_trader):
    import config.ConfigServer as Cs
    configData = Cs.returnConfigData()
    tushare_token = configData["toshare_token"]
    end_date = get_today_trade_day(True)
    # 配置
    AutoTrader(tushare_token, acc, xt_trader, end_date).start()


if __name__ == '__main__':
    import config.ConfigServer as Cs
    from xtquant.xttype import StockAccount

    configData = Cs.returnConfigData()
    # miniQMT安装路径
    path = configData["QMT_PATH"][0]
    # QMT账号
    account = configData["account"][0]
    # 配置
    tushare_token = 'gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482'
    xt_user = '55005056'
    acc = StockAccount(account, 'STOCK')
    session_id = int(time.time())
    xt_trader = xttrader.XtQuantTrader(path, session_id)

    # 启动自动化交易
    try:
        trader = AutoTrader(tushare_token, xt_user, xt_trader)
        trader.start()  # 修正方法名的大小写
    except Exception as e:
        print(f"发生错误: {e}")
