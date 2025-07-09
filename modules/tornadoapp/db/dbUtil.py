import os
from beanie import init_beanie as _init_beanie
from motor.motor_tornado import MotorClient
from dotenv import load_dotenv

from modules.tornadoapp.model import demomodel
from modules.tornadoapp.model.user_model import User, UserSession

# 加载环境变量
load_dotenv()


class CustomMotorClient(MotorClient):
    """自定义MongoDB客户端类"""
    
    def __init__(self, config, db_name):
        # 从环境变量获取MongoDB连接信息
        mongo_host = os.getenv("MONGO_HOST", "127.0.0.1")
        mongo_port = os.getenv("MONGO_PORT", "27017")
        mongo_username = os.getenv("MONGO_USERNAME", "admin")
        mongo_password = os.getenv("MONGO_PASSWORD", "123456")
        
        # 构建MongoDB连接URL
        db_url = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}"
        
        super().__init__(
            db_url, 
            maxPoolSize=config.get("max_pool_size", 10), 
            maxConnecting=1, 
            compressors="snappy"
        )
        self.db = self[db_name]


# 默认配置
DEFAULT_CONFIG = {
    "max_pool_size": 10,
}

# 默认数据库名
DEFAULT_DB_NAME = "nzctest"

# 创建默认数据库客户端实例
demo_db_client = CustomMotorClient(DEFAULT_CONFIG, DEFAULT_DB_NAME)


async def init_beanie():
    """初始化Beanie ODM"""
    database = demo_db_client.db
    await _init_beanie(
        database=database, 
        document_models=[
            demomodel.DemoModel,
            User,
            UserSession
        ]
    )


def create_db_client(config=None, db_name=None):
    """创建数据库客户端实例的工厂函数"""
    if config is None:
        config = DEFAULT_CONFIG
    if db_name is None:
        db_name = DEFAULT_DB_NAME
    
    return CustomMotorClient(config, db_name)


if __name__ == "__main__":
    # 测试代码
    config = {
        "max_pool_size": 10,
    }
    db_name = "nzctest1"
    db_client = create_db_client(config, db_name)
    print(f"数据库客户端创建成功: {db_name}")