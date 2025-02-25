# encoding:gbk
'''
�����������趨�ý��׵Ĺ�Ʊ���ӣ�Ȼ�����ָ����CCIָ�����жϳ���ͳ���
���г���ͳ�������ʱ�����������趨�õĹ�Ʊ����
'''
import pandas as pd
import numpy as np
import talib
import redis

client = redis.Redis(host='localhost', port=6379, db=1, password='123456')
namespace_prefix = 'data:'
print("��������")
# data = get_market_data(['open','close','volume','high','low','amount'],stock_code=['300056.SZ'],start_time='2006-1-1',period='1d',dividend_type='none',count=500)
# print(data)
def init(ContextInfo):
    # ContextInfo.capital = 10000000
    account = 'xxx'
    commissionList = [0, 0.0001, 0.0003, 0.0003, 0, 5]  # ������
    # hs300�ɷֹ���sh��sz�г�������ͨ��ֵ����ǰ3ֻ��Ʊ
    # ContextInfo.trade_code_list = ['601398.SH', '601857.SH', '601288.SH', '000333.SZ', '002415.SZ', '000002.SZ']
    # ContextInfo.set_universe(ContextInfo.trade_code_list)
    ContextInfo.accID = account
    # �趨����ӡ��˰Ϊ 0������ӡ��˰Ϊ 0.0001�����������Ѻ�ƽ�֣�ƽ�������Ѿ�Ϊ������ƽ��������Ϊ 0����С������Ϊ 5
    # ContextInfo.set_commission(0, commissionList)
    # ContextInfo.start = '2023-12-06 10:00:00'
    # ContextInfo.end = '2023-12-08 14:30:00'
    # data = ContextInfo.get_market_data_ex(
    #     fields=['close'],
    #     stock_code=['000001.SZ'],
    #     period='1d',
    #     dividend_type='front')
    # print(data)


def handlebar(ContextInfo):
    print(ContextInfo.capital)
    print(ContextInfo.get_universe())
    print(ContextInfo.period)
    print(ContextInfo.barpos)
    print(ContextInfo.time_tick_size)  # ��ȡ��ǰͼ K ����Ŀ
    print(ContextInfo.is_last_bar())  # �ж��Ƿ�Ϊ���һ�� K ��
    print(ContextInfo.is_new_bar())  # �ж��Ƿ�Ϊ�µ� K ��
    print(ContextInfo.is_suspended_stock('600004.SH'))  # �ж���Ʊ�Ƿ�ͣ��
    # print(is_sector_stock('����300', 'SH', '600000'))  # �ж�������Ʊ�����Ƿ���ָ���İ����
    # print(ContextInfo.do_back_test)  # ��ʾ��ǰ�Ƿ����ز�ģʽ
    # index = ContextInfo.barpos
    # print(get_result_records('buys', index, ContextInfo))  # ��ȡĳ����¼���Ͷ�Ӧ��ĳ��ʱ�̵ļ�¼���
	# # �ۺϽ����µ�
	# passorder(23,1101,"test",'601398.SH',5,-1,100,ContextInfo)








