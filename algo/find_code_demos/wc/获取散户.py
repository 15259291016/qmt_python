import pywencai as pywc
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import pandas as pd

load_dotenv()

class WC:
    def __init__(self, token=''):
        self.data_dict = {
            "0":["散户指标", self.f0],
            "1":["主板且非st,流通市值>12亿且<150亿,昨日涨停,今日的前10日的区间涨幅<25,今日的前10日的涨幅>9.8的次数<2,今日竞价量比>12,竞价金额>1500万,今日竞价涨幅<9.8,竞价量/自由流通股<0.022,今日特大单净量>-0.12,今日特大单净额>-2000万,主力控盘比例>20", self.f1],      #需要情绪周期配合
            # "1":["主板且非st,流通市值>12亿且<150亿,昨日涨停,今日的前10日的区间涨幅<25,今日的前10日的涨幅>9.8的次数<2,今日竞价量比>12,竞价金额>1500万,今日竞价涨幅<9.8", self.1],      #需要情绪周期配合
            "2":["上海凤凰、四川长虹、南京公用、欧菲光、东百集团、通富微电、百大集团、哈森股份、东风股份、宗申动力、豪尔赛、广百股份、新里程、粤传媒", self.f2],      #需要情绪周期配合
            # "2":["实益达、上海凤凰、佳力图、南京化纤、电光科技、好想你", self.f2],      #需要情绪周期配合
                     }
    def f0(self, info:str, stock_name:str):
        print(pywc.get(query=f"{stock_name}散户指标"))
        
    def f1(self, info:str):
        print(pywc.get(query=info))

    def f2(self, stock:str):
        df = pywc.get(query=f"{stock}散户指标")
        print(df)

    def get_single_stock_sh(self):
        return wc.get(query=f"散户指标排名5500-5600")
    
    def get_stock_dde_info(self, stock_name):
        # return wc.get(query=f"{stock_name}散户指标")
        # return wc.get(query=f"首板有哪些")
        # return wc.get(query=f"主力资金流入,剔除ST,剔除次新,剔除北交所,形成拉升通道")
        return wc.get(query=f"主板且非st,流通市值>12亿且<150亿,昨日涨停,今日的前10日的区间涨幅<25,今日的前10日的涨幅>9.8的次数<2,今日竞价量比>12,竞价金额>1500万,今日竞价涨幅<9.8,竞价量/自由流通股<0.022,今日特大单净量>-0.12,今日特大单净额>-2000万,主力控盘比例>20,")

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
# ['大连友谊', '中百集团', '兰州黄河', '河化股份']
# [ ]:

# save_stock_dde_data_all_today(WC().get_stock_dde_info('晶雪节能'))

wc = WC()
wc.data_dict["0"][1](wc.data_dict["0"][0], "来伊份")
# wc.data_dict["2"][1](wc.data_dict["2"][0])