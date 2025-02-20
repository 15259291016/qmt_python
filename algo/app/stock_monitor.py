# stock_monitor.py
import threading
import easyquotation
import pandas as pd
import time
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine

# 加载环境变量
load_dotenv()

# 数据库配置
user = os.getenv("PG_USER")
password = os.getenv("PG_PASSWORD")
host = os.getenv("PG_HOST")
port = os.getenv("PG_PORT")
dbname = os.getenv("PG_DBNAME")

# 创建数据库连接
db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
engine = create_engine(db_url)

# 初始化股票行情接口
quotation = easyquotation.use('tencent')  # 使用腾讯行情

class StockMonitorThread(threading.Thread):
    """
    股票监控线程类，用于实时监控指定股票的行情数据并保存到数据库。
    """
    def __init__(self, stock_names, interval=3):
        """
        初始化线程。

        参数:
            stock_names (list): 要监控的股票名称列表。
            interval (int): 数据更新间隔时间（秒）。
        """
        super().__init__()
        self.stock_names = stock_names
        self.interval = interval
        self.running = True

    def is_trade_time(self):
        """判断当前时间是否为交易时间"""
        now = time.localtime()
        return (9 <= now.tm_hour < 15) and not (now.tm_hour == 12 or (now.tm_hour == 9 and now.tm_min < 24))

    def save_to_db(self, data, table_name):
        """保存数据到数据库"""
        df = pd.DataFrame(data)
        df.to_sql(table_name, engine, if_exists='append', index=False)
        print(f"Data inserted into {table_name} successfully")

    def monitor_stock(self, stock_name, stock_code):
        """监控单个股票的行情数据"""
        while self.running:
            if not self.is_trade_time():
                time.sleep(60)
                continue

            try:
                # 获取实时行情数据
                stock_data = quotation.real(stock_code)[stock_code]
                rename_mapping = {
                    'PE': 'pe',
                    'PB': 'pb',
                    '涨跌(%)': '涨跌百分比',
                    '价格/成交量(手)/成交额': '价格成交量成交额',
                    '成交量(手)': '成交量手',
                    '成交额(万)': '成交额万',
                    '市盈(动)': '市盈动',
                    '市盈(静)': '市盈静'
                }
                renamed_data = {rename_mapping.get(k, k): v for k, v in stock_data.items()}
                renamed_data = {k: [v] for k, v in renamed_data.items()}  # 转换为单行 DataFrame
                renamed_data["unknown"] = [1]  # 添加默认字段

                # 保存到数据库
                self.save_to_db(renamed_data, 'easyquotation_trade_stock_data_sec')

                # 打印关键信息
                print(f"{stock_name} ({stock_code}): {stock_data['now']}, {stock_data['涨跌(%)']}, {stock_data['量比']}, {stock_data['均价']}")

            except Exception as e:
                print(f"Error: {e}")

            time.sleep(self.interval)

    def run(self):
        """线程运行的主逻辑"""
        for stock_name in self.stock_names:
            stock_code = self.get_stock_code(stock_name)  # 假设有一个函数可以根据股票名称获取代码
            if stock_code:
                self.monitor_stock(stock_name, stock_code)

    def get_stock_code(self, stock_name):
        """根据股票名称获取股票代码（示例逻辑）"""
        # 这里可以根据实际情况实现股票名称到代码的映射
        stock_code_map = {
            '嵘泰股份': '605133',
            '远程股份': '002692',
            '海鸥股份': '603269',
            '江海股份': '002484',
            '好想你': '002582',
            '三花智控': '002050',
            '三六零': '601360',
            '飞龙股份': '002536',
            '元隆雅图': '002878',
            '北特科技': '603009',
            '奥飞娱乐': '002292'
        }
        return stock_code_map.get(stock_name)

    def stop(self):
        """停止线程"""
        self.running = False