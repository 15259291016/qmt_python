from typing import List
from modules.data_service.schema import BarData, TickData

class MarketDataSourceBase:
    def get_bar_data(self, ts_code: str, start_time: str, end_time: str, freq: str) -> List[BarData]:
        raise NotImplementedError

    def get_tick_data(self, ts_code: str, start_time: str, end_time: str) -> List[TickData]:
        raise NotImplementedError

    def get_snapshot(self, ts_code: str, trade_time: str) -> dict:
        raise NotImplementedError 