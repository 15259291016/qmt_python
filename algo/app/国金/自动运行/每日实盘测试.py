# encoding:gbk
'''
�����������趨�ý��׵Ĺ�Ʊ���ӣ�Ȼ�����ָ����CCIָ�����жϳ���ͳ���
���г���ͳ�������ʱ�����������趨�õĹ�Ʊ����
'''
import pandas as pd
import numpy as np
import talib
import socket
import sys
import threading
import queue
import time
import requests
import json
import psycopg2

print(sys.version)
print('������λ�ã�' + sys.executable)


def receive_data(sock, message_queue):
    while True:
        data = sock.recv(1024)
        if not data:
            break
        print(data.decode('gbk'))
        message_queue.put(data)


def send_data(sock, message):
    sock.sendall(message.encode('utf-8'))


server_host = '127.0.0.1'
server_port = 8083
# ����socket����
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
message_queue = queue.Queue()
a = 0

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="wcsql",
    user="postgres",
    password="123456"
)


def init(ContextInfo):
    # ContextInfo.run_time("myHandlebar","5nSecond","2024-01-10 13:20:00")
    print("��ǰ������:" + ContextInfo.period)
    # �����˺�
    ContextInfo.set_account('xxx')
    print(ContextInfo.set_universe(['603444.SH']))
    # print('algorithms is running!')
    json_data = json.dumps(dir(ContextInfo))
    # r = requests.post('http://127.0.0.1:8000/init',json=json_data)
    # print(r)
    # ���ӵ�������
    # client_socket.connect((server_host, server_port))
    # �����������ݵ��߳�
    # receive_thread = threading.Thread(target=receive_data, args=(client_socket,message_queue))
    # receive_thread.setDaemon(True)
    # receive_thread.start()
    ContextInfo.set_universe(['603444.SH'])
    print(dir(ContextInfo))
    print('init success!')


def handlebar(ContextInfo):
    global a
    # ��ȡ����������
    # print( ContextInfo.get_longhubang(['600336.SH'],'20231201','20140110'))
    # recv_data = message_queue.get()
    if not ContextInfo.is_last_bar():
        return
    # send_data(client_socket,'buy')
    # print(ContextInfo.get_bar_timetag(ContextInfo.barpos))
    # ��ȡ���·ֱ�����,ʵʱ����
    Result = ContextInfo.get_full_tick(['603444.SH'])

    df = pd.DataFrame(Result)
    print()
    df2 = df.T
    df2.to_csv('603444SHTest.csv', mode='a')
    df.to_csv('603444SH.csv', mode='a')
    print('д��ɹ�!')
    # uni = ContextInfo.get_universe()
    # for u in uni:
    #	passorder(23, 1101, 'xxx', u, 5, -1, 100, ContextInfo)  # 23�� # 24��
    # �����α�
    # cursor = conn.cursor()

    timetag = Result['603444.SH']['timetag']
    lastPrice = Result['603444.SH']['lastPrice']
    open = Result['603444.SH']['open']
    high = Result['603444.SH']['high']
    low = Result['603444.SH']['low']
    amount = Result['603444.SH']['amount']
    volume = Result['603444.SH']['volume']
    askPrice = Result['603444.SH']['askPrice']
    bidPrice = Result['603444.SH']['bidPrice']
    askVol = Result['603444.SH']['askVol']
    print(f'ʱ��֡:{timetag}--����:{volume}--askPrice:{askPrice}--bidPrice:{bidPrice}--askVol:{askVol}')
    print(f'��:{open}----������:{volume - a}---*--*---֡�ȣ�{(volume - a) * 100 * askPrice[0]:.2f}-----{(1 - (bidPrice[0] / open)) * 100:.3f}%--ǰ:{bidPrice[0]}')
    # ִ�� SQL ��ѯ
    # cursor.execute(f"INSERT INTO data_info (id,code,name,date,volume,lastprice,high,low,amount,askprice,bidprice,askvol) VALUES ('{timetag}', '603444.SH','������','{timetag}','{volume}','{lastPrice}','{high}','{low}','{amount}','{askPrice[0]}','{bidPrice[0]}','{askVol[0]}')")

    # ��ȡ��ѯ���
    # result = cursor.fetchall()

    # ��ӡ��ѯ���
    # for row in result:
    #	print(row)

    # �ر��α�����ݿ�����
    # cursor.close()
    # hand = volume
    #
    # hisdict = ContextInfo.get_history_data(3, '1d', 'close')
    # for k, v in hisdict.items():
    #	if len(v) > 1:
    #		# �����Ƿ�
    #		print(k, ':', v[1] - v[0])
    #		pass
    # ��ȡ�������ݳֹ���ϸ
    # ContextInfo.get_hkt_details('600336.SH')
    # ��ȡ�������ݳֹ�ͳ��
    # ContextInfo.get_hkt_statistics('600336.SH')
    # ��ȡ��Լ��ϸ��Ϣ
    # print( ContextInfo.get_instrumentdetail('600336.SH'))
    # ��ȡ��������
    # Result=ContextInfo.get_market_data_ex(
    # ['open', 'high', 'low', 'close'], ['000300.SH'], period='1d'
    # , start_time='', end_time='', count=-1
    # , dividend_type='follow', fill_data=True
    # , subscribe = True)
    # print(Result)
    index = ContextInfo.barpos


# �޷�������
# print( ContextInfo.get_risk_free_rate(index))
# ȡ���̳ɽ���
# print( ContextInfo.get_svol('600336.SH'))
# ��ȡ�ܹɱ�
# print( ContextInfo.get_total_share('600336.SH'))
# ��ȡ����������
# print( ContextInfo.get_turnover_rate(['600336.SH'],'20240101','20240110'))
# ĳֻ��Ʊ��ĳָ���еľ���Ȩ��
# print( ContextInfo.get_weight_in_index('000300.SH', '000002.SZ'))
# obj_list = get_trade_detail_data(ContextInfo.accid,'stock','position')
# for obj in obj_list:
#	print(obj.m_strInstrumentID)
#	print(dir(obj))
# acc_info = get_trade_detail_data(ContextInfo.accid,'stock','account')
# print(acc_info)
# orderid = 297
# print(orderid)
# obj = get_value_by_deal_id(orderid,ContextInfo.accid,'stock','deal')
# print(obj.m_strInstrumentID)
# ��ȡ�������� get_factor_value()
# print(get_factor_value('zzz', '600000.SH', 0, ContextInfo))
# ��ȡ���õ��������ݵ���ֵ������Ʒ�������� get_factor_rank()
# print(get_factor_rank('zzz', '600000.SH', 0, ContextInfo))
# realtimetag = ContextInfo.get_bar_timetag(ContextInfo.barpos)
# value = ContextInfo.get_close_price('','',realtimetag)
# ContextInfo.paint('close',value,-1,0,'white', 'noaxis')
# ContextInfo.draw_text(1,10,'��������������')
# ��ͼ������ʾ����
# close = ContextInfo.get_market_data(['close'])
# ContextInfo.draw_number(1>0, close,close,1)

# �ʽ��˺�״̬�仯����
def account_callback(ContextInfo, accountInfo):
    pass


# �˺�ί��״̬�仯����
def order_callback(ContextInfo, orderInfo):
    print('orderInfo')
    print(orderInfo)


# �˺ųɽ�״̬�仯����
def deal_callback(ContextInfo, dealInfo):
    print('��������')
    print(dealInfo)


# �˺��쳣�µ�����
def position_callback(ContextInfo, orderArgs):
    print('orderArgs')


def myHandlebar(ContextInfo):
    print('hello world')

