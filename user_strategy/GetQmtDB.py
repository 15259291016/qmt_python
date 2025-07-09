from xtquant import xtdata, xttrader
import pandas as pd
import time
import logging
import os
import threading
from queue import Queue

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class XtQuantDataInterface:
    def __init__(self, qmt_path, account, cache_dir='data_cache'):
        """
        初始化xtquant数据接口（适配国金证券）
        :param qmt_path: QMT安装路径
        :param account: 国金证券账号
        :param cache_dir: 数据缓存目录
        """
        self.qmt_path = qmt_path
        self.account = account
        self.cache_dir = cache_dir
        self.xt_trader = None
        self.session_id = int(time.time())
        self.data_queue = Queue()  # 用于存储实时数据的队列
        self.realtime_thread = None  # 实时数据线程
        self.is_running = False  # 控制实时数据线程的运行状态

        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)

        # 检查 QMT 路径和账号
        self._check_config()

        # 初始化xtquant
        self._init_xtquant()

    def _check_config(self):
        """检查 QMT 路径和账号"""
        if not os.path.exists(self.qmt_path):
            raise FileNotFoundError(f"QMT 路径不存在: {self.qmt_path}")
        if not self.account:
            raise ValueError("账号不能为空")

    def _init_xtquant(self):
        """初始化xtquant接口并登录国金证券"""
        try:
            # 初始化xttrader并登录国金证券
            logging.info(f"正在初始化xtquant，QMT路径: {self.qmt_path}")
            self.xt_trader = xttrader.XtQuantTrader(self.qmt_path, self.session_id)
            self.xt_trader.start()
            callback = MyXtQuantTraderCallback()  # 自定义回调类
            self.xt_trader.register_callback(callback)
            logging.info(f"正在连接国金证券，账号: {self.account}")
            connect_result = self.xt_trader.connect()
            if connect_result == 0:
                logging.info("国金证券登录成功")
            else:
                logging.error(f"国金证券登录失败，返回码: {connect_result}")
                raise Exception(f"国金证券登录失败，返回码: {connect_result}")
        except Exception as e:
            logging.error(f"xtquant 初始化失败: {e}")
            raise

    def get_historical_data(self, stock_codes, start_date, end_date, period='1d', force_update=False):
        """
        获取历史数据（支持多线程并发获取）
        :param stock_codes: 股票代码列表，例如 ['000001.SZ', '600000.SH']
        :param start_date: 开始日期，格式 'YYYYMMDD'
        :param end_date: 结束日期，格式 'YYYYMMDD'
        :param period: 数据周期，默认 '1d'（日线），可选 '1m'（分钟线）
        :param force_update: 是否强制更新缓存数据
        :return: 包含历史数据的DataFrame字典，键为股票代码
        """
        historical_data = {}
        threads = []

        def fetch_data(stock_code):
            """单个股票的数据获取函数"""
            cache_file = os.path.join(self.cache_dir, f"{stock_code}_{start_date}_{end_date}_{period}.csv")
            if not force_update and os.path.exists(cache_file):
                # 从缓存加载数据
                logging.info(f"从缓存加载历史数据：{stock_code}")
                df = pd.read_csv(cache_file, parse_dates=['Date'], index_col='Date')
            else:
                # 从xtquant获取数据
                logging.info(f"从xtquant获取历史数据：{stock_code}")
                data = xtdata.get_market_data(field_list=[], stock_list=[stock_code], period=period,
                                              start_time=start_date, end_time=end_date)
                if not data or stock_code not in data:
                    logging.warning(f"未获取到数据：{stock_code}")
                    return
                df = pd.DataFrame(data[stock_code])
                df = df.rename(columns={
                    'time': 'Date',
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                # 保存到缓存
                df.to_csv(cache_file)
            historical_data[stock_code] = df

        # 使用多线程并发获取数据
        for stock_code in stock_codes:
            thread = threading.Thread(target=fetch_data, args=(stock_code,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        return historical_data

    def get_realtime_data(self, stock_codes):
        """
        获取实时数据
        :param stock_codes: 股票代码列表，例如 ['000001.SZ', '600000.SH']
        :return: 包含实时数据的字典，键为股票代码
        """
        realtime_data = {}
        for stock_code in stock_codes:
            logging.info(f"获取实时数据：{stock_code}")
            data = xtdata.get_full_tick([stock_code])
            if not data or stock_code not in data:
                logging.warning(f"未获取到实时数据：{stock_code}")
                continue
            realtime_data[stock_code] = data[stock_code]
        return realtime_data

    def start_realtime_monitoring(self, stock_codes):
        """
        启动实时数据监控（多线程）
        :param stock_codes: 股票代码列表，例如 ['000001.SZ', '600000.SH']
        """
        self.is_running = True
        self.realtime_thread = threading.Thread(target=self._realtime_monitoring, args=(stock_codes,))
        self.realtime_thread.start()
        logging.info("实时数据监控已启动")

    def stop_realtime_monitoring(self):
        """停止实时数据监控"""
        self.is_running = False
        if self.realtime_thread:
            self.realtime_thread.join()
        logging.info("实时数据监控已停止")

    def _realtime_monitoring(self, stock_codes):
        """实时数据监控线程"""

        def on_tick(data):
            """实时数据回调函数"""
            self.data_queue.put(data)

        # 订阅实时数据
        for stock_code in stock_codes:
            xtdata.subscribe_quote(stock_code, callback=on_tick)

        # 持续处理实时数据
        while self.is_running:
            if not self.data_queue.empty():
                data = self.data_queue.get()
                logging.info(f"收到实时数据：{data}")
            time.sleep(1)

    def clean_data(self, df):
        """
        数据清洗：处理缺失值和异常值
        :param df: 输入的DataFrame
        :return: 清洗后的DataFrame
        """
        # 处理缺失值
        df.fillna(method='ffill', inplace=True)  # 前向填充
        df.fillna(method='bfill', inplace=True)  # 后向填充
        # 处理异常值（例如价格或成交量为负的情况）
        df[df['Close'] < 0] = None
        df[df['Volume'] < 0] = None
        df.fillna(method='ffill', inplace=True)
        return df


# 自定义xttrader回调类
class MyXtQuantTraderCallback:
    def on_disconnected(self):
        logging.warning("xttrader 连接断开")

    def on_order_status(self, order):
        logging.info(f"订单状态更新：{order}")

    def on_trade(self, trade):
        logging.info(f"成交回报：{trade}")


# 示例使用
if __name__ == "__main__":
    # 配置参数
    qmt_path = r"D:\国金QMT交易端模拟\userdata_mini"
    account = "55005056"  # 替换为国金证券账号

    # 初始化数据接口
    try:
        data_interface = XtQuantDataInterface(qmt_path, account, cache_dir='data_cache')
    except Exception as e:
        logging.error(f"初始化失败: {e}")
        exit(1)

    # 获取历史数据
    stock_codes = ['000001.SZ', '600000.SH']
    historical_data = data_interface.get_historical_data(stock_codes, '20250301', '20250305')
    for stock_code, data in historical_data.items():
        print(f"{stock_code} 历史数据：")
        print(data.head())

    # 启动实时数据监控
    data_interface.start_realtime_monitoring(stock_codes)

    # 保持程序运行以接收实时数据
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        data_interface.stop_realtime_monitoring()
        print("程序退出")
