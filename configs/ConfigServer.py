import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def returnConfigPath():
    """
    返回配置文件夹路径（保留兼容性）
    :return:
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(current_path), 'configs')
    return config_path + os.sep


def returnConfigData():
    """
    从环境变量返回配置数据
    :return: 配置字典
    """
    configData = {
        "QMT_PATH": [
            os.getenv("QMT_PATH_1", "D:\\国金QMT交易端模拟\\userdata_mini"),
            os.getenv("QMT_PATH_2", "H:\\Program Files (x86)\\国金证券QMT交易端\\userdata_mini")
        ],
        "account": [
            os.getenv("ACCOUNT_1", "55005056"),
            os.getenv("ACCOUNT_2", "8881667160")
        ],
        "toshare_token": os.getenv("TUSHARE_TOKEN", "gx03013e909f633ecb66722df66b360f070426613316ebf06ecd3482")
    }
    return configData


def get_log_config():
    """
    获取日志配置
    :return: 日志配置字典
    """
    return {
        "log_file": os.getenv("LOG_FILE", "logs/app.log"),
        "log_size_limit": int(os.getenv("LOG_SIZE_LIMIT", "1048576"))
    }
