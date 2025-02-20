import logging

from app.db import pgsql
from app.db.pgsql import WatchCode
from datetime import datetime, timedelta, time
import os
import sys

from starlette.middleware.cors import CORSMiddleware

# 获取当前文件的目录路径并添加到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)
import queue
import socket
import threading
import time as t
import webbrowser
import pywencai as wc
import pandas as pd
import redis
import qstock as qs
# https://zhuanlan.zhihu.com/p/659430613
import efinance as ef
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
import traceback
import easyquotation

from app.db import pgsql
from app.db.pgsql import WatchCode, WaitBuyList

def print_(str_obj, directory="files/"):
    print(str_obj)
    logging.log(logging.INFO, str_obj)
    # 确保提供的目录存在
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        # 获取当前时间
    current_time = t.localtime()

    # 将分钟数转换为离最近的10分钟整数倍的时间（向下取整）
    minute = current_time.tm_min - (current_time.tm_min % 10)
    file_name = t.strftime(f"data_log_%Y-%m-%d-%H-{minute:02d}.txt", current_time)

    if directory:
        file_path = os.path.join(directory, file_name)
    else:
        file_path = file_name

    # 写入数据到文件
    with open(file_path, 'a') as file:
        file.write(str(str_obj) + "\n")

    # 上面的代码会在example.txt文件末尾追加内容 "Goodbye, World!"


def brain_init():
    character = "radicalise"  # 激进性格


def brain_bidding():
    """
    竞价:分析竞价
    """
    pass


def get_trade_date(day: int = 0):
    """
    获取交易日
    """
    days_to_subtract = 5
    skipped_days = 0

    while skipped_days < days_to_subtract:
        current_date = datetime.now()
        current_date = current_date - timedelta(days=day)
        if current_date.weekday() < 5:  # 周一到周五为0-4
            skipped_days += 1
        else:
            day += 1
    return current_date.strftime('%Y%m%d')


def download_png_csv():
    """
    诸葛亮、荀彧:分析市场
    找出市场上活跃的板块,主要收集数据
    """
    current_time = datetime.now().time()
    time1 = time(9, 15)
    time2 = time(11, 30)
    time3 = time(13, 0)
    time4 = time(15, 10)
    while True:
        # if time1 <= current_time <= time2 or time3 <= current_time <= time4:
        if True:
            for root, dirs, files in os.walk('./data/png'):
                # 打印当前目录路径
                # print(f'当前目录：{root}')

                # 打印所有子目录
                # print('子目录：')
                for dir in dirs:
                    if not os.path.exists(os.path.join(root.replace('png', 'csv'), dir)):
                        os.makedirs(os.path.join(root.replace('png', 'csv'), dir))
                    # print(os.path.join(root, dir))
                code_list = []
                # 打印所有文件
                # print('文件：')
                for file in files:
                    # print(os.path.join(root, file))
                    code_list.append(file.split(".")[0][-2:].lower() + file.split(".")[0][:-2])
                if code_list:
                    # print(quotation.stocks(code_list, prefix=True))
                    res = quotation.stocks(code_list, prefix=True)
                    for code in res.keys():
                        pd.DataFrame(res[code], index=[0]).to_csv(f'{os.path.join(root.replace("png", "csv"), code)}.csv', mode='a', header=True, index=False)
        t.sleep(60)


def code_list_to_csv(code_list: list):
    """
    将股票代码列表转换为csv文件
    """
    now = datetime.now()
    day = now.strftime("%Y-%m-%d")
    if not os.path.exists(f'./data/{day}'):
        os.makedirs(f'./data/{day}')
    if code_list:
        freq = 1
        for i in code_list:
            df = ef.stock.get_quote_history(i, klt=freq)
            df.to_csv(f'./data/{day}/{i}.csv', encoding='utf-8-sig', index=None)


def question_wc(question):
    wc_cookie = 'other_uid=Ths_iwencai_Xuangu_vt1m3hjjud764awfezv3ezly4t2f9xco; ta_random_userid=38r3s4iaao; PHPSESSID=670fb84a8754b3555e226c6b40c1d831; cid=670fb84a8754b3555e226c6b40c1d8311712721082; ComputerID=670fb84a8754b3555e226c6b40c1d8311712721082; WafStatus=0; u_ukey=A10702B8689642C6BE607730E11E6E4A; u_uver=1.0.0; u_dpass=HDZXnLqPSJ%2FMpvbRfnHhizBr0Y9TGLpA9wXLLjwsvQ09AWJ2DoZsyKUcGwEmAARD%2FsBAGfA5tlbuzYBqqcUNFA%3D%3D; u_did=ED35F01A88274FB59C3D3D607D30FEF0; u_ttype=WEB; ttype=WEB; user=MDptb181NjI3MjgwNzU6Ok5vbmU6NTAwOjU3MjcyODA3NTo3LDExMTExMTExMTExLDQwOzQ0LDExLDQwOzYsMSw0MDs1LDEsNDA7MSwxMDEsNDA7MiwxLDQwOzMsMSw0MDs1LDEsNDA7OCwwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMSw0MDsxMDIsMSw0MDoyNDo6OjU2MjcyODA3NToxNzEyNzIxMTIyOjo6MTYxMDkyNDk0MDo0MDAwNzg6MDoxNTljOTE4ODcwNDMzZjVlZDBhYTA5YWUzZWZiMDZhN2M6ZGVmYXVsdF80OjE%3D; userid=562728075; u_name=mo_562728075; escapename=mo_562728075; ticket=c35f5ff9817c2eee41b92f1a856ae0aa; user_status=0; utk=4261b365b2919c25775389e81aabe8e0; v=Az9jBtnQZWCRhWF8zdmzVs3XzhjMJJPPrXiXutEM2-414FHG2fQjFr1IJwbi'
    res = None
    try:
        res = wc.get(query=question, cookie=wc_cookie)
        # res = None
    except Exception as e:
        webbrowser.open('https://www.iwencai.com/unifiedwap/reptile.html?returnUrl=https%3A%2F%2Fwww.iwencai.com%2Funifiedwap%2Fhome%2Findex%3Fsign%3D1709793871013&sessionId=117.30.119.18&antType=unifiedwap')
        print_(e)
        t.sleep(20)
    # if res is not None:
    # res_list = print_data(res)
    # code_list_to_csv(res_list)
    # return res_list
    return res


def wencai_():
    public_obj = {'code_list': [],
                  }
    def brain_think(res, ideal):
        """
        分析数据
        """
        print_(ideal)

        # 回忆：都数据库中取出数据,然后分析
        # 读redis或者es然后分析
        code_list = []

        def get_code_info(stock_info):
            if '股票代码' in stock_info.keys(): stock_info['股票代码']  # 001282.SZ
            if '股票简称' in stock_info.keys(): stock_info['股票简称']  # 三联锻造
            if '最新价' in stock_info.keys(): stock_info['最新价']  # 32.20
            if '最新涨跌幅' in stock_info.keys(): stock_info['最新涨跌幅']  # 0.846
            master_money_str = '主力资金流向'  #
            current_date = get_trade_date(0)  #
            # 市值
            # 资金买卖
            # 资金净流入
            if f'资金流入inner[{current_date}]' in stock_info.keys() and f'主力买入金额[{current_date}]' in stock_info.keys() and f'a股市值(不含限售股)[{current_date}]' in stock_info.keys():
                market_value = int(float(stock_info[f'a股市值(不含限售股)[{get_trade_date(0)}]'])) / 10000  # 9.144036
                net_capital_inflow = (float(stock_info[f'资金流入inner[{current_date}]']) - float(stock_info[f'资金流出inner[{current_date}]'])) / 10000
                main_net_buying = (float(stock_info[f'主力买入金额[{current_date}]']) - float(stock_info[f'主力卖出金额[{current_date}]'])) / 10000
                net_capital_inflow / market_value
                main_net_buying / market_value
            if f'dde散户数量[{current_date}]' in stock_info.keys():
                stock_info[f'dde散户数量[{current_date}]']
            res = question_wc(f'{stock_info["股票简称"]}散户情况')
            # res = wc.get(query=f'{stock_info["股票简称"]}散户情况')
            try:
                if res is not None:
                    if 'barline3' in res.keys():
                        print_(res['barline3'])
                        if 'dde散户数量' in res['barline3'].keys(): print_(res['barline3']['dde散户数量'].astype(float).sum())
                    if '多日累计dde散户数量' in res.keys(): print_(res['多日累计dde散户数量'])
                    if '文本标题h1' in res.keys(): print_(res['文本标题h1'])
                    # if 'txt1' in res.keys():
                    # print_(res['txt1'])

                    # print_(pd.merge(res['barline3'], res['历史主力资金流向']['barline3']))
                    code_list.append(stock_info['code'])

                    i = stock_info['股票代码']
                    current_time = t.localtime()

                    # 将分钟数转换为离最近的10分钟整数倍的时间（向下取整）
                    minute = current_time.tm_min - (current_time.tm_min % 10)
                    path_ = t.strftime(f"%H-{minute:02d}", current_time)
                    file_name = f'./data/png/其他/{get_trade_date(0)}/{path_}'
                    if os.path.isfile(f'{file_name}/{i.replace(".", "")}.png'):
                        return
                    # browser = webdriver.Chrome()
                    # sz002933
                    # browser.get(f'https://finance.sina.com.cn/realstock/company/{i.split(".")[1].lower()}{i.split(".")[0]}/nc.shtml')

                    # 现在页面上的JavaScript已执行，包括绘制到<canvas>的内容
                    # 你可以使用Selenium的API来与页面交互或提取信息
                    # 例如，获取<canvas>元素的截图
                    # browser.find_element(By.CLASS_NAME, 'snp-btn-close-new').click()
                    # t.sleep(1)
                    # [element for element in browser.find_elements(By.CLASS_NAME, 'kke_menus_tab_normal') if element.text == 'B/S点'][0].click()  # B/S点 click
                    # t.sleep(0.5)
                    # [element for element in browser.find_elements(By.TAG_NAME, 'li') if element.text == 'RSI'][0].click()  # RSI li click
                    # canvas = browser.find_elements(By.CLASS_NAME, 'wrapflash')

                    if not os.path.exists(file_name):
                        if not os.path.exists(f'data/png/其他/{get_trade_date(0)}'):
                            os.mkdir(f'data/png/其他/{get_trade_date(0)}')
                        os.mkdir(f'data/png/其他/{get_trade_date(0)}/{path_}')
                    with open(f'{file_name}/{i.replace(".", "")}.png', 'wb') as file:
                        # file.write(canvas[0].screenshot_as_png)
                        file.write("...".encode())
            except Exception as e:
                print(traceback.print_exc())

            if 'apply' in dir(res): res.apply(get_code_info, axis=1)
            print_(code_list)

        res.apply(get_code_info, axis=1)
        # res_list = res.to_dict(orient='records')
        # res_code_list = [i['股票代码'] for i in res_list]
        # for i in res_code_list:
        #     code_info = wc.get(query=i)
        # public_obj['code_list'] = res.to_dict(orient='records')

    def brain_think_ascending_channel(res, ideal):
        """
        上升通道
        散户会有很多散户持有一个股票,出现一个股票多个散户持有是正常的情况
        """
        print_('上升通道')
        print_(ideal)

        def get_code_info(stock_info):
            current_time = t.localtime()

            # 将分钟数转换为离最近的10分钟整数倍的时间（向下取整）
            minute = current_time.tm_min - (current_time.tm_min % 10)
            path_ = t.strftime(f"%H-{minute:02d}", current_time)
            file_name = f'./data/png/拉升通道/{get_trade_date(0)}/{path_}'
            if os.path.isfile(f'{file_name}/{stock_info["股票代码"].replace(".", "")}.png'):
                return
            # browser = webdriver.Chrome()
            # browser.get(f'https://finance.sina.com.cn/realstock/company/{stock_info["股票代码"].split(".")[1].lower()}{stock_info["股票代码"].split(".")[0]}/nc.shtml')
            # browser.find_element(By.CLASS_NAME, 'snp-btn-close-new').click()
            # [element for element in browser.find_elements(By.CLASS_NAME, 'kke_menus_tab_normal') if element.text == 'B/S点'][0].click()  # B/S点 click
            # t.sleep(0.5)
            # [element for element in browser.find_elements(By.TAG_NAME, 'li') if element.text == 'RSI'][0].click()  # RSI li click
            # canvas = browser.find_elements(By.CLASS_NAME, 'wrapflash')
            try:
                pgsql.create(WatchCode(code=stock_info["股票代码"], market=stock_info["股票代码"].split(".")[-1]))
            except Exception as e:
                print(traceback.print_exc())
            if not os.path.exists(file_name):
                if not os.path.exists(f'data/png/拉升通道'):
                    os.mkdir(f'data/png/拉升通道')
                if not os.path.exists(f'data/png/拉升通道/{get_trade_date(0)}'):
                    os.mkdir(f'data/png/拉升通道/{get_trade_date(0)}')
                os.mkdir(f'data/png/拉升通道/{get_trade_date(0)}/{path_}')
                return {"data": "添加成功", "code": 200}

            with open(f'{file_name}/{stock_info["股票代码"].replace(".", "")}.png', 'wb') as file:
                # file.write(canvas[0].screenshot_as_png)
                file.write("...".encode())

        if 'apply' in dir(res): res.apply(get_code_info, axis=1)
        # res_list = res.to_dict(orient='records')
        # res_code_list = [i['股票代码'] for i in res_list]
        # for i in res_code_list:
        #     code_info = wc.get(query=i)
        # public_obj['code_list'] = res.to_dict(orient='records')
        # print_(res)

    def brain_think_private_investor(res, ideal):
        """
        分析散户
        散户会有很多散户持有一个股票,出现一个股票多个散户持有是正常的情况
        """
        print_('分析散户')
        print_(ideal)
        res_list = res.to_dict(orient='records')
        res_code_list = [i['股票代码'] for i in res_list]
        for i in res_code_list:
            try:
                code_info = wc.get(query=i)
                print(code_info)
                if '历史主力资金流向' in code_info.keys():
                    flag_list = []
                    data = pd.merge(code_info['barline3'], code_info['历史主力资金流向']['barline3'])
                    shsl_info = wc.get(query=f'{i}散户数量')
                    cmqj_info = wc.get(query=f'{i}筹码区间')
                    zlzj_info = wc.get(query=f'{i}主力资金')
                    # flag_list.append(data.loc[:, '成交额'].astype(float).head().sum() / 100000000 < data.loc[:, '成交额'].astype(float).tail().sum() / 100000000)
                    flag_list.append(data.loc[:, '主力资金'].sum() / 10000000 > 1)
                    flag_list.append(shsl_info['多日累计dde散户数量'].loc[:, "区间dde散户数量"].head().sum() < 0)
                    flag_list.append(cmqj_info['barline3'].loc[:, "收盘获利"].tail(1).to_list()[0] > 30)
                    flag_list.append(zlzj_info['每日主力资金流向']['bar3'].loc[:, "主力资金"].sum() / 1000000 > 4)  # 主力资金 日进入大于4百万
                    try:
                        flag_list.append(zlzj_info['每15分钟实时资金流向']['line3'].loc[:, "分时资金流向"].astype(float).sum() > 0)
                        flag_list.append(int(code_info['历史主力资金流向']['txt1'].split("两市排名")[1].split("。")[0].split("/")[0]) < 1000)
                    except Exception as e:
                        print(traceback.print_exc())
                    if flag_list.count(True) + 1 >= len(flag_list):
                        print("-".join(code_info['所属概念列表'].loc[:, "诊股概念分类名称"].tolist()))

                        current_time = t.localtime()

                        # 将分钟数转换为离最近的10分钟整数倍的时间（向下取整）
                        minute = current_time.tm_min - (current_time.tm_min % 10)
                        path_ = t.strftime(f"%H-{minute:02d}", current_time)
                        file_name = f'./data/png/散户分析/{get_trade_date(0)}/{path_}'
                        if os.path.isfile(f'{file_name}/{i.replace(".", "")}.png'):
                            return
                        # browser = webdriver.Chrome()
                        # sz002933
                        # browser.get(f'https://finance.sina.com.cn/realstock/company/{i.split(".")[1].lower()}{i.split(".")[0]}/nc.shtml')

                        # 现在页面上的JavaScript已执行，包括绘制到<canvas>的内容
                        # 你可以使用Selenium的API来与页面交互或提取信息
                        # 例如，获取<canvas>元素的截图
                        # browser.find_element(By.CLASS_NAME, 'snp-btn-close-new').click()
                        # [element for element in browser.find_elements(By.CLASS_NAME, 'kke_menus_tab_normal') if element.text == 'B/S点'][0].click()  # B/S点 click
                        # t.sleep(0.5)
                        # [element for element in browser.find_elements(By.TAG_NAME, 'li') if element.text == 'RSI'][0].click()  # RSI li click
                        # canvas = browser.find_elements(By.CLASS_NAME, 'wrapflash')

                        if not os.path.exists(file_name):
                            if not os.path.exists(f'data/png/散户分析/{get_trade_date(0)}'):
                                os.mkdir(f'data/png/散户分析/{get_trade_date(0)}')
                            os.mkdir(f'data/png/散户分析/{get_trade_date(0)}/{path_}')
                        with open(f'{file_name}/{i.replace(".", "")}.png', 'wb') as file:
                            # file.write(canvas[0].screenshot_as_png)
                            file.write("...".encode())
            except Exception as e:
                webbrowser.open('https://www.iwencai.com/unifiedwap/reptile.html?returnUrl=https%3A%2F%2Fwww.iwencai.com%2Funifiedwap%2Fhome%2Findex%3Fsign%3D1712645234441&sessionId=117.30.204.16&antType=unifiedwap')
                print(traceback.print_exc())
                t.sleep(15)
                continue
        public_obj['code_list'] = res.to_dict(orient='records')
        print_(res)

    current_time = datetime.now().time()
    start_time = time(9, 28)
    end_time = time(9, 30)

    while True:
        # if start_time <= current_time <= end_time:
        ideals = ['9:20之前的竞价出现涨跌停价挂单加分,剔除ST',
                    '9:20~9:25期间,撮合价格逐步走高,同时伴随着成交量的放大,且以密集红柱为主。最后两分钟内大资金强吃货,且最终竞价涨幅在3%~7%之间，剔除ST',
                    '9:30前,有巨单挂过涨跌停价,个股形态完好,前几日分时有过异动或者有过涨停,开始股价涨停 ,竞价过程中撮合价格慢慢走低,但成交量有效放大,并且承接很好,主买盘为主', ]
        sleep_time = 1800
        # else:
        #     # 市值小于50亿
        #     ideals = [
        #         # '总市值大于等于20亿小于等于50亿,剔除ST,缩量,最近10个交易日有6个交易日以上主力资金净流入,最近3个交易日涨幅为正,资金净流入的股票,散户卖出,筹码高度集中,MACD大于0,最近3个交易日涨幅为正,rsi金叉，',
        #         '市值大于100亿,放量,剔除ST,剔除次新,剔除北交所,拉升通道,最近20日放量,最近3个交易日涨幅为正,',
        #         # '流通市值大于20亿元,市值小于100亿,散户持续卖出,放量,剔除ST,剔除次新,亿剔除次北交所,最近10个交易日有6个交易日以上主力资金净流入,最近3个交易日涨幅为正,rsi金叉',
        #         '市值大于100亿,放量,不包括次新股,剔除ST,剔除次新,亿剔除次北交所,股票市场不包括北交所,散户卖出,最近3个交易日涨幅为正,',
        #         # '机构净额大于500万,关注度高,近期热门板块,散户卖出,最近3个交易日涨幅为正,,',
        #         '市值大于100亿,亿剔除次新股,拉升通道,股票市场只包括创业板,MACD大于0,资金流入,最近20日放量,最近3个交易日涨幅为正,',
        #         '市值大于100亿,拉升通道,仅创业板,MACD大于0,筹码高度集中,资金流入,',
        #         'rsi金叉，总市值大于100亿，拉升通道,',
        #         'dde大单净额>100万，散户数量减少，量比>0.8，振幅>3%，流通市值大于等于20亿小于等于50亿，boll突破中轨，拉升通道',
        #         '20天内有过涨停，阳包阴，当日振幅前100，放量，上升通道，',
        #         # AI模型精选优质股
        #         # '小盘股(流通市值小于100亿),日线放量上涨,macd提示买入,近期大股东没有减持,',
        #         # '业绩预增大于20%,机构评级看多,近期大股东没有减持,',
        #         # '龙虎榜净买入,昨日放量上涨,短期趋势向上,近期大股东没有减持,',
        #     ]
        #     sleep_time = 6000
        current_time = datetime.now().time()
        time1 = time(9, 15)
        time2 = time(11, 30)
        time3 = time(13, 0)
        time4 = time(15, 10)
        thread_list = []
        if time1 <= current_time <= time2 or time3 <= current_time <= time4:  # 程序9.26分-11.30分,13.00-15.10运行时间
            # if time3 <= current_time <= time4:  # 程序9.28分-11.30分,13.00-15.10运行时间
            # if True:            # 程序9.10分-11.30分,13.00-15.10运行时间
            for ideal in ideals:
                print_(ideal)
                try:
                    res = wc.get(query=ideal)
                    print_(res)
                except Exception as e:
                    webbrowser.open('https://www.iwencai.com/unifiedwap/reptile.html?returnUrl=https%3A%2F%2Fwww.iwencai.com%2Funifiedwap%2Fhome%2Findex%3Fsign%3D1709793871013&sessionId=117.30.119.18&antType=unifiedwap')
                    print_(e)
                    t.sleep(15)
                    continue
                t.sleep(1)
                # if res is not None:
                #     if '散户卖出' in ideal:
                #         thead = threading.Thread(target=brain_think_private_investor, args=(res, ideal))
                #         thread_list.append(thead)
                #         thead.start()
                #         # brain_think_private_investor(res, ideal)
                #     elif '升' in ideal:
                #         thead = threading.Thread(target=brain_think_ascending_channel, args=(res, ideal))
                #         thread_list.append(thead)
                #         thead.start()
                #     else:
                #         brain_think(res, ideal)
        print("break time")
        t.sleep(sleep_time)
        # public_obj['code_list'] = res.rename(columns={'股票代码': 'code', '股票简称': 'name', '最新价': 'price'}).loc[:, ['code', 'name', 'price']].drop_duplicates().to_dict(orient='records')


def brain_buy():
    pass


def brain_sell():
    pass


def brain_analyse_BX():
    """
    分析北向资金
    """
    pass


def brain_analyse_CY():
    """
    分析创业板stock
    """
    pass


def brain_analyse_SH():
    """
    分析上证指数,
    根据历史走势,近期热点板块,列入观察列表
    """
    pass


def brain_analyse_block():
    """
    分析上证指数,
    根据历史走势,近期热点板块,列入观察列表
    """
    pass


def watch_list():
    """
    观察列表,是否观察到了大额度的交易,涨停前的具体表现就是大单子上推
    """
    pass


# 创建一个 Redis 客户端对象
# client = redis.Redis(host='localhost', port=6379, db=1, password='123456')
# namespace_prefix = 'data:'
# 获取一个键值对
# value = client.get(namespace_prefix+'拉升通道')
# print_(value)
# 关闭 Redis 客户端对象
# https://www.iwencai.com/unifiedwap/result?w=%E5%89%94%E9%99%A4%E6%AC%A1%E6%96%B0%E8%82%A1%EF%BC%9B%E5%89%94%E9%99%A4st%E8%82%A1%EF%BC%9B%E6%8B%89%E5%8D%87%E9%80%9A%E9%81%93%EF%BC%8C&querytype=stock
# https://backtest.10jqka.com.cn/
# print_('记住dde散户数量最重要~~~~~')


# ['__class__', '__deepcopy__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'barpos', 'benchmark', 'bsm_iv', 'bsm_price', 'capital', 'context', 'create_sector', 'current_bar', 'data_info_level', 'dividend_type', 'do_back_test', 'draw_icon', 'draw_number', 'draw_text', 'draw_vertline', 'end', 'get_ETF_list', 'get_all_subscription', 'get_back_test_index', 'get_bar_timetag', 'get_bvol', 'get_close_price', 'get_commission', 'get_contract_expire_date', 'get_contract_multiplier', 'get_date_location', 'get_divid_factors', 'get_factor_data', 'get_finance', 'get_financial_data', 'get_float_caps', 'get_full_tick', 'get_function_line', 'get_his_contract_list', 'get_his_index_data', 'get_his_st_data', 'get_history_data', 'get_hkt_details', 'get_hkt_statistics', 'get_holder_num', 'get_industry', 'get_instrumentdetail', 'get_largecap', 'get_last_close', 'get_last_volume', 'get_local_data', 'get_longhubang', 'get_main_contract', 'get_market_data', 'get_market_data_ex', 'get_market_data_ex_ori', 'get_midcap', 'get_net_value', 'get_north_finance_change', 'get_open_date', 'get_option_detail_data', 'get_option_iv', 'get_option_list', 'get_option_undl', 'get_option_undl_data', 'get_product_asset_value', 'get_product_init_share', 'get_product_share', 'get_raw_financial_data', 'get_risk_free_rate', 'get_scale_and_rank', 'get_scale_and_stock', 'get_sector', 'get_slippage', 'get_smallcap', 'get_stock_list_in_sector', 'get_stock_name', 'get_stock_type', 'get_svol', 'get_tick_timetag', 'get_top10_share_holder', 'get_total_share', 'get_tradedatafromerds', 'get_trading_dates', 'get_turn_over_rate', 'get_turnover_rate', 'get_universe', 'get_weight_in_index', 'in_pythonworker', 'is_fund', 'is_future', 'is_last_bar', 'is_new_bar', 'is_stock', 'is_suspended_stock', 'load_stk_list', 'load_stk_vol_list', 'market', 'paint', 'period', 'refresh_rate', 'request_id', 'run_time', 'set_account', 'set_commission', 'set_slippage', 'set_universe', 'start', 'stockcode', 'stockcode_in_rzrk', 'subMap', 'subscribe_quote', 'subscribe_whole_quote', 'time_tick_size', 'unsubscribe_quote', 'z8sglma_last_barpos', 'z8sglma_last_version']
# ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__instance_size__', '__le__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'm_Enable', 'm_dAssetBalance', 'm_dAssureAsset', 'm_dAvailable', 'm_dBalance', 'm_dBuyWaitMoney', 'm_dCashIn', 'm_dCloseProfit', 'm_dCommission', 'm_dCredit', 'm_dCurrMargin', 'm_dDeposit', 'm_dEntrustAsset', 'm_dFetchBalance', 'm_dFrozenCash', 'm_dFrozenCommission', 'm_dFrozenMargin', 'm_dFrozenRoyalty', 'm_dFundValue', 'm_dGoldFrozen', 'm_dGoldValue', 'm_dInitBalance', 'm_dInitCloseMoney', 'm_dInstrumentValue', 'm_dInstrumentValueRMB', 'm_dIntradayBalance', 'm_dIntradayFreedBalance', 'm_dLoanValue', 'm_dLongValue', 'm_dMargin', 'm_dMaxMarginRate', 'm_dMortgage', 'm_dNav', 'm_dNetValue', 'm_dOccupiedBalance', 'm_dPositionProfit', 'm_dPreBalance', 'm_dPreCredit', 'm_dPreMortgage', 'm_dPurchasingPower', 'm_dRawMargin', 'm_dRealRiskDegree', 'm_dRealUsedMargin', 'm_dReceiveInterestTotal', 'm_dRepurchaseValue', 'm_dRisk', 'm_dRoyalty', 'm_dSellWaitMoney', 'm_dShortValue', 'm_dStockValue', 'm_dSubscribeFee', 'm_dTotalDebit', 'm_dWithdraw', 'm_nBrokerType', 'm_nDirection', 'm_strAccountID', 'm_strAccountKey', 'm_strAccountRemark', 'm_strBrokerName', 'm_strMoneyType', 'm_strOpenDate', 'm_strStatus', 'm_strTradingDate']
# def print_data(data):
#     if data is None: return
#     data = data['xuangu_tableV1']
#     data.rename(columns={'股票简称': 'name', '最新价': 'price'}, inplace=True)
#     data.sort_values(by='code', ascending=True, inplace=True, )
#     data = data.loc[:, ['code', 'name', 'price']].drop_duplicates()
#     for row in data.iterrows():
#         try:
#             result_set = wc.get(query=row[1]['name'], )
#             df3 = pd.merge(result_set['barline3'], result_set['历史主力资金流向']['barline3'])
#             result_set['barline3']
#             result_set['所属概念列表']
#             result_set['历史主力资金流向']['barline3']
#             result_set['kline2']
#             result_set['估值指标']['市盈率']['labelLine']
#             result_set['估值指标']['市净率']['labelLine']
#             result_set['估值指标']['市销率']['labelLine']
#             print_(df3)
#         except Exception as e:
#             print_(e)

def print_data(res):
    if res is None: return
    print_(res)
    try:
        res.rename(columns={'股票简称': 'name', '最新价': 'price'}, inplace=True)
        res.sort_values(by='code', ascending=True, inplace=True, )
        res = res.loc[:, ['code', 'name', 'price']].drop_duplicates()
        for row in res.iterrows():
            try:
                result_set = wc.get(query=row[1]['name'], )
                df3 = pd.merge(result_set['barline3'], result_set['历史主力资金流向']['barline3'])

                # print__demo(result_set['近期重要事件'])
                # print_(result_set['所属概念列表']['诊股概念分类名称'].to_list())
                # print_("-" * 100)
                # print_(f"支撑位:{result_set['kline2'].iloc[0:]['止盈止损(支撑位)'][0]} ------压力位:{result_set['kline2'].iloc[0:]['止盈止损(压力位)'][0]}----{result_set['支撑位压力位']}")
                # if '若能站稳，意味着上涨空间打开，可适当关注5日均线，若跌破可考虑止盈' in result_set['支撑位压力位']:
                # print_(result_set['财务数据'])
                # print_(result_set['估值指标']['市净率']['txt1'][40:])
                # print_(result_set['估值指标']['市销率']['txt1'][52:])
                # print_(result_set['十大股东持股比例'].loc[:, ['大股东名称', '大股东持股比例', '大股东公告日期', '股东类型']])
                # result_set['估值指标']['市销率']['labelLine'].tail(30)           # 有参考价值
                # result_set['估值指标']['市净率']['labelLine'].tail(30)           # 有参考价值
                # result_set['估值指标']['市净率']['labelLine'].tail(30)           # 有参考价值
                # result_set['barline3']
                # result_set['所属概念列表']
                # result_set['历史主力资金流向']['barline3']
                # result_set['kline2']
                # result_set['估值指标']['市盈率']['labelLine']
                # result_set['估值指标']['市净率']['labelLine']
                # result_set['估值指标']['市销率']['labelLine']
                # print_(df3)
                # else:
                #     pass
                # print_(df3)
                print_(df3)
            except Exception as e:
                print_(e)
    except Exception as e:
        print_(e)
    if res is not None and 'code' in res.columns:
        return res['code'].to_list()


def analyse():
    # now = datetime.datetime.now()
    # day = now.strftime("%Y-%m-%d")
    # if not os.path.exists(f"{day}"):
    #     os.mkdir(f"{day}")
    # # namespace_prefix = 'data:'
    # # namespace_prefix = namespace_prefix + day
    # res = wc.get(query='市值小于50亿；即将启动拉升；剔除次新股；剔除st股股票市场不包括北交所,剔除创业板股票')
    # print_('------------------------即将启动拉升----------------------------')
    # print_(res['xuangu_tableV1'])
    # if res is not None: client.set(namespace_prefix + '即将启动拉升', json.dumps(list(set([i for i in res['xuangu_tableV1']['股票代码']]))))
    # print_(res['xuangu_tableV1'])
    # print_data(res)
    # res = wc.get(query='市值小于50亿；上升趋势；剔除次新股；剔除st股；股票市场不包括北交所,剔除创业板股票')
    # print_('------------------------市值小于60亿上升趋势----------------------------')
    # if res is not None: client.set(namespace_prefix + '上升趋势', json.dumps(list(set([i for i in res['xuangu_tableV1']['股票代码']]))))
    # print_(res['xuangu_tableV1'])
    # print_data(res)
    # res = wc.get(query='市值小于100亿,亿剔除次新股；剔除st股；拉升通道,股票市场不包括北交所,剔除创业板股票')
    # print_('------------------------市值小于100亿,拉升通道----------------------------')
    # if res is not None: client.set(namespace_prefix + '拉升通道', json.dumps(list(set([i for i in res['xuangu_tableV1']['股票代码']]))))
    # print_(res['xuangu_tableV1'])
    # print_data(res)
    # res = wc.get(query='市值小于100亿,剔除创业板股票,筹码集中度90小于15%,PE小于70,准备拉升')
    # print_('------------------------市值小于100亿,准备拉升----------------------------')
    # if res is not None: client.set(namespace_prefix + '近半年没有拉升过的', json.dumps(list(set([i for i in res['xuangu_tableV1']['股票代码']]))))
    # client.close()
    # print_(res['xuangu_tableV1'])
    # print_data(res)
    pass


# 用于处理队列中的消息的函数
def process_messages(message_queue):
    while True:
        # 从队列中取出消息
        # if not message_queue.empty():
        addr, data = message_queue.get()

        # 处理数据（这里简单地将数据原样发送回客户端）
        response = f"Received from {addr}: {data.decode('utf-8')}"


# 用于处理客户端连接的函数
def handle_client(client_socket, addr, message_queue):
    print_(f"Accepted connection from {addr}")

    while True:
        # 接收客户端数据
        data = client_socket.recv(1024)
        if not data:
            break
        print_(data.decode('gbk'))
        try:
            data = qs.intraday_data(data.decode('gbk')).tail(1).to_string()
        except Exception as e:
            print_(e)
            data = '无'
        print_(f'客户端发来:{data}')
        data_set = message_queue.get()
        print_(f'队列取出:{data_set}')
        print_(data_set)
        if data_set:
            client_socket.sendall(str(data_set).encode('gbk'))
        # 将数据放入队列

    # 关闭与客户端的连接
    client_socket.close()
    print_(f"Connection from {addr} closed")


def myServer(host, port):
    print_('myServer is running')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    # 开始监听连接
    sock.listen()
    # 等待客户端连接
    while True:
        client_socket, client_address = sock.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, message_queue))
        client_handler.start()


def myAnalyse(message_queue):
    print_('myAnalyse is running')
    stock_list = []
    while True:
        try:
            res = wc.get(query='市值小于50亿,即将启动拉升,剔除次新股,剔除st股,剔除创业板股票')
            if not res['xuangu_tableV1'].empty:
                print_(res)
            result_set = res['xuangu_tableV1'].loc[:, ['股票简称', '最新价', '股票代码', '所属同花顺行业', '准备拉升(条件说明)[20240110]', '技术形态[20240110]', '最新涨跌幅'], ]
            print_(result_set)
            da = res['xuangu_tableV1'].loc[:, ['股票简称']].values.ravel()
            [stock_list.append(i) for i in da]
        except Exception as e:
            print_(e)
        # data = qs.intraday_data('澳柯玛').tail(1)
        if not message_queue.empty():
            message_queue.queue.clear()
        message_queue.put(stock_list)
        print_(f'队列放入:{stock_list}')
        # for stock_name in stock_list:
        #     t.sleep(1)
        #     res = wc.get(query=f'{stock_name}最近30个交易日,股票开盘价和收盘价,最高价最低价成交量,散户数量,机构数量,大单数量,中单数量,小单数量,大单金额,中单金额,小单金额')
        #     print_(res)
        stock_list.clear()
        t.sleep(100)


quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']



def watch_data_history():
    # 获取所有信息
    while True:
        try:
            watch_code_list = pgsql.get_db().query(WatchCode).all()
            watch_code_list = [i.code.split(".")[-1].lower() + i.code.split(".")[0] for i in watch_code_list]
            all_info = pd.DataFrame(quotation.stocks(watch_code_list, prefix=True)).T
            # all_info[all_info['涨跌(%)']>1 & all_info['close']< all_info['open']]
            # all_info[(all_info['涨跌(%)'] > 1) & (all_info['close'] < all_info['open'])]
            # all_info[(all_info['涨跌(%)'] > 1) & (all_info['close'] < all_info['open'])].sort_values(by='振幅', ascending=False)
            if not all_info.empty:
                code = all_info[(all_info['涨跌(%)'] > 1) & (all_info['close'] < all_info['open'])].sort_values(by='振幅', ascending=False).iloc[1, :].code

                pgsql.create(WaitBuyList(code=code, market=code[:2]))
        except Exception as e:
            print(traceback.print_exc())
        t.sleep(600)
