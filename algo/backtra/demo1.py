from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

import backtrader as bt


class MyStrategy:
    pass


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    data = bt.feeds.YahooFinanceCSVData(
        dataname='algo/backtra/000890.csv',
        fromdate=datetime.datetime(2017, 1, 1),
        todate=datetime.datetime(2023, 12, 31),
        reverse=False)
    cerebro.adddata(data)
    cerebro.addstrategy(MyStrategy)
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot()