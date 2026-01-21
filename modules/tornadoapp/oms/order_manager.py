import threading
from datetime import datetime, timedelta
from .order_model import Order
from .order_status import OrderStatus
import uuid
from modules.tornadoapp.risk.risk_manager import RiskManager
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
from modules.tornadoapp.audit.audit_logger import AuditLogger
from xtquant import xtconstant
import asyncio
import logging

logger = logging.getLogger(__name__)

class OrderManager:
    def __init__(self, xt_trader, risk_manager=None, compliance_manager=None, audit_logger=None):
        self.orders = {}  # order_id -> Order
        self.lock = threading.Lock()
        self.xt_trader = xt_trader
        self.broker_order_map = {}  # 券商订单号 -> 本地order_id
        self.risk_manager = risk_manager or RiskManager()
        self.compliance_manager = compliance_manager or ComplianceManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.monitoring_tasks = {}  # broker_order_id -> asyncio.Task 监控任务
        self.order_broker_map = {}  # order_id -> broker_order_id 反向映射

    def create_order(self, symbol, side, price, quantity, account, user="system"):
        # 验证数量参数
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            logger.error(f"[订单创建] {symbol}: 数量参数格式错误: {quantity}")
            return None
        
        # 验证数量合理性（防止异常大的数量）
        if quantity <= 0:
            logger.error(f"[订单创建] {symbol}: 数量必须大于0，当前: {quantity}")
            return None
        
        # 卖出订单限制：一笔最大100万股
        MAX_SELL_QUANTITY = 1000000
        if side == "卖" and quantity > MAX_SELL_QUANTITY:
            logger.warning(f"[订单创建] {symbol}: 卖出数量{quantity}超过单笔最大限制{MAX_SELL_QUANTITY}股，自动调整为{MAX_SELL_QUANTITY}股")
            quantity = MAX_SELL_QUANTITY
        
        # 通用异常大数量检查（买入和卖出都适用）
        if quantity > 10000000:  # 1000万股，异常大的数量
            logger.error(f"[订单创建] {symbol}: 数量异常大: {quantity}，可能存在计算错误，拒绝创建订单")
            return None
        
        # A股交易规则：最小委托单位100股，必须是100的整数倍
        min_unit = 100
        if quantity % min_unit != 0:
            logger.warning(f"[订单创建] {symbol}: 数量{quantity}不是100的整数倍，自动调整为{(quantity // min_unit) * min_unit}")
            quantity = (quantity // min_unit) * min_unit
            if quantity < min_unit:
                logger.error(f"[订单创建] {symbol}: 调整后数量{quantity}不足100股，无法创建订单")
                return None
        
        risk_pass, risk_msg = self.risk_manager.check_order(symbol, price, quantity, account)
        if not risk_pass:
            self.audit_logger.log(user, "order_rejected_risk", {
                "symbol": symbol, "side": side, "price": price, "quantity": quantity, "reason": risk_msg
            })
            return None
        order_info = {"symbol": symbol, "side": side, "price": price, "quantity": quantity, "account": account}
        compliance_pass = self.compliance_manager.check(order_info)
        if not compliance_pass:
            self.audit_logger.log(user, "order_rejected_compliance", order_info)
            return None
        self.audit_logger.log(user, "order_create", order_info)
        order_id = self._generate_order_id()
        order = Order(order_id, symbol, side, price, quantity, account=account)
        with self.lock:
            self.orders[order_id] = order
        self._send_order_to_broker(order)
        return order

    def _send_order_to_broker(self, order):
        assert self.xt_trader.callback is not None, "xt_trader.callback 必须已注册且不为None"
        account = order.account
        if order.side == "买":
            direction = xtconstant.STOCK_BUY
        elif order.side == "卖":
            direction = xtconstant.STOCK_SELL
        else:
            direction = None
        if direction is not None:
            broker_order_id = self.xt_trader.order_stock_async(
                account,
                order.symbol,
                direction,
                order.quantity,
                xtconstant.LATEST_PRICE,
                order.price,
                order.order_id
            )
            if broker_order_id:
                with self.lock:
                    self.broker_order_map[broker_order_id] = order.order_id
                    self.order_broker_map[order.order_id] = broker_order_id
                
                # 如果是卖出订单，启动监控任务（1分钟后如果未成交则撤单重卖）
                if order.side == "卖":
                    task = asyncio.create_task(self._monitor_sell_order(
                        broker_order_id, order.order_id, order.symbol, 
                        order.price, order.quantity, order.account, 
                        timeout_seconds=60  # 1分钟
                    ))
                    with self.lock:
                        self.monitoring_tasks[broker_order_id] = task
                    logger.info(f"[订单监控] 启动卖出订单监控: {broker_order_id} ({order.symbol}), 1分钟后检查")

    def update_order_status(self, broker_order_id, broker_status, filled_quantity=0, avg_fill_price=0.0, user="system"):
        with self.lock:
            order_id = self.broker_order_map.get(broker_order_id, broker_order_id)
            order = self.orders.get(order_id)
            if order:
                status = self._map_status(broker_status)
                order.status = status
                order.filled_quantity = filled_quantity
                order.avg_fill_price = avg_fill_price
                order.update_time = datetime.now()
                if status == OrderStatus.FILLED:
                    self.risk_manager.on_order_filled(order.price, order.filled_quantity)
                    # 订单已全部成交，取消监控任务
                    if broker_order_id in self.monitoring_tasks:
                        task = self.monitoring_tasks.pop(broker_order_id)
                        if not task.done():
                            task.cancel()
                            logger.debug(f"[订单监控] 订单 {broker_order_id} 已成交，取消监控任务")
                elif status in [OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.FAILED]:
                    # 订单已撤销/拒绝/失败，取消监控任务
                    if broker_order_id in self.monitoring_tasks:
                        task = self.monitoring_tasks.pop(broker_order_id)
                        if not task.done():
                            task.cancel()
                            logger.debug(f"[订单监控] 订单 {broker_order_id} 状态为 {status.name}，取消监控任务")
                self.audit_logger.log(user, "order_status_update", {
                    "order_id": order_id, "status": status.name, "filled_quantity": filled_quantity, "avg_fill_price": avg_fill_price
                })

    def cancel_order(self, broker_order_id, user="system"):
        self.audit_logger.log(user, "order_cancel", {"broker_order_id": broker_order_id})
        self.xt_trader.cancel_order(broker_order_id)

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def get_all_orders(self):
        return list(self.orders.values())

    def _generate_order_id(self):
        return str(uuid.uuid4())

    def _map_status(self, broker_status):
        mapping = {
            "已报": OrderStatus.SUBMITTED,
            "全部成交": OrderStatus.FILLED,
            "部分成交": OrderStatus.PARTIALLY_FILLED,
            "已撤销": OrderStatus.CANCELLED,
            "拒单": OrderStatus.REJECTED,
            "失败": OrderStatus.FAILED,
        }
        return mapping.get(broker_status, OrderStatus.FAILED)
    
    async def _monitor_sell_order(
        self, 
        broker_order_id: str, 
        order_id: str, 
        symbol: str, 
        price: float, 
        quantity: int, 
        account: str,
        timeout_seconds: int = 60
    ):
        """
        监控卖出订单，如果指定时间内未成交则撤单并重新卖出
        
        Args:
            broker_order_id: 券商订单号
            order_id: 本地订单ID
            symbol: 股票代码
            price: 价格
            quantity: 数量
            account: 账户
            timeout_seconds: 超时时间（秒），默认60秒
        """
        try:
            # 等待指定时间
            await asyncio.sleep(timeout_seconds)
            
            # 检查订单状态
            with self.lock:
                order = self.orders.get(order_id)
                if not order:
                    logger.debug(f"[订单监控] 订单 {order_id} 不存在，停止监控")
                    return
                
                # 如果订单已经成交、撤销或失败，不需要处理
                if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.FAILED]:
                    logger.info(f"[订单监控] 订单 {order_id} ({symbol}) 状态为 {order.status.name}，无需撤单重卖")
                    return
                
                # 如果订单是部分成交，检查是否全部成交
                if order.status == OrderStatus.PARTIALLY_FILLED:
                    remaining_quantity = quantity - order.filled_quantity
                    if remaining_quantity <= 0:
                        logger.info(f"[订单监控] 订单 {order_id} ({symbol}) 已全部成交，无需撤单重卖")
                        return
                    # 部分成交，撤单后重新卖出剩余数量
                    quantity = remaining_quantity
                    logger.info(f"[订单监控] 订单 {order_id} ({symbol}) 部分成交，撤单后重新卖出剩余 {quantity} 股")
                else:
                    # 未成交，撤单后重新卖出全部数量
                    logger.info(f"[订单监控] 订单 {order_id} ({symbol}) 超时未成交，撤单后重新卖出")
            
            # 撤单
            try:
                logger.info(f"[订单监控] 开始撤单: {broker_order_id} ({symbol})")
                self.cancel_order(broker_order_id, user="auto_cancel_timeout")
                # 等待撤单完成（给一点时间）
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"[订单监控] 撤单失败: {broker_order_id}, 错误: {e}")
                return
            
            # 重新卖出
            try:
                # 获取最新价格（可选：使用原价格或最新价格）
                # 这里使用原价格，也可以改为获取最新价格
                new_price = price
                
                logger.info(f"[订单监控] 重新卖出: {symbol}, 价格={new_price:.2f}, 数量={quantity}股")
                new_order = self.create_order(
                    symbol=symbol,
                    side="卖",
                    price=new_price,
                    quantity=quantity,
                    account=account,
                    user="auto_resell_after_timeout"
                )
                
                if new_order:
                    logger.info(f"[订单监控] 重新卖出成功: {symbol}, 新订单ID={new_order.order_id}")
                else:
                    logger.warning(f"[订单监控] 重新卖出失败: {symbol}, 订单创建返回None")
            except Exception as e:
                logger.error(f"[订单监控] 重新卖出异常: {symbol}, 错误: {e}")
        
        except asyncio.CancelledError:
            logger.debug(f"[订单监控] 监控任务被取消: {broker_order_id}")
        except Exception as e:
            logger.error(f"[订单监控] 监控任务异常: {broker_order_id}, 错误: {e}", exc_info=True)
        finally:
            # 清理监控任务记录
            with self.lock:
                self.monitoring_tasks.pop(broker_order_id, None) 