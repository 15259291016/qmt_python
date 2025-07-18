# modules/data_service/integration.py
"""
数据服务集成模块
提供与main.py量化交易系统的交互接口
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from modules.data_service.collector.daily_collector import collect_all_daily
from modules.data_service.storage.db_manager import get_conn
import pandas as pd
from modules.data_service.datasource.tushare_pro import TushareProSource
from modules.data_service.manager import DataServiceManager

logger = logging.getLogger(__name__)

def get_data_service_manager() -> DataServiceManager:
    """获取统一数据服务管理器实例，支持多源主备切换"""
    tushare_source = TushareProSource()
    # 未来可扩展更多源
    return DataServiceManager([tushare_source]) 