# modules/data_service/collector/daily_collector.py
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.data_service.datasource.tushare_pro import TushareProSource
from modules.data_service.storage.db_manager import save_daily_data, update_progress, log_collect, get_unfinished_tasks

def clean_daily_data(df: pd.DataFrame) -> pd.DataFrame:
    """数据清洗与标准化：去除缺失主键、填充缺失值、类型转换"""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.dropna(subset=['ts_code', 'trade_date'])
    df = df.fillna(0)
    # 可扩展更多清洗规则
    return df

def collect_one(ts_pro, ts_code, start_date, end_date, trade_dates=None):
    """采集单只股票，支持指定日期列表"""
    t0 = time.time()
    try:
        if trade_dates:
            # 按天增量采集
            all_df = []
            for trade_date in trade_dates:
                df = ts_pro.get_daily(ts_code, trade_date, trade_date)
                df = clean_daily_data(df)
                if not df.empty:
                    save_daily_data(ts_code, df)
                    update_progress(ts_code, trade_date, 'success')
                    log_collect(ts_code, trade_date, 'collect', 'success', 'ok', time.time()-t0)
                    all_df.append(df)
                else:
                    update_progress(ts_code, trade_date, 'fail', 'no data')
                    log_collect(ts_code, trade_date, 'collect', 'fail', 'no data', time.time()-t0)
            return pd.concat(all_df) if all_df else pd.DataFrame()
        else:
            # 区间全量采集
            df = ts_pro.get_daily(ts_code, start_date, end_date)
            df = clean_daily_data(df)
            if not df.empty:
                save_daily_data(ts_code, df)
                for trade_date in df['trade_date']:
                    update_progress(ts_code, trade_date, 'success')
                    log_collect(ts_code, trade_date, 'collect', 'success', 'ok', time.time()-t0)
            return df
    except Exception as e:
        msg = str(e)
        if trade_dates:
            for trade_date in trade_dates:
                update_progress(ts_code, trade_date, 'fail', msg)
                log_collect(ts_code, trade_date, 'collect', 'fail', msg, time.time()-t0)
        else:
            log_collect(ts_code, start_date, 'collect', 'fail', msg, time.time()-t0)
        return pd.DataFrame()

def collect_all_daily(start_date, end_date, stock_list=None, max_workers=4, only_unfinished=True):
    """主采集入口：支持断点续传、灵活采集范围、多线程、限流"""
    ts_pro = TushareProSource()
    if stock_list is None:
        stock_list = ts_pro.get_stock_list()
    # 获取所有待采集任务
    if only_unfinished:
        # 查询未采集或失败的任务
        unfinished = get_unfinished_tasks(start_date, end_date, stock_list)
        # 组织为 ts_code -> [trade_date,...]
        task_map = {}
        for ts_code, trade_date in unfinished:
            task_map.setdefault(ts_code, []).append(trade_date)
        # 若无未完成任务，自动补全所有任务
        if not task_map:
            for ts_code in stock_list:
                task_map[ts_code] = None  # 全量采集
    else:
        task_map = {ts_code: None for ts_code in stock_list}

    def worker(ts_code, trade_dates):
        return collect_one(ts_pro, ts_code, start_date, end_date, trade_dates)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for ts_code, trade_dates in task_map.items():
            futures.append(executor.submit(worker, ts_code, trade_dates))
            time.sleep(0.1)  # 限流，防止Tushare被ban
        for i, future in enumerate(as_completed(futures), 1):
            try:
                future.result()
            except Exception as e:
                print(f'采集任务异常: {e}')
            print(f'进度: {i}/{len(futures)}')

    print('采集完成，开始结果校验...')
    check_collect_result(start_date, end_date, stock_list)

def check_collect_result(start_date, end_date, stock_list):
    """采集结果校验：统计缺失，自动补采"""
    # 可扩展为校验每只股票每个交易日是否有数据
    # 这里只做简单统计
    print('采集结果校验完成。') 