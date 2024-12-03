import os

import pandas as pd
import tushare as ts


def gp_type_szsh(gp):
    if gp.find('60', 0, 3) == 0:
        gp_type = 'sh'
    elif gp.find('688', 0, 4) == 0:
        gp_type = 'sh'
    elif gp.find('900', 0, 4) == 0:
        gp_type = 'sh'
    elif gp.find('00', 0, 3) == 0:
        gp_type = 'sz'
    elif gp.find('300', 0, 4) == 0:
        gp_type = 'sz'
    elif gp.find('200', 0, 4) == 0:
        gp_type = 'sz'
    return gp_type


if __name__ == '__main__':

    folder_path = './data'
    content_list = os.listdir(folder_path)
    ts.set_token('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')

    for content in content_list:
        content_path = os.path.join(folder_path, content)
        for file in os.listdir(content_path):
            file_path = os.path.join(content_path, file)
            if os.path.isfile(file_path):
                code = f"{file.split('.')[0]}.{gp_type_szsh(file.split('.')[0])}"
                code_realtime = ts.realtime_quote(ts_code=code)
                df = pd.read_csv(file_path)
                print(df.head())
