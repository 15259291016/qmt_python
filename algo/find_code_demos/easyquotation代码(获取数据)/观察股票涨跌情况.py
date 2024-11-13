import easyquotation
import pandas as pd

quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']

# 获取所有股票行情
all_data = quotation.market_snapshot(prefix=True)  # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀
print(all_data)
# # 单只股票
# one_data = quotation.real('162411')  # 支持直接指定前缀，如 'sh000001'
#
# # 多只股票
# many_data = quotation.stocks(['000001', '162411'])
#
# # 同时获取指数和行情
part_data = quotation.stocks(['sh000001', 'sz000001'], prefix=True)
print(part_data)
# print(all_data)


all_info = pd.DataFrame(quotation.market_snapshot(prefix=True).values())
# >100亿 总量
sz_gt100 = len(all_info[all_info['总市值'] >= 100])
# >100亿 10%数量
sz_gt100_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] >= 100)])
# >100亿 3%-7%数量
sz_gt100_zd_gt3lt7 = len(
    all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] >= 100)])
# >100亿 0%--3%数量
sz_gt100_zd_gt0lt3 = len(
    all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] >= 100)])
# >100亿 -3%-0%%数量
sz_gt100_zd_gt_3lt0 = len(
    all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (all_info['总市值'] >= 100)])
# >100亿 -7%-3%数量
sz_gt100_zd_gt_7lt_3 = len(
    all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] >= 100)])
# >100亿 -10%-7%数量
sz_gt100_zd_gt_7lt_10 = len(
    all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (all_info['总市值'] >= 100)])
# >100亿 -10%%数量
sz_gt100_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] >= 100)])
# 50-100亿 总量
sz_gt50lt100 = len(all_info[(all_info['总市值'] < 100) & (all_info['总市值'] >= 50)])
# 50-100亿 10%数量
sz_gt50lt100_zd_gt10 = len(
    all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] < 100) & (all_info['总市值'] >= 50)])
# 50-100亿 7%--3%数量
sz_gt50lt100_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (
            all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
# 50-100亿 0%--3%数量
sz_gt50lt100_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (
            all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
# 50-100亿 -3%-0%%数量
sz_gt50lt100_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (
            all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
# 50-100亿 -7%-3%数量
sz_gt50lt100_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (
            all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
# 50-100亿 -10%-7%数量
sz_gt50lt100_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (
            all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
# 50-100亿 -10%%数量
sz_gt50lt100_zd_lt_10 = len(
    all_info[(all_info['涨跌(%)'] < -10) & (all_info['总市值'] > 50) & (all_info['总市值'] < 100)])
# <50亿 总量
sz_lt50 = len(all_info[all_info['总市值'] < 50])
# <50亿 10%数量
sz_lt50_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] <= 50)])

# <50亿 7%--3%数量
sz_lt50_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] > 3) & (all_info['涨跌(%)'] < 7) & (all_info['总市值'] < 50)])
# <50亿 0%--3%数量
sz_lt50_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] > 0) & (all_info['涨跌(%)'] < 3) & (all_info['总市值'] < 50)])
# <50亿 -3%-0%%数量
sz_lt50_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] > -3) & (all_info['涨跌(%)'] < 0) & (all_info['总市值'] < 50)])
# <50亿 -7%-3%数量
sz_lt50_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] > -7) & (all_info['涨跌(%)'] < -3) & (all_info['总市值'] < 50)])
# <50亿 -10%-7%数量
sz_lt50_zd_gt_7lt_10 = len(
    all_info[(all_info['涨跌(%)'] > -10) & (all_info['涨跌(%)'] < -7) & (all_info['总市值'] < 50)])
# <50亿 -10%%数量
sz_lt50_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] < -10) & (all_info['总市值'] < 50)])

# >100亿 5%数量
sz_gt100_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] > 100)])
# 50-100亿 5%数量
sz_gt50lt100_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] < 100) & (all_info['总市值'] > 50)])
# <50亿 5%数量
sz_lt50_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] < 50)])
# >10% 数量
zd_gt10 = len(all_info[all_info['涨跌(%)'] > 10])
# >5% 数量
zd_gt5 = len(all_info[all_info['涨跌(%)'] > 5])
# >3% 数量
zd_gt3 = len(all_info[all_info['涨跌(%)'] > 3])

# ---------------------盘后--------------------------------
# 5日 涨超5%数量
# res = wc.get(query='5日涨幅超过5%')
# # 5日 涨超10%数量
# res = wc.get(query='5日涨幅超过10%')
# # 跌超 10%数量
# zd_lt10 = all_info[all_info['涨跌(%)'] < -10]
data = {
    "sz_gt100": sz_gt100,
    "sz_gt100_zd_gt10": sz_gt100_zd_gt10,
    "sz_gt100_zd_gt3lt7": sz_gt100_zd_gt3lt7,
    "sz_gt100_zd_gt0lt3": sz_gt100_zd_gt0lt3,
    "sz_gt100_zd_gt_3lt0": sz_gt100_zd_gt_3lt0,
    "sz_gt100_zd_gt_7lt_3": sz_gt100_zd_gt_7lt_3,
    "sz_gt100_zd_gt_7lt_10": sz_gt100_zd_gt_7lt_10,
    "sz_gt100_zd_lt_10": sz_gt100_zd_lt_10,
    "sz_gt50lt100": sz_gt50lt100,
    "sz_gt50lt100_zd_gt10": sz_gt50lt100_zd_gt10,
    "sz_gt50lt100_zd_lt7gt3": sz_gt50lt100_zd_lt7gt3,
    "sz_gt50lt100_zd_gt0lt3": sz_gt50lt100_zd_gt0lt3,
    "sz_gt50lt100_zd_gt_3lt0": sz_gt50lt100_zd_gt_3lt0,
    "sz_gt50lt100_zd_gt_7lt_3": sz_gt50lt100_zd_gt_7lt_3,
    "sz_gt50lt100_zd_gt_7lt_10": sz_gt50lt100_zd_gt_7lt_10,
    "sz_gt50lt100_zd_lt_10": sz_gt50lt100_zd_lt_10,
    "sz_lt50": sz_lt50,
    "sz_lt50_zd_gt10": sz_lt50_zd_gt10,
    "sz_lt50_zd_lt7gt3": sz_lt50_zd_lt7gt3,
    "sz_lt50_zd_gt0lt3": sz_lt50_zd_gt0lt3,
    "sz_lt50_zd_gt_3lt0": sz_lt50_zd_gt_3lt0,
    "sz_lt50_zd_gt_7lt_3": sz_lt50_zd_gt_7lt_3,
    "sz_lt50_zd_gt_7lt_10": sz_lt50_zd_gt_7lt_10,
    "sz_lt50_zd_lt_10": sz_lt50_zd_lt_10,
    "sz_gt100_zd_gt5": sz_gt100_zd_gt5,
    "sz_gt50lt100_zd_gt5": sz_gt50lt100_zd_gt5,
    "sz_lt50_zd_gt5": sz_lt50_zd_gt5,
    "zd_gt10": zd_gt10,
    "zd_gt5": zd_gt5,
    "zd_gt3": zd_gt3
}
print(f'表格\n{data}')
