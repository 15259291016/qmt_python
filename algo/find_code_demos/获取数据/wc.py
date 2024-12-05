import pywencai as wc

class WC:
    def __init__(self, token=''):
        pass

    def get_single_stock_sh(self):
        return wc.get(query=f"散户指标排名5500-5600")
    
    def get_stock_dde_info(self, stock_name):
        return wc.get(query=f"{stock_name} 散户指标")

    def get_all_stock_list(self):
        pass