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
        # freq: '1min', '5min', '15min', '30min', '60min', 'day'
        if freq == 'day':
            df = self.pro.daily(ts_code=ts_code, start_date=start_time, end_date=end_time)
        else:
            # tushare分钟线接口
            df = self.pro.query('stk_mins', ts_code=ts_code, start_date=start_time, end_date=end_time, freq=freq)
        bars = []
        for _, row in df.iterrows():
            bars.append(BarData(
                ts_code=row['ts_code'],
                trade_time=row.get('trade_time', row.get('trade_date', '')),
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['vol'],
                amount=row.get('amount', 0),
                freq=freq
            ))
        return bars

    def get_tick_data(self, ts_code, start_time, end_time):
        # tushare不直接支持tick，可用level2或其他源实现
        raise NotImplementedError("Tushare不支持tick数据")

    def get_snapshot(self, ts_code, trade_time):
        # 可用实时行情接口实现
        raise NotImplementedError("Tushare不支持盘口快照") 