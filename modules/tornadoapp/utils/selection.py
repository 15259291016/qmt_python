import pandas as pd
from .config import STOCK_POOL_SIGNALS, MIN_VOLUME, MIN_PRICE
from .signals import add_all_signals

def select_stock_pool(df, date_str=None, signals=None, min_volume=None, min_price=None):
    """
    选股池筛选
    :param df: DataFrame，已包含信号列
    :param date_str: 日期字符串，筛选当日数据
    :param signals: 信号组合，默认为config中的STOCK_POOL_SIGNALS
    :param min_volume: 最小成交量
    :param min_price: 最低股价
    :return: DataFrame，推荐股票池
    """
    if signals is None:
        signals = STOCK_POOL_SIGNALS
    if min_volume is None:
        min_volume = MIN_VOLUME
    if min_price is None:
        min_price = MIN_PRICE

    # 只取指定日期
    if date_str is not None and 'trade_time' in df.columns:
        df = df[df['trade_time'].dt.date == pd.to_datetime(date_str).date()]

    # 只取最后一行（最新时刻）
    if not df.empty:
        last_row = df.iloc[-1]
        # 多信号组合
        signal_flag = all([last_row.get(sig, False) for sig in signals])
        volume_flag = last_row.get('vol', 0) >= min_volume
        price_flag = last_row.get('close', 0) >= min_price
        if signal_flag and volume_flag and price_flag:
            return pd.DataFrame([last_row])
    return pd.DataFrame([])

def batch_select_stock_pool(data_dir, date_str=None):
    """
    批量选股，遍历目录下所有股票数据
    :param data_dir: 数据目录
    :param date_str: 日期字符串
    :return: 推荐股票池DataFrame
    """
    import os
    selected = []
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and '_1min_' in f]
    for file in files:
        df = pd.read_csv(f'{data_dir}/{file}')
        if 'trade_time' in df.columns:
            df['trade_time'] = pd.to_datetime(df['trade_time'])
        # 自动补全信号
        df = add_all_signals(df)
        row = select_stock_pool(df, date_str)
        if not row.empty:
            row['ts_code'] = file.split('_')[0]
            selected.append(row)
    if selected:
        return pd.concat(selected, ignore_index=True)
    else:
        return pd.DataFrame([]) 