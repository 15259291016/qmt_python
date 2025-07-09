# coding=utf-8
import asyncio
import threading
import time

import tornado
# from xtquant.xttrader import XtQuantTrader
# from xtquant.xttype import StockAccount
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import configs.ConfigServer as Cs

# from user_strategy import auto_Buy, select_stock, sell
# from utils.callback import MyXtQuantTraderCallback
# from utils.data import download_all_data

configData = Cs.returnConfigData()
# miniQMT安装路径
path = configData["QMT_PATH"][0]
# QMT账号
account = configData["account"][0]


async def main():
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(
    #     download_all_data,
    #     trigger=CronTrigger(day_of_week="0-4", hour=15, minute=40),
    #     id="morning_analysis",
    #     replace_existing=True
    # )
    # scheduler.start()
    # acc = StockAccount(account, 'STOCK')
    # session_id = int(time.time())
    # xt_trader = XtQuantTrader(path, session_id)
    # xt_trader.start()
    # xt_trader.connect()
    # callback = MyXtQuantTraderCallback()
    # xt_trader.register_callback(callback)
    # subscribe_result = xt_trader.subscribe(acc)
    # if subscribe_result == -1:
    #     print('重新打开qmt')
    #     raise Exception('重新打开qmt')
    # thread_list = []
    # # thread_list.append(threading.Thread(target=auto_Buy.run_strategy, args=(acc, xt_trader,)))
    # # thread_list.append(threading.Thread(target=select_stock.run_strategy, args=()))
    # thread_list.append(threading.Thread(target=sell.run_strategy, args=("000011.SZ", acc, xt_trader,)))
    # for i in thread_list:
    #     i.daemon = True
    #     i.start()
    #     # i.join()
    # xt_trader.run_forever()
    # scheduler.shutdown()
    # 导入tornado app
    pass

if __name__ == "__main__":
    import tornado.ioloop

    from modules.tornadoapp.app import app
    from modules.tornadoapp.db.dbUtil import init_beanie
    tornado.ioloop.IOLoop.current().run_sync(init_beanie)
    http_server = tornado.httpserver.HTTPServer(app, max_body_size=1024**3 * 5)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.current().start()
