from enum import Enum

class OrderStatus(Enum):
    NEW = "新订单"
    SUBMITTED = "已报"
    PARTIALLY_FILLED = "部分成交"
    FILLED = "全部成交"
    CANCELLED = "已撤销"
    REJECTED = "拒单"
    FAILED = "失败" 