from typing import List
from modules.data_service.datasource.source_base import MarketDataSourceBase
from modules.data_service.schema import BarData, TickData

class DataServiceManager:
    def __init__(self, sources: List[MarketDataSourceBase]):
        self.sources = sources  # 按优先级排列

    def get_bar_data(self, ts_code, start_time, end_time, freq) -> List[BarData]:
        for src in self.sources:
            try:
                return src.get_bar_data(ts_code, start_time, end_time, freq)
            except Exception as e:
                print(f"数据源{src}异常: {e}")
                continue
        raise Exception("所有数据源均不可用")

    def get_tick_data(self, ts_code, start_time, end_time) -> List[TickData]:
        for src in self.sources:
            try:
                return src.get_tick_data(ts_code, start_time, end_time)
            except Exception as e:
                print(f"数据源{src}异常: {e}")
                continue
        raise Exception("所有数据源均不可用")

    def get_snapshot(self, ts_code, trade_time):
        for src in self.sources:
            try:
                return src.get_snapshot(ts_code, trade_time)
            except Exception as e:
                print(f"数据源{src}异常: {e}")
                continue
        raise Exception("所有数据源均不可用") 