# modules/data_service/config.py
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '')

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'stock_data'),
    'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4')
} 