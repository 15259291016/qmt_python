#coding:gbk

# �����
import pandas as pd
import numpy as np
import datetime

"""
ʾ��˵����˫����ʵ�̲��ԣ�ͨ���������˫���ߣ��ڽ��ʱ���룬����ʱ������
"""

class a():
	pass
A = a() #�����յ����ʵ�� ��������ί��״̬
account = "xxx"

def init(C):
	A.stock= C.stockcode + '.' + C.market #Ʒ��Ϊģ�ͽ��׽���ѡ��Ʒ��
	A.acct= account #�˺�Ϊģ�ͽ��׽���ѡ���˺�
	A.acct_type= accountType #�˺�����Ϊģ�ͽ��׽���ѡ���˺�
	A.amount = 10000 #���������� ���������źź�����ָ�����
	A.line1=17   #��������
	A.line2=27   #��������
	A.waiting_list = [] #δ�鵽ί���б� ����δ�鵽ί�������ͣ�������� ��ֹ����
	A.buy_code = 23 if A.acct_type == 'STOCK' else 33 #�������� ���ֹ�Ʊ �� �����˺�
	A.sell_code = 24 if A.acct_type == 'STOCK' else 34
	print(f'˫����ʵ��ʾ��{A.stock} {A.acct} {A.acct_type} ����������{A.amount}')

def handlebar(C):
	#������ʷk��
	if not C.is_last_bar():
		return
	now = datetime.datetime.now()
	now_time = now.strftime('%H%M%S')
	# �����ǽ���ʱ��
	if now_time < '093000' or now_time > "150000":
		return
	account = get_trade_detail_data(A.acct, A.acct_type, 'account')
	if len(account)==0:
		print(f'�˺�{A.acct} δ��¼ ����')
		return
	account = account[0]
	available_cash = int(account.m_dAvailable)
	#�����δ�鵽ί�� ��ѯί��
	if A.waiting_list:
		found_list = []
		orders = get_trade_detail_data(A.acct, A.acct_type, 'order')
		for order in orders:
			if order.m_strRemark in A.waiting_list:
				found_list.append(order.m_strRemark)
		A.waiting_list = [i for i in A.waiting_list if i not in found_list]
	if A.waiting_list:
		print(f"��ǰ��δ�鵽ί�� {A.waiting_list} ��ͣ��������")
		return
	holdings = get_trade_detail_data(A.acct, A.acct_type, 'position')
	holdings = {i.m_strInstrumentID + '.' + i.m_strExchangeID : i.m_nCanUseVolume for i in holdings}
	#��ȡ��������
	data = C.get_market_data_ex(["close"],[A.stock],period = '1d',count = max(A.line1, A.line2)+1)
	close_list = data[A.stock].values
	if len(close_list) < max(A.line1, A.line2)+1:
		print('���鳤�Ȳ���(�����л������ͣ��) ��������')
		return
	pre_line1 = np.mean(close_list[-A.line1-1: -1])
	pre_line2 = np.mean(close_list[-A.line2-1: -1])
	current_line1 = np.mean(close_list[-A.line1:])
	current_line2 = np.mean(close_list[-A.line2:])
	#������ߴ������ߣ�������ί�� ��ǰ�޳ֲ� ����
	vol = int(A.amount / close_list[-1] / 100) * 100 #�������� ����ȡ����100��������
	if A.amount < available_cash and vol >= 100 and A.stock not in holdings and pre_line1 < pre_line2 and current_line1 > current_line2:
		#�µ����� ������˵��������PY���׺��� passorder
		msg = f"˫����ʵ�� {A.stock} �ϴ����� ���� {vol}��"
		passorder(A.buy_code, 1101, A.acct, A.stock, 14, -1, vol, '˫����ʵ��', 2 , msg, C)
		print(msg)
		A.waiting_list.append(msg)
	#��������´����ߣ�������ί��
	if A.stock in holdings and holdings[A.stock] > 0 and pre_line1 > pre_line2 and current_line1 < current_line2:
		msg = f"˫����ʵ�� {A.stock} �´����� ���� {holdings[A.stock]}��"
		passorder(A.sell_code, 1101, A.acct, A.stock, 14, -1, holdings[A.stock], '˫����ʵ��', 2 , msg, C)
		print(msg)
		A.waiting_list.append(msg)

