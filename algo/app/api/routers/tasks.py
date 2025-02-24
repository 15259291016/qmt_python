# app/tasks.py
from datetime import datetime
import easyquotation
import os
import efinance as ef
import pywencai as wc
import webbrowser
import time

def my_task():
    """定时任务函数"""
    print("定时任务执行了！当前时间：", datetime.now())

def morning_analysis():
    """定时任务函数"""
    question_list = [
        '剔除ST,准备拉升',
        '主力资金流入,剔除ST,剔除次新,剔除北交所,形成拉升通道',
        '量比大于5的个股,排除高开8%以上的个股,同时剔除涨幅为负或0的个股',
        '委比为正、主力净买额为正,5日、10日均线向上发散',
        '在9:25分点击现量排名，选择现量在一万手以上的个股',
        '量比大于1.8且涨幅在0-2%之间的个股也值得关注',
        '大盘走势和市场热点板块，优先选择板块内趋势向上的个股',
        '选择流通盘较小（如小于200亿）且处于阶段性底部的个股',
        '选择短期均线（如5日、10日、21日均线）多头排列的个股',
        '关注KDJ低位金叉（40分界线以上）且周、月KDJ向上发散的个股',
        '主力资金流入或热点板块，快速筛选',
    ]

    for i in question_list:
        print(i)
        question_wc(i)
        time.sleep(10)



now = datetime.now()
day = now.strftime("%Y-%m-%d")

quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']


def print_(str):
    print(str)


def print__data(res):
    if res is None: return
    print_(res)
    try:
        res.rename(columns={'股票简称': 'name', '最新价': 'price'}, inplace=True)
        res.sort_values(by='code', ascending=True, inplace=True, )
        res = res.loc[:, ['code', 'name', 'price']].drop_duplicates()
        # for row in res.iterrows():
        #     try:
        #         result_set = wc.get(query=row[1]['name'], )
        #         df3 = pd.merge(result_set['barline3'], result_set['历史主力资金流向']['barline3'])

        #         # print__demo(result_set['近期重要事件'])
        #         # print_(result_set['所属概念列表']['诊股概念分类名称'].to_list())
        #         # print_("-" * 100)
        #         # print_(f"支撑位:{result_set['kline2'].iloc[0:]['止盈止损(支撑位)'][0]} ------压力位:{result_set['kline2'].iloc[0:]['止盈止损(压力位)'][0]}----{result_set['支撑位压力位']}")
        #         # if '若能站稳，意味着上涨空间打开，可适当关注5日均线，若跌破可考虑止盈' in result_set['支撑位压力位']:
        #         # print_(result_set['财务数据'])
        #         # print_(result_set['估值指标']['市净率']['txt1'][40:])
        #         # print_(result_set['估值指标']['市销率']['txt1'][52:])
        #         # print_(result_set['十大股东持股比例'].loc[:, ['大股东名称', '大股东持股比例', '大股东公告日期', '股东类型']])
        #         # result_set['估值指标']['市销率']['labelLine'].tail(30)           # 有参考价值
        #         # result_set['估值指标']['市净率']['labelLine'].tail(30)           # 有参考价值
        #         # result_set['估值指标']['市净率']['labelLine'].tail(30)           # 有参考价值
        #         # result_set['barline3']
        #         # result_set['所属概念列表']
        #         # result_set['历史主力资金流向']['barline3']
        #         # result_set['kline2']
        #         # result_set['估值指标']['市盈率']['labelLine']
        #         # result_set['估值指标']['市净率']['labelLine']
        #         # result_set['估值指标']['市销率']['labelLine']
        #         # print_(df3)
        #         # else:
        #         #     pass
        #         # print_(df3)
        #         print_(df3)
        #     except Exception as e:
        #         print_(e)
        if res is not None and 'code' in res.columns:
            return res['code'].to_list()
    except Exception as e:
        print_(e)
    return []


def code_list_to_csv(code_list: list):
    """
    将股票代码列表转换为csv文件
    """
    if not os.path.exists(f'./data/{day}'):
        os.makedirs(f'./data/{day}')
    if code_list:
        freq = 1
        for i in code_list:
            df = ef.stock.get_quote_history(i, klt=freq)
            df.to_csv(f'./data/{day}/{i}.csv', encoding='utf-8-sig', index=None)


def question_wc(question):
    res = None
    try:
        res = wc.get(query=question)
    except Exception as e:
        webbrowser.open('https://www.iwencai.com/unifiedwap/reptile.html?returnUrl=https%3A%2F%2Fwww.iwencai.com%2Funifiedwap%2Fhome%2Findex%3Fsign%3D1709793871013&sessionId=117.30.119.18&antType=unifiedwap')
        print_(e)
        time.sleep(20)
    if res is not None:
        res_list = print__data(res)
        code_list_to_csv(res_list)
        return res_list
    return None


# 用于处理队列中的消息的函数
# 竞价策略
# 百度查这个 ：集合竞价怎么选股
# res = wc.get(query=)

# https://zhuanlan.zhihu.com/p/370195994#:~:text=%E2%80%9C%E9%9B%86%E5%90%88%E7%AB%9E%E4%BB%B7%E6%89%93%E6%9D%BF%E2%80%9D%E8%BD%BB%E6%9D%BE%E9%80%89%E5%87%BA%E6%B6%A8%E5%81%9C%E8%82%A1%20%28%E5%86%85%E9%99%84%E6%8C%87%E6%A0%87%E6%BA%90%E7%A0%81%29%201%20%E4%B8%89%E7%A7%8D%E5%85%B8%E5%9E%8B%E8%B5%B0%E5%8A%BF%EF%BC%8C%E7%9C%8B%E6%87%82%E9%9B%86%E5%90%88%E7%AB%9E%E4%BB%B7%E7%9A%84%E6%89%93%E6%9D%BF%E7%AD%96%E7%95%A5%20%E5%AF%B9%E5%A4%A7%E8%B5%84%E9%87%91%E8%80%8C%E8%A8%80%EF%BC%8C%E9%9B%86%E5%90%88%E7%AB%9E%E4%BB%B7%E6%98%AF%E5%85%A8%E5%A4%A9%E6%93%8D%E7%9B%98%E6%B4%BB%E5%8A%A8%E7%9A%84%E5%BA%8F%E5%B9%95%EF%BC%8C%E5%A4%9A%E7%A9%BA%E5%8F%8C%E6%96%B9%E7%BB%8F%E5%B8%B8%E5%9C%A8%E8%BF%99%E6%97%B6%E8%BF%9B%E8%A1%8C%E7%AC%AC%E4%B8%80%E8%BD%AE%E6%83%A8%E7%83%88%E5%8E%AE%E6%9D%80%E3%80%82%20%E5%9C%A8%E8%BF%9915%E5%88%86%E9%92%9F%E9%87%8C%EF%BC%8C%E5%BE%80%E5%BE%80%E4%BC%9A%E4%BD%93%E7%8E%B0%E5%A4%A7%E8%B5%84%E9%87%91%E6%97%A5%E5%86%85%E7%9A%84%E5%81%9A%E7%9B%98%E6%84%8F%E5%9B%BE%E3%80%82%20...%202,%E7%AC%AC%E4%B8%89%E7%A7%8D%EF%BC%8C%E6%A8%AA%E7%9B%98%E8%B5%B0%E9%AB%98%E3%80%82%20%E6%8C%87%E7%9A%84%E6%98%AF9%3A20%E4%B9%8B%E5%90%8E%EF%BC%8C%E6%92%AE%E5%90%88%E4%BB%B7%E6%A0%BC%E7%A8%B3%E5%AE%9A%E4%B8%8D%E5%8A%A8%EF%BC%8C%E7%AB%9E%E4%BB%B7%E8%BD%A8%E8%BF%B9%E5%91%88%E4%B8%80%E6%9D%A1%E7%9B%B4%E7%BA%BF%20%28%E5%A4%A7%E8%B5%84%E9%87%91%E6%8E%A7%E7%9B%98%29%EF%BC%8C%E6%9C%80%E7%BB%88%E7%AB%9E%E4%BB%B7%E5%B0%8F%E5%B9%85%E9%AB%98%E5%BC%80%E6%88%96%E5%B9%B3%E5%BC%80%E3%80%82%20...%205%20%E6%9C%80%E5%90%8E%EF%BC%8C%E5%86%8D%E9%80%81%E5%A4%A7%E5%AE%B6%E4%B8%80%E4%B8%AA%E9%80%9A%E8%BE%BE%E4%BF%A1%E9%9B%86%E5%90%88%E7%AB%9E%E4%BB%B7%E9%80%89%E8%82%A1%E5%85%AC%E5%BC%8F%EF%BC%9A%20%7B9%E7%82%B925%E5%88%86-9%E7%82%B929%E5%88%86%E9%80%89%E8%82%A1%7D%20


# def watch(code_list: list):
#     print_('观察线程已经启动')
#     print_(code_list)
#     while True:
#         try:
#             print_(quotation.stocks(code_list, prefix=True))
#             time.sleep(60)
#         except Exception as e:
#             print_(e)
#             time.sleep(60)


# question_list = [
#     '剔除ST,准备拉升',
#     '主力资金流入,剔除ST,剔除次新,剔除北交所,形成拉升通道',
#     '量比大于5的个股,排除高开8%以上的个股,同时剔除涨幅为负或0的个股',
#     '委比为正、主力净买额为正,5日、10日均线向上发散',
#     '在9:25分点击现量排名，选择现量在一万手以上的个股',
#     '量比大于1.8且涨幅在0-2%之间的个股也值得关注',
#     '大盘走势和市场热点板块，优先选择板块内趋势向上的个股',
#     '选择流通盘较小（如小于200亿）且处于阶段性底部的个股',
#     '选择短期均线（如5日、10日、21日均线）多头排列的个股',
#     '关注KDJ低位金叉（40分界线以上）且周、月KDJ向上发散的个股',
#     '主力资金流入或热点板块，快速筛选',
# ]

# watch_list = []
# for i in question_list:
#     print(i)
#     question_wc(i)
#     time.sleep(10)
    # if res is not None:
    #     print_(res)
    #     watch_list = watch_list + res
        # print_(quotation.stocks(res, prefix=True))