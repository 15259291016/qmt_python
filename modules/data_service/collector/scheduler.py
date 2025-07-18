# modules/data_service/collector/scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from modules.data_service.collector.daily_collector import collect_all_daily
from datetime import datetime, timedelta

def daily_job():
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    print(f'自动采集任务启动: {yesterday} ~ {today}')
    collect_all_daily(start_date=yesterday, end_date=today, only_unfinished=True)

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(daily_job, 'cron', hour=18, minute=0)  # 每天18:00自动采集
    print('定时采集调度器已启动...')
    scheduler.start() 