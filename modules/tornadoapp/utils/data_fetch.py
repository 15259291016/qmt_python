import tushare as ts
import pandas as pd
import os
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pro = ts.pro_api('gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482')

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_stock_list():
    """获取A股股票列表"""
    try:
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
        return df['ts_code'].tolist()
    except Exception as e:
        logging.error(f"获取股票列表失败: {e}")
        return []

def download_minute_data(ts_code, start_date, end_date, freq='1min', max_retry=3):
    """下载单只股票分钟数据，带重试"""
    for attempt in range(max_retry):
        try:
            df = pro.stk_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq)
            if df is not None and not df.empty:
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            if "每分钟最多访问该接口2次" in str(e):
                logging.warning(f"API限速，等待60秒重试...（{ts_code} 第{attempt+1}次）")
                time.sleep(60)
            else:
                logging.error(f"{ts_code} 下载失败: {e}")
                break
    return pd.DataFrame()

def batch_download_minute_data(
    save_dir='data/min',
    start_date='20250301',
    end_date='20250711',
    freq='1min',
    max_stocks=100
):
    create_dir(save_dir)
    stock_list = get_stock_list()
    if not stock_list:
        logging.error("股票列表为空，退出。")
        return
    # 断点续传：已下载的不再重复
    downloaded = set([f.split('_')[0] for f in os.listdir(save_dir) if f.endswith('.csv')])
    count = 0
    for ts_code in stock_list:
        if ts_code in downloaded:
            logging.info(f"{ts_code} 已存在，跳过。")
            continue
        logging.info(f"正在下载 {ts_code} ...")
        df = download_minute_data(ts_code, start_date, end_date, freq)
        if not df.empty:
            file_path = os.path.join(save_dir, f"{ts_code}_{freq}_{end_date}.csv")
            df.to_csv(file_path, index=False)
            logging.info(f"{ts_code} 下载完成，保存到 {file_path}")
        else:
            logging.warning(f"{ts_code} 无数据或下载失败。")
        count += 1
        if count >= max_stocks:
            break
        time.sleep(30)  # API限速
    logging.info("批量下载完成。") 