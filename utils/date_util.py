import datetime
import pandas as pd

from datetime import datetime, time

def is_trading_time():
    """
    判断当前时间是否为交易时间。
    假设交易时间是周一至周五的上午9:30至下午3:00。
    """
    # 获取当前时间
    now = datetime.now()

    # 判断是否为工作日（周一至周五）
    if now.weekday() >= 5:  # 周六（5）和周日（6）
        return False

    # 定义交易时间范围
    start_time = time(9, 30)  # 上午9:30
    end_time = time(15, 0)    # 下午3:00

    # 获取当前时间的时分秒部分
    current_time = now.time()

    # 判断当前时间是否在交易时间范围内
    if start_time <= current_time <= end_time:
        return True
    else:
        return False



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
