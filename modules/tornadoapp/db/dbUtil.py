from beanie import init_beanie as _init_beanie
from motor.motor_tornado import MotorClient

from modules.tornadoapp.model import demomodel


class MotorClient(MotorClient):
    def __init__(self, config, db_name):
        # db_url = get_common_db_url(config)
        db_url = "mongodb://admin:123456@127.0.0.1:27017"
        super().__init__(db_url, maxPoolSize=config["max_pool_size"], maxConnecting=1, compressors="snappy")
        self.db = self[db_name]
        
config = {
        "max_pool_size": 10,
    }
db_name = "nzctest"
demo_db_client = MotorClient(config, db_name)

async def init_beanie():
    database = demo_db_client.db
    await _init_beanie(database=database, document_models=[demomodel.DemoModel])


if __name__ == "__main__":
    config = {
        "max_pool_size": 10,
    }
    db_name = "nzctest1"
    db_client = MotorClient(config, db_name)