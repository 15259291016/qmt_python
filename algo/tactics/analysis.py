
import time
import pandas as pd
import easyquotation
import pywencai as pywc
import threading

csv_file_path = './data/股票列表.csv'    # 替换为您的CSV文件路径
df = pd.read_csv(csv_file_path)
quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']

def stock_names_to_list(stock_names:list[str]):
    result = []
    for name in stock_names:
        result.append(df['ts_code'][df['name'] == name].tolist()[0].split(".")[0])
    return result
def is_trade_time():
    now = time.localtime()
    # return True
    if (now.tm_hour == 9 and now.tm_min >= 24) or (now.tm_hour == 10) or (now.tm_hour == 11 and now.tm_min <= 30) or (now.tm_hour == 13) or (now.tm_hour == 14) or (now.tm_hour == 15 and now.tm_min == 0):
        return True
    return False


def watch_stock_tick(stock_name: list[str], interval):
    """
    获取并保存指定股票名称列表的股票信息，并按指定间隔时间更新。

    参数:
        stock_name (list[str]): 要获取信息的股票名称列表。
        interval (int): 每次获取操作之间的时间间隔（以秒为单位）。

    返回:
        None

    该函数执行以下步骤:
    1. 将股票名称列表转换为股票代码列表。
    2. 为每个股票代码初始化一个空的 DataFrame。
    3. 按指定间隔时间连续获取实时股票数据。
    4. 重命名获取数据中的某些列以保持一致性。
    5. 计算 '涨跌'（价格变化）列的滚动最大值和最小值。
    6. 根据滚动值生成买入和卖出信号。
    7. 将新数据连接到每个股票代码的现有 DataFrame。
    8. 打印最新的股票信息和买入/卖出信号。
    9. 在再次获取数据之前按指定间隔时间休眠。
    """ 
    df_dict = {
        'tick':{},
        "sh":{},
    }
    cjbs = 0
    sh_thread = None
    def watch_sh_by_stocks_names(stock_names: list[str], interval, df_dict):
        stock_code_list = stock_names_to_list(stock_names)
        stock_e_c_name_dict = {stock_names[i]:stock_code_list[i] for i in range(len(stock_code_list))}
        while True:
            if is_trade_time() is False:
                time.sleep(60)
                continue
            
            stock_dde_info = pywc.get(query=f"{stock_names} 散户指标")
            info_dict = [stock_dde_info[key] for key in stock_dde_info.keys()][0].T.to_dict()
            for key in info_dict:
                try:
                    df_dict["sh"][stock_e_c_name_dict[info_dict[key]['名称']]] = info_dict[key]['dde散户数量']
                except Exception as e:
                    print(e)
                    continue
            # [info_dict[key] for key in info_dict]
            # sh_num = float(stock_dde_info["barline3"]["dde散户数量"].iloc[-1])
            # print(info_dict)
            # print(df_dict["sh"])
            print("updated")
            time.sleep(interval)
            
    if sh_thread is None:
        sh_thread = threading.Thread(target=watch_sh_by_stocks_names, args=(stock_name, interval*10, df_dict))
        sh_thread.start()  
        
    stock_code_list = stock_names_to_list(stock_name)
    for stock_code in stock_code_list:
        df_dict['tick'][stock_code] = pd.DataFrame()
    while True:
        if is_trade_time() is False:
            time.sleep(60)
            continue
        stock_data = quotation.real(stock_code_list)
        rename_mapping = {
            'PE': 'pe',
            'PB': 'pb',
            '涨跌(%)': '涨跌百分比',
            '价格/成交量(手)/成交额': '价格成交量成交额',
            '成交量(手)': '成交量手',
            '成交额(万)': '成交额万',
            '市盈(动)': '市盈动',
            '市盈(静)': '市盈静'
        }
        for stock_code in stock_code_list:
            renamed_data = {rename_mapping.get(k, k): v for k, v in stock_data[stock_code].items()}
            for i in renamed_data.keys():
                renamed_data[i] = [renamed_data[i]]
            renamed_data["unknown"] = [1]
            ef = pd.DataFrame(renamed_data)
            ef['rolling_max'] = ef['涨跌百分比']
            ef['rolling_min'] = ef['涨跌百分比'].rolling(window=100, min_periods=1).min()
            if len(df_dict['tick'][stock_code])<=10:
                ef['signal_sell'] = "00"
                ef['signal_buy'] = "00"
                df_dict['tick'][stock_code] = pd.concat([df_dict['tick'][stock_code], ef], ignore_index=True)
            else:
                ef['signal_sell'] = 'sell' if df_dict['tick'][stock_code]['rolling_max'].rolling(window=100, min_periods=1).max().max() - ef['涨跌百分比'].iloc[-1] >= 1.5 else "00"
                ef['signal_buy'] = 'buy' if ef['涨跌百分比'].iloc[-1] - df_dict['tick'][stock_code]['rolling_min'].rolling(window=100, min_periods=1).min().min() >= 1.5 else "00"
                df_dict['tick'][stock_code] = pd.concat([df_dict['tick'][stock_code], ef], ignore_index=True)
            jgcjl = renamed_data["价格成交量成交额"][0].split("/")
            if cjbs != int(jgcjl[1]):
                cjbs = int(jgcjl[1])
            print(f'{ef["name"].iloc[-1]}:{ef["now"].iloc[-1]}\t||{ef["涨跌百分比"].iloc[-1]}-{ef["量比"].iloc[-1]}-{ef["均价"].iloc[-1]}' +
                  f'-{df_dict["tick"][stock_code]["rolling_max"].rolling(window=100, min_periods=1).max().max()},' +
                  f'{df_dict["tick"][stock_code]["rolling_min"].rolling(window=100, min_periods=1).min().min()}\t{ef["signal_sell"].iloc[-1]}-{ef["signal_buy"].iloc[-1]}, {int(jgcjl[1]) - cjbs}' +
                  f'\t{df_dict["sh"][stock_code] if stock_code in df_dict["sh"] else 0}' +
                  f'\t\t{"高" if ef["now"].iloc[-1] > ef["均价"].iloc[-1] else "低"}:' +
                  f'{(ef["now"].iloc[-1] - ef["均价"].iloc[-1]):.2f}:' + 
                  f'{(float((ef["now"].iloc[-1] - ef["均价"].iloc[-1])) / ef["now"].iloc[-1])*100:.2f}%')
        print('-'*100)
        time.sleep(interval)
# 中国核电、国机精工、电光科技、小方制药、中际旭创
watch_stock_tick(['嵘泰股份', '远程股份', '吉比特','春风动力', '可孚医疗','华北制药', '比亚迪', '巨轮智能'], 3)