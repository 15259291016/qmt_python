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
    def __init__(
        self,
        xt_trader,
        risk_manager=None,
        compliance_manager=None,
        audit_logger=None,
        *,
        sell_resell_enabled: bool = True,
        sell_resell_timeout_seconds: int = 60,
        # 卖出“超时撤单重卖”的最小金额阈值（元）
        # - 该机制会增加“下单次数”，更容易触发最低佣金，导致手续费翻倍。
        # - 因此默认只对金额较大的卖单启用；小额卖单（<=阈值）不撤单重卖，避免额外手续费。
        # - 经验阈值：10万以下通常无需为了成交去增加一次委托（更适合“直接挂着等成交/让它慢慢成交”）。
        sell_resell_min_value: float = 100000.0,
    ):
        self.orders = {}  # order_id -> Order
        self.lock = threading.Lock()
        self.xt_trader = xt_trader
        self.broker_order_map = {}  # 券商订单号 -> 本地order_id
        self.risk_manager = risk_manager or RiskManager()
        self.compliance_manager = compliance_manager or ComplianceManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.monitoring_tasks = {}  # broker_order_id -> asyncio.Task 监控任务
        self.order_broker_map = {}  # order_id -> broker_order_id 反向映射

        # 卖出超时撤单重卖（可选）
        # 说明：撤单重卖会增加“下单次数”，从而更容易触发最低佣金，导致手续费翻倍。
        # 因此默认只对“金额较大的卖单”启用，小金额卖单不自动撤单重卖，避免不必要的手续费损耗。
        self.sell_resell_enabled = bool(sell_resell_enabled)
        self.sell_resell_timeout_seconds = int(sell_resell_timeout_seconds)
        self.sell_resell_min_value = float(sell_resell_min_value)

    def has_open_order(self, symbol: str, side: str, account: str | None = None) -> bool:
        """检查是否存在同股票/同方向的未完成订单，用于防止实盘重复下单。

        说明：
        - auto_trader 是循环任务，同一只股票可能在多个周期都满足卖出条件。
        - 若上一笔卖单尚未完成（已报/部分成交等），重复发单会造成“重复卖出/多笔委托”风险。
        """
        open_statuses = {OrderStatus.NEW, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED}
        with self.lock:
            for o in self.orders.values():
                if o.symbol != symbol or o.side != side:
                    continue
                if account is not None and getattr(o, "account", None) != account:
                    continue
                if o.status in open_statuses:
                    return True
        return False

    def create_order(
        self,
        symbol,
        side,
        price,
        quantity,
        account,
        user="system",
        *,
        min_order_value: float = 10000.0,
        check_cash: bool = True,
    ):
        # ====== 实盘幂等保护：同股票同方向存在未完成订单时，拒绝重复下单 ======
        # 说明：这是“最后一道防线”，即使上层策略漏做去重也能避免重复委托。
        try:
            if self.has_open_order(symbol, side, account):
                logger.warning(
                    f"[订单创建] {symbol}: 检测到未完成的{side}订单，跳过重复下单（account={account}）"
                )
                self.audit_logger.log(user, "order_rejected_duplicate_open_order", {
                    "symbol": symbol, "side": side, "account": account, "reason": "duplicate_open_order"
                })
                return None
        except Exception as e:
            # 去重检查异常时，为安全起见拒单（避免重复委托）
            logger.error(f"[订单创建] {symbol}: 去重检查异常: {e}，拒绝下单", exc_info=True)
            self.audit_logger.log(user, "order_rejected_duplicate_check_error", {
                "symbol": symbol, "side": side, "account": account, "reason": f"duplicate_check_error: {e}"
            })
            return None

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
        
        # 验证价格参数
        if price is None:
            logger.error(f"[订单创建] {symbol}: 价格参数为 None，无法创建订单")
            return None
        if price <= 0:
            logger.error(f"[订单创建] {symbol}: 价格参数无效: {price}，必须大于0")
            return None

        # ====== 资金/最低金额校验（实盘兜底防线） ======
        # 说明：
        # - 策略层可能已经做过资金与最小持仓金额判断，但这里再做一次“下单前最后验证”，避免出现 -57 可用资金不足。
        # - min_order_value 默认 10000（与策略最小持仓金额保持一致）；如需关闭可传 0。
        if side == "买":
            try:
                est_value = float(price) * int(quantity)
                if min_order_value and est_value < float(min_order_value):
                    msg = f"单笔金额{est_value:.2f}元低于最低限制{float(min_order_value):.2f}元，拒绝下单"
                    logger.warning(f"[订单创建] {symbol}: {msg}")
                    self.audit_logger.log(user, "order_rejected_min_value", {
                        "symbol": symbol, "side": side, "price": price, "quantity": quantity,
                        "min_order_value": float(min_order_value), "est_value": est_value, "reason": msg
                    })
                    return None

                if check_cash:
                    asset = self.xt_trader.query_stock_asset(account)
                    available_cash = getattr(asset, 'cash', 0) or getattr(asset, 'available_cash', 0)
                    commission_rate = 0.0003  # 估算佣金（仅用于预校验）
                    est_cost = est_value * (1 + commission_rate)
                    if available_cash is None:
                        available_cash = 0
                    if float(available_cash) < est_cost:
                        msg = f"可用资金不足：可用{float(available_cash):.2f}元 < 预估成本{est_cost:.2f}元，拒绝下单"
                        logger.warning(f"[订单创建] {symbol}: {msg}")
                        self.audit_logger.log(user, "order_rejected_insufficient_cash", {
                            "symbol": symbol, "side": side, "price": price, "quantity": quantity,
                            "available_cash": float(available_cash), "est_cost": est_cost, "reason": msg
                        })
                        return None
            except Exception as e:
                # 资金校验异常时，为了安全起见直接拒单（防止误下单）
                msg = f"资金校验异常: {e}，拒绝下单"
                logger.error(f"[订单创建] {symbol}: {msg}", exc_info=True)
                self.audit_logger.log(user, "order_rejected_cash_check_error", {
                    "symbol": symbol, "side": side, "price": price, "quantity": quantity, "reason": msg
                })
                return None
        
        risk_pass, risk_msg = self.risk_manager.check_order(symbol, price, quantity, account)
        if not risk_pass:
            logger.warning(f"[订单创建] {symbol}: 风控检查未通过: {risk_msg}")
            self.audit_logger.log(user, "order_rejected_risk", {
                "symbol": symbol, "side": side, "price": price, "quantity": quantity, "reason": risk_msg
            })
            return None
        order_info = {"symbol": symbol, "side": side, "price": price, "quantity": quantity, "account": account}
        compliance_pass = self.compliance_manager.check(order_info)
        if not compliance_pass:
            logger.warning(f"[订单创建] {symbol}: 合规检查未通过")
            self.audit_logger.log(user, "order_rejected_compliance", order_info)
            return None
        self.audit_logger.log(user, "order_create", order_info)
        order_id = self._generate_order_id()
        order = Order(order_id, symbol, side, price, quantity, account=account)
        logger.info(f"[订单创建] 成功创建订单: 订单ID={order_id}, 股票={symbol}, 方向={side}, 价格={price}, 数量={quantity}")
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
            # 记录订单提交前的详细信息
            logger.info(f"[订单提交] 准备提交订单: 股票={order.symbol}, 方向={order.side}, "
                       f"价格={order.price}, 数量={order.quantity}, 账户={account}, 本地订单ID={order.order_id}")
            
            # 验证价格参数
            if order.price is None or order.price <= 0:
                logger.error(f"[订单提交失败] {order.symbol}: 价格参数无效: {order.price}")
                return
            
            broker_order_id = self.xt_trader.order_stock_async(
                account,
                order.symbol,
                direction,
                order.quantity,
                xtconstant.LATEST_PRICE,
                order.price,
                order.order_id
            )
            
            # 记录订单提交结果
            logger.info(f"[订单提交] {order.symbol}: order_stock_async 返回值={broker_order_id} (类型={type(broker_order_id).__name__})")
            
            if broker_order_id:
                with self.lock:
                    self.broker_order_map[broker_order_id] = order.order_id
                    self.order_broker_map[order.order_id] = broker_order_id
                
                # 如果是卖出订单，按需启动监控任务（超时未成交则撤单重卖）
                if order.side == "卖":
                    est_value = float(order.price) * int(order.quantity)
                    if not self.sell_resell_enabled:
                        logger.info(
                            f"[订单监控] 卖出撤单重卖已关闭: {broker_order_id} ({order.symbol})"
                        )
                    elif est_value < self.sell_resell_min_value:
                        logger.info(
                            f"[订单监控] 跳过卖出撤单重卖(金额较小): {broker_order_id} ({order.symbol}) "
                            f"金额={est_value:.2f} < 阈值{self.sell_resell_min_value:.2f}，避免额外手续费"
                        )
                    else:
                        task = asyncio.create_task(self._monitor_sell_order(
                            broker_order_id, order.order_id, order.symbol,
                            order.price, order.quantity, order.account,
                            timeout_seconds=self.sell_resell_timeout_seconds
                        ))
                        with self.lock:
                            self.monitoring_tasks[broker_order_id] = task
                            logger.info(
                                f"[订单监控] 启动卖出订单监控: {broker_order_id} ({order.symbol}), "
                                f"{self.sell_resell_timeout_seconds}秒后检查，金额={est_value:.2f}"
                            )
            else:
                # broker_order_id 为 None、-1 或空，说明订单提交失败
                logger.error(f"[订单提交失败] {order.symbol}: order_stock_async 返回值为 {broker_order_id}，订单未成功提交到券商")
                logger.error(f"[订单提交失败] 订单参数: 价格={order.price}, 数量={order.quantity}, 账户={account}, 方向={order.side}")
                # 更新订单状态为失败
                with self.lock:
                    if order.order_id in self.orders:
                        self.orders[order.order_id].status = OrderStatus.FAILED

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
        """撤单封装：根据券商订单号撤单，自动匹配账户并调用 xtquant 接口。

        设计说明：
        - xtquant 撤单接口为 cancel_order_stock(account, order_id)，需要证券账号。
        - 这里通过 broker_order_id -> 本地 order_id -> Order.account 反查账户，确保实盘使用正确账号撤单。
        """
        account = None
        with self.lock:
            order_id = self.broker_order_map.get(broker_order_id)
            if order_id:
                order = self.orders.get(order_id)
                if order is not None:
                    account = order.account

        if account is None:
            logger.error(
                f"[撤单失败] 无法为券商订单号 {broker_order_id} 找到对应账户，撤单请求被忽略"
            )
            self.audit_logger.log(user, "order_cancel_failed_no_account", {
                "broker_order_id": broker_order_id,
                "reason": "no_account_found",
            })
            return

        self.audit_logger.log(user, "order_cancel", {
            "broker_order_id": broker_order_id,
            "account": getattr(account, "account_id", str(account)),
        })
        try:
            # XtQuantTrader 撤单接口：cancel_order_stock(account, order_id)
            result = self.xt_trader.cancel_order_stock(account, broker_order_id)
            logger.info(
                f"[撤单请求] 账户={getattr(account, 'account_id', account)}, "
                f"订单号={broker_order_id}, 结果={result}"
            )
        except AttributeError as e:
            # 兼容环境异常：xt_trader 未提供撤单接口时仅记录错误，避免崩溃
            logger.error(
                f"[撤单失败] XtQuantTrader 未提供 cancel_order_stock 接口: {e}"
            )
            self.audit_logger.log(user, "order_cancel_failed_no_api", {
                "broker_order_id": broker_order_id,
                "reason": "no_cancel_order_stock",
            })
        except Exception as e:
            logger.error(f"[撤单失败] 撤单调用异常: {e}", exc_info=True)
            self.audit_logger.log(user, "order_cancel_failed_exception", {
                "broker_order_id": broker_order_id,
                "reason": str(e),
            })

    def cancel_all_open_buy_orders(self, user="system") -> int:
        """撤销所有未成交的买入订单，在极端行情冻结时调用。
        
        Returns:
            int: 实际发起撤单的订单数量
        """
        open_statuses = {OrderStatus.NEW, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED}
        to_cancel = []
        with self.lock:
            for order in self.orders.values():
                if order.side == "买" and order.status in open_statuses:
                    broker_id = self.order_broker_map.get(order.order_id)
                    if broker_id:
                        to_cancel.append((broker_id, order.symbol))
        
        for broker_id, symbol in to_cancel:
            logger.info(f"[极端行情撤单] 撤销未成交买入订单: {symbol}, 券商订单号={broker_id}")
            self.cancel_order(broker_id, user=user)
        
        if to_cancel:
            logger.info(f"[极端行情撤单] 共撤销{len(to_cancel)}笔未成交买入订单")
        return len(to_cancel)

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
                # 等待撤单完成：撤单通常是异步回报，固定 sleep 可能不够，容易导致“未完成卖单”拦截重卖
                cancel_wait_seconds = 10
                poll_interval = 0.5
                waited = 0.0
                while waited < cancel_wait_seconds:
                    with self.lock:
                        o = self.orders.get(order_id)
                        if not o:
                            # 本地订单丢失时，为安全起见不再重卖
                            logger.warning(f"[订单监控] 撤单后本地订单丢失: {order_id} ({symbol})，停止重卖")
                            return
                        if o.status in [
                            OrderStatus.CANCELLED,
                            OrderStatus.REJECTED,
                            OrderStatus.FAILED,
                            OrderStatus.FILLED,
                        ]:
                            break
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval

                with self.lock:
                    o = self.orders.get(order_id)
                    # 仍未进入“已撤销/成交/失败”等终态，说明撤单回报还没到，继续重卖会被幂等保护拦截且无意义
                    if o and o.status not in [
                        OrderStatus.CANCELLED,
                        OrderStatus.REJECTED,
                        OrderStatus.FAILED,
                        OrderStatus.FILLED,
                    ]:
                        logger.warning(
                            f"[订单监控] 撤单回报未确认({cancel_wait_seconds}s内未到): {symbol}, "
                            f"order_id={order_id}, status={o.status.name}，跳过重卖避免重复委托"
                        )
                        return
            except Exception as e:
                logger.error(f"[订单监控] 撤单失败: {broker_order_id}, 错误: {e}")
                return
            
            # 重新卖出
            try:
                # 如果账户里仍有同方向未完成卖单（例如撤单未成功/未回报），则不要重卖
                try:
                    if self.has_open_order(symbol, "卖", account):
                        logger.warning(
                            f"[订单监控] {symbol}: 检测到未完成卖订单（撤单可能未生效），跳过重卖"
                        )
                        return
                except Exception:
                    # 去重检查失败时，为安全起见不重卖
                    logger.warning(f"[订单监控] {symbol}: 未完成订单检查异常，跳过重卖", exc_info=True)
                    return

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