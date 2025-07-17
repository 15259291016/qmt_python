from dataclasses import dataclass, field
from datetime import datetime
from .order_status import OrderStatus

@dataclass
class Order:
    order_id: str
    symbol: str
    side: str  # 买/卖
    price: float
    quantity: int
    status: OrderStatus = OrderStatus.NEW
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    account: str = ""
    ext: dict = field(default_factory=dict)  # 扩展字段 