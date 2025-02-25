# encoding:gbk
'''
�����������趨�ý��׵Ĺ�Ʊ���ӣ�Ȼ�����ָ����CCIָ�����жϳ���ͳ���
���г���ͳ�������ʱ�����������趨�õĹ�Ʊ����
'''
import pandas as pd
import numpy as np
import talib
import redis
import time

opr = {
    'buy': 23,
    'sell': 24
}


def init(ContextInfo):
    account = 'xxx'
    ContextInfo.set_account(account)
    # ---------------------------------------ֻ���ڻ�ز�������---------------------------------------
    ContextInfo.start = '2023-11-15 10:00:00'
    ContextInfo.end = '2024-01-05 14:30:00'
    ContextInfo.capital = 160000
    # ���û���
    ContextInfo.set_slippage(1, 0.01)
    # �趨���Իز������������
    # commissionType:
    # 0������
    # 1��ÿ��
    # ContextInfo.set_commission(commissionType, commissionList)
    # commissionList = [open_tax, close_tax,open_commission, close_commission, close_tdaycommission, min_commission]
    # �趨����ӡ��˰Ϊ 0������ӡ��˰Ϊ 0.0001�����������Ѻ�ƽ�֣�ƽ�������Ѿ�Ϊ������ƽ��������Ϊ0����С������Ϊ5
    commissionList = [0, 0.0001, 0.0003, 0.0003, 0, 5]
    ContextInfo.set_commission(0, commissionList)
    # ---------------------------------------ֻ���ڻ�ز�������---------------------------------------

    redis_client = redis.Redis(host='localhost', port=6379, db=1, password='123456')
    data = redis_client.get('data:2024-01-05����ͨ��')
    # hs300�ɷֹ���sh��sz�г�������ͨ��ֵ����ǰ3ֻ��Ʊ
    stockpool = eval(str(data)[2:-1])
    ContextInfo.set_universe(stockpool)  # �趨��Ʊ��
    ContextInfo.trade_code_list = stockpool
    print(ContextInfo.trade_code_list)
    ContextInfo.set_universe(ContextInfo.trade_code_list)

    ContextInfo.buy = False
    ContextInfo.sell = True


def handlebar(ContextInfo):
    # ���㵱ǰ��ͼ��cci
    # ��ȡ������ͨ�ɱ�
    print('��ȡ������ͨ�ɱ�:' + ContextInfo.get_last_volume('000002.SZ'))
    # ��ȡ��ǰK�߶�Ӧ��ʱ���
    index = ContextInfo.barpos
    print('��ȡ��ǰK�߶�Ӧ��ʱ���' + ContextInfo.get_bar_timetag(index))
    print(get_result_records('buys', index, ContextInfo))
    # ��ȡ��ǰ��ͼƷ�����·ֱʶ�Ӧ��ʱ���ʱ���
    print('��ȡ��ǰ��ͼƷ�����·ֱʶ�Ӧ��ʱ���ʱ���' + ContextInfo.get_tick_timetag())
    realtime = ContextInfo.get_bar_timetag(index)
    print('��ȡָ���ɷݹ�' + ContextInfo.get_sector('000300.SH', realtime))
    # indexcode��string��ָ�����룬��ʽ��,'stockcode.market'����'000300.SH'
    # stockcode��string����Ʊ���룬��ʽ��'stockcode.market'����'600004.SH'
    print('��ȡĳֻ��Ʊ��ĳָ���еľ���Ȩ��' + ContextInfo.get_weight_in_index('000300.SH', '000002.SZ'))
    # print(f'��ǰ�������ǣ�{ContextInfo.period}')
    print('��ȡ�޷�������' + ContextInfo.get_risk_free_rate(index))
    mkdict = ContextInfo.get_market_data(['high', 'low', 'close'], count=int(period) + 1)
    highs = np.array(mkdict['high'])
    lows = np.array(mkdict['low'])
    closes = np.array(mkdict['close'])
    cci_list = talib.CCI(highs, lows, closes, timeperiod=int(period))
    now_cci = cci_list[-1]
    ContextInfo.paint("CCI", now_cci, -1, 0, 'noaxis')
    if len(cci_list) < 2:
        return

    buy_condition = cci_list[-2] < buy_value <= now_cci and ContextInfo.buy
    sell_condition = cci_list[-2] > buy_value >= now_cci and ContextInfo.sell

    if buy_condition:
        ContextInfo.buy = False
        ContextInfo.sell = True
        for stock in ContextInfo.trade_code_list:
            order_lots(stock, 10, ContextInfo, ContextInfo.accID)
    elif sell_condition:
        ContextInfo.buy = True
        ContextInfo.sell = False
        for stock in ContextInfo.trade_code_list:
            order_lots(stock, -10, ContextInfo, ContextInfo.accID)

    df = ContextInfo.get_market_data(['close'], stock_code=ContextInfo.get_universe(), skip_paused=True, period='1d', count='1d', dividend_type='front')
    print(df)
    # print(ContextInfo.barpos)
    # for stock in ContextInfo.trade_code_list:
    #	passorder(23, 1101, ContextInfo.accID, stock, 5, -1, 100, ContextInfo)  # 23�� # 24��
    Result = ContextInfo.get_full_tick(['600000.SH', '000001.SZ'])
    print(Result)
    print(ContextInfo.get_north_finance_change('1d'))
    print('��ȡָ���г�������ʱ��' + get_market_time("SH"))

