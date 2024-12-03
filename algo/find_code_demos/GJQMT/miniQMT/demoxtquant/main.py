

def init(C):
    pass
def after_init(C):
    pass

def handlebar(C):
    pass

if __name__ == '__main__':
    import sys
    from xtquant.qmttools import run_strategy_file

    param = {
        'stock_code': '000300.SH',
        'period': '1d',
        'start_time': '2020-01-01 00:00:00',
        'end_time': '2023-01-01 00:00:00',
        'trade_mode': 'backtest',
        'quote_mode': 'history',
        'dividend_type': 'front_ratio',
    }

    user_script = sys.argv[0]
    print(user_script)
    run_strategy_file(user_script, param=param)