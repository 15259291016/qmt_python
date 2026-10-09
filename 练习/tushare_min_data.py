import pandas as pd
import tushare as ts
import os
from datetime import datetime, timedelta
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化tushare API
pro = ts.pro_api('gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482')

def create_directory(path):
    """创建目录"""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"创建目录: {path}")

def get_stock_list():
    """获取股票列表"""
    try:
        # 获取所有A股股票列表
        stock_list = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
        logger.info(f"获取到 {len(stock_list)} 只股票")
        return stock_list
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return pd.DataFrame()

def download_minute_data(ts_code, start_date, end_date, freq='1min', max_retries=3):
    """
    下载分钟级数据，带重试机制
    
    Args:
        ts_code: 股票代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        freq: 频率 ('1min', '5min', '15min', '30min', '60min')
        max_retries: 最大重试次数
    """
    for attempt in range(max_retries):
        try:
            # 使用tushare的分钟级数据接口
            df = pro.stk_mins(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                freq=freq
            )
            
            if df is not None and not df.empty:
                logger.info(f"成功下载 {ts_code} 的分钟级数据，共 {len(df)} 条记录")
                return df
            else:
                logger.warning(f"{ts_code} 在指定时间段内无数据")
                return pd.DataFrame()
                
        except Exception as e:
            error_msg = str(e)
            if "每分钟最多访问该接口2次" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = 60  # 等待60秒
                    logger.warning(f"API限制，等待 {wait_time} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"下载 {ts_code} 数据失败，已达到最大重试次数: {e}")
                    return pd.DataFrame()
            else:
                logger.error(f"下载 {ts_code} 数据失败: {e}")
                return pd.DataFrame()
    
    return pd.DataFrame()

def save_data(df, ts_code, freq, save_dir):
    """保存数据到文件"""
    if df is not None and not df.empty:
        # 创建文件名
        filename = f"{ts_code}_{freq}_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = os.path.join(save_dir, filename)
        
        # 保存数据
        df.to_csv(filepath, index=False)
        logger.info(f"数据已保存到: {filepath}")
        return filepath
    return None

def main():
    """主函数"""
    # 设置参数
    start_date = "20250301"
    end_date = "20250711"
    freq = "1min"  # 1分钟数据
    
    # 创建保存目录
    save_dir = "data/min"
    create_directory(save_dir)
    
    # 获取股票列表
    stock_list = get_stock_list()
    if stock_list.empty:
        logger.error("无法获取股票列表，程序退出")
        return
    
    # 限制下载的股票数量（避免API限制）
    max_stocks = 10  # 减少到10只股票，避免API限制
    stock_list = stock_list.head(max_stocks)
    
    logger.info(f"开始下载 {len(stock_list)} 只股票的分钟级数据")
    logger.info(f"时间范围: {start_date} 到 {end_date}")
    logger.info(f"数据频率: {freq}")
    logger.info("注意：由于API限制，每分钟只能访问2次，下载速度较慢")
    
    # 下载数据
    success_count = 0
    failed_count = 0
    
    for index, row in stock_list.iterrows():
        ts_code = row['ts_code']
        logger.info(f"正在下载 {ts_code} ({row['name']}) 的数据... ({index+1}/{len(stock_list)})")
        
        # 下载数据
        df = download_minute_data(ts_code, start_date, end_date, freq)
        
        if not df.empty:
            # 保存数据
            filepath = save_data(df, ts_code, freq, save_dir)
            if filepath:
                success_count += 1
        else:
            failed_count += 1
        
        # 添加延时避免API限制（每次下载后等待30秒）
        if index < len(stock_list) - 1:  # 最后一只股票不需要等待
            logger.info("等待30秒后继续下载下一只股票...")
            time.sleep(30)
    
    # 输出统计信息
    logger.info("=" * 50)
    logger.info("下载完成统计:")
    logger.info(f"成功下载: {success_count} 只股票")
    logger.info(f"下载失败: {failed_count} 只股票")
    logger.info(f"数据保存在: {os.path.abspath(save_dir)}")

if __name__ == "__main__":
    main()