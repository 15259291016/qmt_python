from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from modules.tornadoapp.oms.order_manager import OrderManager
from modules.tornadoapp.oms.order_status import OrderStatus
import logging
import requests
import os

# 日志目录和文件
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'order_callback.log')

# 日志配置
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def __init__(self, order_manager: OrderManager, order_callback_handler=None):
        self.order_manager = order_manager
        self.order_callback_handler = order_callback_handler

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
        print("on_order_stock_async_response", response)
        if self.order_callback_handler:
            self.order_callback_handler.on_order_stock_async_response(response)

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        print("on_account_status")
        print(status.account_id, status.account_type, status.status)

    def on_order_status(self, order_info):
        # 假设order_info包含券商订单号、状态、成交量、均价等
        broker_order_id = order_info.get('order_id')
        broker_status = order_info.get('status')
        filled_quantity = order_info.get('filled_quantity', 0)
        avg_fill_price = order_info.get('avg_fill_price', 0.0)
        self.order_manager.update_order_status(
            broker_order_id, broker_status, filled_quantity, avg_fill_price
        )


class OrderCallbackHandler:
    def __init__(self, order_manager):
        self.order_status_dict = {}  # 订单状态管理
        self.position_dict = {}      # 简单持仓管理（symbol -> {'volume': int, 'avg_price': float}）
        self.retry_count = {}        # 订单重试计数
        self.max_retry = 1           # 废单自动重试1次
        self.dingtalk_webhook = 'https://oapi.dingtalk.com/robot/send?access_token=你的token'  # TODO:替换为你的钉钉机器人
        self.order_params = {}       # 记录每个订单的原始下单参数
        self.order_manager = order_manager

    def record_order_params(self, order_id, params):
        self.order_params[order_id] = params

    def update_position(self, symbol, filled, price):
        pos = self.position_dict.get(symbol, {'volume': 0, 'avg_price': 0.0})
        total_cost = pos['avg_price'] * pos['volume'] + price * filled
        new_volume = pos['volume'] + filled
        new_avg_price = total_cost / new_volume if new_volume > 0 else 0.0
        self.position_dict[symbol] = {'volume': new_volume, 'avg_price': new_avg_price}
        print(f"[持仓更新] {symbol} 成交 {filled} 股 @ {price}，新持仓: {self.position_dict[symbol]}")

    def notify_user(self, msg):
        data = {
            "msgtype": "text",
            "text": {"content": msg}
        }
        try:
            resp = requests.post(self.dingtalk_webhook, json=data, timeout=5)
            print(f"[通知] {msg}，钉钉返回: {resp.status_code}")
        except Exception as e:
            print(f"[通知失败] {e}")

    def log_order_response(self, order_id, status, filled, price, error_msg):
        log_msg = f"订单{order_id} 状态:{status} 成交:{filled} 价格:{price} 错误:{error_msg}"
        logging.info(log_msg)
        print(f"[日志] {log_msg}")

    def retry_order(self, order_id):
        params = self.order_params.get(order_id)
        if params:
            try:
                print(f"[重试下单] 使用原参数重试订单: {params}")
                new_order = self.order_manager.create_order(**params)
                if new_order:
                    self.notify_user(f"订单{order_id} 废单，已自动重试成功，新订单: {new_order.order_id}")
                    logging.info(f"订单{order_id} 废单，已自动重试成功，新订单: {new_order.order_id}")
                else:
                    self.notify_user(f"订单{order_id} 废单，自动重试失败！")
                    logging.error(f"订单{order_id} 废单，自动重试失败！")
            except Exception as e:
                self.notify_user(f"订单{order_id} 废单，重试异常: {e}")
                logging.exception(f"订单{order_id} 废单，重试异常: {e}")
        else:
            self.notify_user(f"订单{order_id} 废单，未找到原始下单参数，无法重试！")
            logging.error(f"订单{order_id} 废单，未找到原始下单参数，无法重试！")

    def on_order_stock_async_response(self, response):
        try:
            print("on_order_stock_async_response", response)
            order_id = getattr(response, 'order_id', None)
            status = getattr(response, 'order_status', None)
            error_msg = getattr(response, 'error_msg', '')
            filled = getattr(response, 'filled', 0)
            price = getattr(response, 'price', 0)
            symbol = getattr(response, 'stock_code', '')

            # 1. 订单状态管理
            if order_id:
                self.order_status_dict[order_id] = status
                print(f"[订单状态] 订单{order_id} 状态更新为: {status}")

            # 2. 成交回报处理
            if status in ['已成交', '部分成交']:
                self.update_position(symbol, filled, price)
                print(f"[成交回报] 订单{order_id} {symbol} 成交 {filled} 股 @ {price}")

            # 3. 异常/错误处理+自动重试
            if status == '废单' or error_msg:
                print(f"[订单异常] 订单{order_id} 失败: {error_msg}")
                retry = self.retry_count.get(order_id, 0)
                if retry < self.max_retry:
                    print(f"[重试] 订单{order_id} 第{retry+1}次重试...")
                    self.retry_count[order_id] = retry + 1
                    self.retry_order(order_id)
                else:
                    self.notify_user(f"订单{order_id} 废单，重试失败，请人工处理！错误: {error_msg}")
                    logging.error(f"订单{order_id} 废单，重试失败，请人工处理！错误: {error_msg}")

            # 4. 通知推送
            if status in ['已成交', '废单']:
                self.notify_user(f"订单{order_id} 状态: {status}，{error_msg}")

            # 5. 日志记录
            self.log_order_response(order_id, status, filled, price, error_msg)
        except Exception as e:
            logging.exception(f"[回调异常] 订单回报处理异常: {e}")
            self.notify_user(f"[回调异常] 订单回报处理异常: {e}")
