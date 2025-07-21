import datetime
import pandas as pd

from datetime import datetime, time

def is_trading_time():
    """
    判断当前时间是否为中国A股交易时间。
    - 交易日：周一至周五（不含法定节假日）
    - 上午 9:30-11:30，下午 13:00-15:00
    """
    now = datetime.now()
    # 判断是否为工作日（周一至周五）
    if now.weekday() >= 5:  # 周六（5）和周日（6）
        return False
    # 定义交易时间段
    morning_start = time(9, 30)
    morning_end = time(11, 30)
    afternoon_start = time(13, 0)
    afternoon_end = time(15, 0)
    current_time = now.time()
    # 判断是否在交易时间段内
    in_morning = morning_start <= current_time <= morning_end
    in_afternoon = afternoon_start <= current_time <= afternoon_end
    return in_morning or in_afternoon



def get_previous_trading_day():
    now = datetime.now()
    day = now.strftime("%Y-%m-%d")
    previous_trading_day = (pd.Timestamp(day) - pd.offsets.BDay(1)).strftime("%Y-%m-%d")
    return previous_trading_day

def get_today_trade_day(is_format=False):
    now = datetime.now()
    day = now.strftime("%Y-%m-%d")
    if is_format:
        # 将字符串转换为datetime对象
        date_obj = datetime.strptime(day, '%Y-%m-%d')

        # 将datetime对象格式化为所需的字符串格式
        day = date_obj.strftime('%Y%m%d')
    return day
