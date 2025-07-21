# modules/data_service/datasource/tushare_pro.py
import tushare as ts
from modules.data_service.config import TUSHARE_TOKEN
from modules.data_service.schema import BarData, TickData
from modules.data_service.datasource.source_base import MarketDataSourceBase
import pandas as pd

class TushareProSource(MarketDataSourceBase):
    def __init__(self):
        self.pro = ts.pro_api(TUSHARE_TOKEN)

    def get_stock_list(self):
        df = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code')
        return df['ts_code'].tolist()

    def get_bar_data(self, ts_code, start_time, end_time, freq):
        import time
        # freq: '1min', '5min', '15min', '30min', '60min', 'day'
        if freq == 'day':
            df = self.pro.daily(ts_code=ts_code, start_date=start_time, end_date=end_time)
            time.sleep(31)  # 限频：每分钟最多2次
        else:
            # tushare分钟线接口
            df = self.pro.query('stk_mins', ts_code=ts_code, start_date=start_time, end_date=end_time, freq=freq)
            time.sleep(31)  # 限频：每分钟最多2次
        bars = []
        for _, row in df.iterrows():
            bars.append(BarData(
                ts_code=str(row['ts_code']),
                trade_time=str(row.get('trade_time', row.get('trade_date', ''))),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['vol']),
                amount=float(row.get('amount', 0) or 0),
                freq=str(freq)
            ))
        return bars

    def get_tick_data(self, ts_code, start_time, end_time):
        # tushare不直接支持tick，可用level2或其他源实现
        raise NotImplementedError("Tushare不支持tick数据")

    def get_snapshot(self, ts_code, trade_time):
        # 可用实时行情接口实现
        raise NotImplementedError("Tushare不支持盘口快照") 