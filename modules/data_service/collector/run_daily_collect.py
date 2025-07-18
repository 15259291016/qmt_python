# modules/data_service/collector/run_daily_collect.py
import argparse
from modules.data_service.collector.daily_collector import collect_all_daily

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tushare Pro 日线行情采集')
    parser.add_argument('--start', type=str, required=True, help='采集开始日期，如20230701')
    parser.add_argument('--end', type=str, required=True, help='采集结束日期，如20230718')
    parser.add_argument('--stock', type=str, nargs='*', help='股票代码列表，留空为全市场')
    parser.add_argument('--threads', type=int, default=4, help='并发线程数')
    parser.add_argument('--resume', action='store_true', help='仅采集未完成任务（断点续传）')
    args = parser.parse_args()

    collect_all_daily(
        start_date=args.start,
        end_date=args.end,
        stock_list=args.stock,
        max_workers=args.threads,
        only_unfinished=args.resume
    ) 