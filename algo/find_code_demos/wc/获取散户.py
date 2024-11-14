import pywencai as wc
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import pandas as pd

load_dotenv()

class WC:
    def __init__(self, token=''):
        pass

    def get_single_stock_sh(self):
        return wc.get(query=f"散户指标排名5500-5600")
    
    def get_stock_dde_info(self, stock_name):
        return wc.get(query=f"{stock_name}散户指标")

    def get_all_stock_list(self):
        pass


# save data to pgsql wc_data
def save_stock_dde_data(df: pd.DataFrame):
    host = os.getenv("HOST")
    port = int(os.getenv("PORT"))
    wc_data_url = os.getenv("PGSQL_ENGINE_URL_WCDATA")
    engine = create_engine(wc_data_url)
    print(df)
    # df.to_sql(name="", con=engine, index=False, if_exists='replace')

# save data to pgsql wc_data
def save_stock_dde_data_all_today(df: pd.DataFrame):
    host = os.getenv("HOST")
    port = int(os.getenv("PORT"))
    wc_data_url = os.getenv("PGSQL_ENGINE_URL_WCDATA")
    engine = create_engine(wc_data_url)
    print(df)
    # df.to_sql(name="", con=engine, index=False, if_exists='replace')

save_data(WC().get_stock_dde_info('启迪环境'))