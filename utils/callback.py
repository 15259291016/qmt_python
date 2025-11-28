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
    
    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        print("on order_error callback")
        failed_order_id = order_error.order_id
        error_id = order_error.error_id
        error_msg = order_error.error_msg
        print(f"[委托失败] 订单ID: {failed_order_id}, 错误ID: {error_id}, 错误信息: {error_msg}")
        
        # 如果有order_callback_handler，调用其撤单逻辑
        if self.order_callback_handler:
            self.order_callback_handler.on_order_error(order_error)

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
        print(f"资金账号{order.account_id} 下单股票{order.stock_code} 订单状态{order.order_status} 订单系统ID{order.order_sysid}")
        print(f"委托价格{order.price} 委托数量{order.m_nOrderVolume} 委托方向{order.direction} 委托时间{order.order_time}")

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
        # 订单历史记录：按股票代码记录订单列表（broker_order_id -> {'broker_order_id': str, 'symbol': str, 'timestamp': datetime}）
        self.order_history = {}  # symbol -> [order_info, ...] 按时间顺序
        self.broker_order_to_symbol = {}  # broker_order_id -> symbol 快速查找

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
                
                # 记录订单历史（用于撤单功能）
                if symbol and order_id:
                    from datetime import datetime
                    if symbol not in self.order_history:
                        self.order_history[symbol] = []
                    # 记录订单信息
                    order_info = {
                        'broker_order_id': order_id,
                        'symbol': symbol,
                        'timestamp': datetime.now(),
                        'status': status
                    }
                    self.order_history[symbol].append(order_info)
                    self.broker_order_to_symbol[order_id] = symbol
                    # 只保留最近20个订单，避免内存占用过大
                    if len(self.order_history[symbol]) > 20:
                        old_order = self.order_history[symbol].pop(0)
                        self.broker_order_to_symbol.pop(old_order['broker_order_id'], None)

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
    
    def _normalize_stock_code(self, symbol: str) -> str:
        """
        标准化股票代码格式
        将 [SZ002083] 或 SZ002083 转换为 002083.SZ 格式（系统使用的格式）
        """
        if not symbol:
            return symbol
        
        # 如果已经是标准格式（如 002083.SZ 或 000001.SH），直接返回
        if '.' in symbol:
            return symbol
        
        # 处理 [SZ002083] 或 SZ002083 格式
        import re
        # 移除方括号
        symbol = symbol.replace('[', '').replace(']', '').strip()
        
        # 匹配 SZ002083 或 SH600000 格式
        match = re.match(r'([SH|SZ])(\d{6})', symbol)
        if match:
            market = match.group(1)
            code = match.group(2)
            # 转换为 002083.SZ 格式（系统使用的格式：代码.市场）
            return f"{code}.{market}"
        
        # 如果只有6位数字，尝试根据代码判断市场
        if re.match(r'^\d{6}$', symbol):
            # 6开头是上海，0/3开头是深圳
            if symbol.startswith('6'):
                return f"{symbol}.SH"
            else:
                return f"{symbol}.SZ"
        
        return symbol
    
    def on_order_error(self, order_error):
        """
        委托失败推送 - 自动撤上一个订单
        :param order_error: XtOrderError 对象
        :return:
        """
        import re
        from datetime import datetime
        
        failed_order_id = order_error.order_id
        error_id = order_error.error_id
        error_msg = order_error.error_msg
        logging.warning(f"[委托失败] 订单ID: {failed_order_id}, 错误ID: {error_id}, 错误信息: {error_msg}")
        print(f"[委托失败] 订单ID: {failed_order_id}, 错误ID: {error_id}, 错误信息: {error_msg}")
        
        # 尝试获取股票代码（多种方法）
        symbol = None
        
        # 方法1: 从order_error对象直接获取stock_code属性（如果存在）
        try:
            symbol = getattr(order_error, 'stock_code', None)
            if symbol:
                symbol = self._normalize_stock_code(symbol)
                logging.info(f"[撤单] 从order_error对象获取股票代码: {symbol}")
        except Exception as e:
            logging.debug(f"[撤单] 尝试从order_error获取stock_code失败: {e}")
        
        # 方法2: 从错误信息中解析股票代码（格式如：[SZ002083] 或 [SH600000]）
        if not symbol and error_msg:
            try:
                # 匹配 [SZ002083] 或 [SH600000] 格式
                match = re.search(r'\[([SH|SZ]\d{6})\]', error_msg)
                if match:
                    raw_symbol = match.group(1)
                    symbol = self._normalize_stock_code(raw_symbol)
                    logging.info(f"[撤单] 从错误信息中解析股票代码: {raw_symbol} -> {symbol}")
            except Exception as e:
                logging.debug(f"[撤单] 从错误信息解析股票代码失败: {e}")
        
        # 方法3: 从broker_order_to_symbol查找
        if not symbol:
            symbol = self.broker_order_to_symbol.get(failed_order_id)
            if symbol:
                logging.info(f"[撤单] 从broker_order_to_symbol获取股票代码: {symbol}")
        
        # 方法4: 从order_manager查找订单信息
        if not symbol:
            try:
                # 通过broker_order_map查找本地订单
                local_order_id = self.order_manager.broker_order_map.get(failed_order_id)
                if local_order_id:
                    order = self.order_manager.get_order(local_order_id)
                    if order:
                        symbol = order.symbol
                        logging.info(f"[撤单] 从order_manager获取股票代码: {symbol}")
            except Exception as e:
                logging.warning(f"[撤单] 查找订单信息失败: {e}")
        
        # 方法5: 遍历order_history查找（最后手段）
        if not symbol:
            try:
                for sym, orders in self.order_history.items():
                    for order_info in orders:
                        if order_info.get('broker_order_id') == failed_order_id:
                            symbol = sym
                            logging.info(f"[撤单] 从order_history遍历获取股票代码: {symbol}")
                            break
                    if symbol:
                        break
            except Exception as e:
                logging.warning(f"[撤单] 遍历order_history失败: {e}")
        
        # 方法6: 如果从错误信息解析到了代码但格式可能不同，尝试在order_history中模糊匹配
        if symbol and '.' in symbol:
            # 如果order_history中没有这个格式的symbol，尝试查找相同代码但不同格式的
            if symbol not in self.order_history:
                code_part = symbol.split('.')[0]  # 提取代码部分（如 002083）
                for sym in self.order_history.keys():
                    if sym.split('.')[0] == code_part:  # 代码部分相同
                        symbol = sym  # 使用order_history中的格式
                        logging.info(f"[撤单] 找到相同代码但不同格式的股票: {sym} -> {symbol}")
                        break
        
        # 如果找到股票代码，记录失败订单并尝试撤上一个订单
        if symbol:
            # 记录失败订单到历史（即使失败也要记录，方便后续查找）
            if symbol not in self.order_history:
                self.order_history[symbol] = []
            
            # 检查是否已记录此订单
            order_exists = any(
                order_info.get('broker_order_id') == failed_order_id 
                for order_info in self.order_history[symbol]
            )
            
            if not order_exists:
                order_info = {
                    'broker_order_id': failed_order_id,
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'status': '委托失败',
                    'error_id': error_id,
                    'error_msg': error_msg
                }
                self.order_history[symbol].append(order_info)
                self.broker_order_to_symbol[failed_order_id] = symbol
                logging.info(f"[撤单] 已记录失败订单到历史: {symbol} - {failed_order_id}")
            
            # 尝试撤该股票的上一个订单
            self._cancel_previous_order(symbol, failed_order_id)
        else:
            logging.warning(f"[撤单] 无法找到失败订单{failed_order_id}对应的股票代码，无法撤单")
            print(f"[撤单] 无法找到失败订单{failed_order_id}对应的股票代码，无法撤单")
            # 打印调试信息
            print(f"[调试] broker_order_to_symbol keys (前10个): {list(self.broker_order_to_symbol.keys())[:10]}")
            print(f"[调试] order_history symbols: {list(self.order_history.keys())}")
            print(f"[调试] 错误信息: {error_msg}")
    
    def _cancel_previous_order(self, symbol, failed_order_id):
        """
        撤该股票的上一个订单
        :param symbol: 股票代码
        :param failed_order_id: 失败的订单ID（排除此订单）
        """
        try:
            if symbol not in self.order_history or len(self.order_history[symbol]) < 2:
                logging.info(f"[撤单] {symbol} 订单历史不足，无法撤单")
                print(f"[撤单] {symbol} 订单历史不足，无法撤单")
                return
            
            # 找到上一个订单（排除失败的订单）
            orders = self.order_history[symbol]
            previous_order = None
            
            # 从后往前查找，找到失败订单之前的最后一个有效订单
            for i in range(len(orders) - 1, -1, -1):
                order_info = orders[i]
                broker_order_id = order_info['broker_order_id']
                status = order_info.get('status', '')
                
                # 跳过失败的订单本身
                if broker_order_id == failed_order_id:
                    continue
                
                # 只撤未完全成交的订单（已报、部分成交）
                if status in ['已报', '部分成交']:
                    previous_order = order_info
                    break
            
            if previous_order:
                prev_order_id = previous_order['broker_order_id']
                logging.info(f"[撤单] {symbol} 委托失败，撤上一个订单: {prev_order_id}")
                print(f"[撤单] {symbol} 委托失败，撤上一个订单: {prev_order_id}")
                
                # 调用order_manager撤单
                try:
                    self.order_manager.cancel_order(prev_order_id, user="auto_cancel_on_error")
                    logging.info(f"[撤单] {symbol} 已提交撤单请求: {prev_order_id}")
                    print(f"[撤单] {symbol} 已提交撤单请求: {prev_order_id}")
                except Exception as e:
                    logging.error(f"[撤单] {symbol} 撤单失败: {e}")
                    print(f"[撤单] {symbol} 撤单失败: {e}")
            else:
                logging.info(f"[撤单] {symbol} 未找到可撤的上一个订单")
                print(f"[撤单] {symbol} 未找到可撤的上一个订单")
        except Exception as e:
            logging.exception(f"[撤单] 撤单处理异常: {e}")
            print(f"[撤单] 撤单处理异常: {e}")
