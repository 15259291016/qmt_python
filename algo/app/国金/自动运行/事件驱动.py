#coding:gbk

class a():pass
A = a()
A.bought_list = []

account = 'xxx'
def init(C):
	#�µ������Ĳ�����Ҫ ContextInfo���� ��init�ж�������ص����� �����õ�init��������� �����ֶ�����
	def callback_func(data):
		#print(data)
		for stock in data:
			current_price = data[stock]['close']
			pre_price = data[stock]['preClose']
			ratio = current_price / pre_price - 1
			print(stock, C.get_stock_name(stock), '��ǰ�Ƿ�', ratio)
			#if ratio > 0 and stock not in A.bought_list:
			if stock not in A.bought_list:
				msg = f"��ǰ�Ƿ� {ratio} ����0 ����100��"
				print(msg)
				#�µ�����passorder ��ȫ�������ע��״̬ ��Ҫʵ�ʲ����µ�����ʱ�ٷſ�
				#passorder(23, 1101, account, stock, 5, -1, 100, '�����µ�ʾ��', 2, msg, C)
				A.bought_list.append(stock)
	stock_list = ['600000.SH', '000001.SZ']
	for stock in stock_list:
		C.subscribe_quote(stock, period = '1d', callback = callback_func)

