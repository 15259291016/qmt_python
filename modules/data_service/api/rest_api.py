# modules/data_service/api/rest_api.py
from fastapi import FastAPI, Query
from typing import List, Optional
import pymysql
from modules.data_service.config import MYSQL_CONFIG
import pandas as pd
from tornado.web import RequestHandler
from modules.data_service.integration import get_data_service_manager

app = FastAPI(title="行情与采集服务API")

def get_conn():
    return pymysql.connect(**MYSQL_CONFIG)

@app.get("/quote/daily")
def get_daily(ts_code: str, start: str, end: str):
    """查询日线行情"""
    sql = '''
    SELECT * FROM stock_daily WHERE ts_code=%s AND trade_date BETWEEN %s AND %s ORDER BY trade_date
    '''
    with get_conn() as conn:
        df = pd.read_sql(sql, conn, params=(ts_code, start, end))
    return df.to_dict(orient='records')

@app.get("/collect/progress")
def get_progress(ts_code: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None):
    """查询采集进度"""
    sql = 'SELECT * FROM collect_progress WHERE 1=1'
    params = []
    if ts_code:
        sql += ' AND ts_code=%s'
        params.append(ts_code)
    if start and end:
        sql += ' AND trade_date BETWEEN %s AND %s'
        params.extend([start, end])
    with get_conn() as conn:
        df = pd.read_sql(sql, conn, params=params)
    return df.to_dict(orient='records')

@app.get("/collect/log")
def get_log(ts_code: Optional[str] = None, status: Optional[str] = None, limit: int = 100):
    """查询采集日志"""
    sql = 'SELECT * FROM collect_log WHERE 1=1'
    params = []
    if ts_code:
        sql += ' AND ts_code=%s'
        params.append(ts_code)
    if status:
        sql += ' AND status=%s'
        params.append(status)
    sql += ' ORDER BY create_time DESC LIMIT %s'
    params.append(limit)
    with get_conn() as conn:
        df = pd.read_sql(sql, conn, params=params)
    return df.to_dict(orient='records')

class BarDataAPI(RequestHandler):
    async def get(self):
        ts_code = self.get_argument('ts_code')
        start = self.get_argument('start')
        end = self.get_argument('end')
        freq = self.get_argument('freq', '1min')
        manager = get_data_service_manager()
        bars = manager.get_bar_data(ts_code, start, end, freq)
        self.set_header('Content-Type', 'application/json')
        self.write({'data': [bar.dict() for bar in bars]}) 