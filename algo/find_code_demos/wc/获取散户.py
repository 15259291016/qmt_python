import pywencai as wc


class WC:
    def __init__(self, token=''):
        pass

    def get_single_stock_sh(self, stock_name):
        return wc.get(query=f"{stock_name}散户")

    def get_all_stock_list(self):
        pass


print(WC().get_single_stock_sh('启迪环境'))
