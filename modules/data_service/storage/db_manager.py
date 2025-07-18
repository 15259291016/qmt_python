# modules/data_service/storage/db_manager.py
import pymysql
import pandas as pd
from modules.data_service.config import MYSQL_CONFIG
from datetime import datetime

def get_conn():
    return pymysql.connect(**MYSQL_CONFIG)

def create_table():
    sql_daily = '''
    CREATE TABLE IF NOT EXISTS stock_daily (
        ts_code VARCHAR(16),
        trade_date VARCHAR(8),
        open FLOAT,
        high FLOAT,
        low FLOAT,
        close FLOAT,
        pre_close FLOAT,
        `change` FLOAT,
        pct_chg FLOAT,
        vol FLOAT,
        amount FLOAT,
        PRIMARY KEY (ts_code, trade_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    '''
    sql_progress = '''
    CREATE TABLE IF NOT EXISTS collect_progress (
        ts_code VARCHAR(16),
        trade_date VARCHAR(8),
        status VARCHAR(16), -- pending, success, fail
        last_update DATETIME,
        error_msg TEXT,
        PRIMARY KEY (ts_code, trade_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    '''
    sql_log = '''
    CREATE TABLE IF NOT EXISTS collect_log (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        ts_code VARCHAR(16),
        trade_date VARCHAR(8),
        action VARCHAR(32),
        status VARCHAR(16),
        message TEXT,
        elapsed FLOAT,
        create_time DATETIME
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    '''
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_daily)
            cur.execute(sql_progress)
            cur.execute(sql_log)
        conn.commit()

def save_daily_data(ts_code, df: pd.DataFrame):
    if df is None or df.empty:
        return
    create_table()
    with get_conn() as conn:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                sql = '''
                REPLACE INTO stock_daily (ts_code, trade_date, open, high, low, close, pre_close, `change`, pct_chg, vol, amount)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                '''
                cur.execute(sql, (
                    row['ts_code'], row['trade_date'], row['open'], row['high'], row['low'],
                    row['close'], row['pre_close'], row['change'], row['pct_chg'], row['vol'], row['amount']
                ))
        conn.commit()

def update_progress(ts_code, trade_date, status, error_msg=None):
    create_table()
    with get_conn() as conn:
        with conn.cursor() as cur:
            sql = '''
            REPLACE INTO collect_progress (ts_code, trade_date, status, last_update, error_msg)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cur.execute(sql, (ts_code, trade_date, status, datetime.now(), error_msg))
        conn.commit()

def log_collect(ts_code, trade_date, action, status, message, elapsed):
    create_table()
    with get_conn() as conn:
        with conn.cursor() as cur:
            sql = '''
            INSERT INTO collect_log (ts_code, trade_date, action, status, message, elapsed, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cur.execute(sql, (ts_code, trade_date, action, status, message, elapsed, datetime.now()))
        conn.commit()

def get_unfinished_tasks(start_date, end_date, stock_list=None):
    """获取未采集或采集失败的任务"""
    create_table()
    with get_conn() as conn:
        with conn.cursor() as cur:
            if stock_list:
                format_strings = ','.join(['%s'] * len(stock_list))
                sql = f'''
                SELECT ts_code, trade_date FROM collect_progress
                WHERE status != 'success' AND trade_date BETWEEN %s AND %s AND ts_code IN ({format_strings})
                '''
                cur.execute(sql, [start_date, end_date] + stock_list)
            else:
                sql = '''
                SELECT ts_code, trade_date FROM collect_progress
                WHERE status != 'success' AND trade_date BETWEEN %s AND %s
                '''
                cur.execute(sql, (start_date, end_date))
            return cur.fetchall() 