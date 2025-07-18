from pydantic import BaseModel
from typing import List

class BarData(BaseModel):
    ts_code: str
    trade_time: str  # 精确到分钟/日
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    freq: str  # '1min', '5min', 'day', 'tick'

class TickData(BaseModel):
    ts_code: str
    trade_time: str  # 精确到秒
    price: float
    volume: float
    bid_price: List[float]
    ask_price: List[float]
    bid_volume: List[float]
    ask_volume: List[float] 