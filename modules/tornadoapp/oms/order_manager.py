import threading
from datetime import datetime
from .order_model import Order
from .order_status import OrderStatus
import uuid
from modules.tornadoapp.risk.risk_manager import RiskManager
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
from modules.tornadoapp.audit.audit_logger import AuditLogger

class OrderManager:
    def __init__(self, xt_trader, risk_manager=None, compliance_manager=None, audit_logger=None):
        self.orders = {}  # order_id -> Order
        self.lock = threading.Lock()
        self.xt_trader = xt_trader
        self.broker_order_map = {}  # 券商订单号 -> 本地order_id
        self.risk_manager = risk_manager or RiskManager()
        self.compliance_manager = compliance_manager or ComplianceManager()
        self.audit_logger = audit_logger or AuditLogger()

    def create_order(self, symbol, side, price, quantity, account, user="system"):
        # 风控校验
        risk_pass, risk_msg = self.risk_manager.check_order(symbol, price, quantity, account)
        if not risk_pass:
            self.audit_logger.log(user, "order_rejected_risk", {
                "symbol": symbol, "side": side, "price": price, "quantity": quantity, "reason": risk_msg
            })
            return None
        # 合规校验
        order_info = {"symbol": symbol, "side": side, "price": price, "quantity": quantity, "account": account}
        if not self.compliance_manager.check(order_info):
            self.audit_logger.log(user, "order_rejected_compliance", order_info)
            return None
        # 通过风控与合规，记录审计
        self.audit_logger.log(user, "order_create", order_info)
        order_id = self._generate_order_id()
        order = Order(order_id, symbol, side, price, quantity, account=account)
        with self.lock:
            self.orders[order_id] = order
        self._send_order_to_broker(order)
        return order

    def _send_order_to_broker(self, order):
        if order.side == "买":
            broker_order_id = self.xt_trader.buy(order.symbol, order.price, order.quantity, user_tag=order.order_id)
        elif order.side == "卖":
            broker_order_id = self.xt_trader.sell(order.symbol, order.price, order.quantity, user_tag=order.order_id)
        else:
            broker_order_id = None
        if broker_order_id:
            with self.lock:
                self.broker_order_map[broker_order_id] = order.order_id

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
                # 成交后更新风控
                if status == OrderStatus.FILLED:
                    self.risk_manager.on_order_filled(order.price, order.filled_quantity)
                # 审计日志
                self.audit_logger.log(user, "order_status_update", {
                    "order_id": order_id, "status": status.name, "filled_quantity": filled_quantity, "avg_fill_price": avg_fill_price
                })

    def cancel_order(self, broker_order_id, user="system"):
        # 撤单前审计
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