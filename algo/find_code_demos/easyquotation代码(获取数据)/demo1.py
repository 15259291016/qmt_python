import time

import easyquotation
import pandas as pd
from datetime import datetime


def market_data():
    all_info = pd.DataFrame(quotation.market_snapshot(prefix=True).values())
    # >2000亿 总量
    sz_gt2000 = len(all_info[all_info['总市值'] >= 2000])
    # >2000亿 10%数量
    sz_gt2000_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] >= 2000)])
    # >2000亿 10%数量 比例
    sz_gt2000_zd_gt10_ratio = sz_gt2000_zd_gt10 / sz_gt2000
    # >2000亿 3%-7%数量
    sz_gt2000_zd_gt3lt7 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] >= 2000)])
    # sz_gt2000_zd_gt10 比例
    sz_gt2000_zd_gt3lt7_ratio = sz_gt2000_zd_gt3lt7 / sz_gt2000
    # >2000亿 0%--3%数量
    sz_gt2000_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] >= 2000)])
    # >2000亿 0%--3%数量 比例
    sz_gt2000_zd_gt0lt3_ratio = sz_gt2000_zd_gt0lt3 / sz_gt2000
    # >2000亿 -3%-0%%数量
    sz_gt2000_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (all_info['总市值'] >= 2000)])
    # >2000亿 -3%-0%%数量 比例
    sz_gt2000_zd_gt_3lt0_ratio = sz_gt2000_zd_gt_3lt0 / sz_gt2000
    # >2000亿 -7%-3%数量
    sz_gt2000_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] >= 2000)])
    # >2000亿 -7%-3%数量 比例
    sz_gt2000_zd_gt_7lt_3_ratio = sz_gt2000_zd_gt_7lt_3 / sz_gt2000
    # >2000亿 -10%-7%数量
    sz_gt2000_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (all_info['总市值'] >= 2000)])
    # >2000亿 -10%-7%数量 比例
    sz_gt2000_zd_gt_7lt_10_ratio = sz_gt2000_zd_gt_7lt_10 / sz_gt2000
    # >2000亿 -10%%数量
    sz_gt2000_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] >= 2000)])
    # >2000亿 -10%%数量 比例
    sz_gt2000_zd_lt_10_ratio = sz_gt2000_zd_lt_10 / sz_gt2000
    # >1000亿 总量
    sz_gt1000 = len(all_info[(all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 10%数量
    sz_gt1000_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 10%数量 比例
    sz_gt1000_zd_gt10_ratio = sz_gt1000_zd_gt10 / sz_gt1000
    # >1000亿 7%--3%数量
    sz_gt1000_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 7%--3%数量 比例
    sz_gt1000_zd_lt7gt3_ratio = sz_gt1000_zd_lt7gt3 / sz_gt1000
    # >1000亿 0%--3%数量
    sz_gt1000_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 0%--3%数量 比例
    sz_gt1000_zd_gt0lt3_ratio = sz_gt1000_zd_gt0lt3 / sz_gt1000
    # >1000亿 -3%-0%%数量
    sz_gt1000_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 -3%-0%%数量 比例
    sz_gt1000_zd_gt_3lt0_ratio = sz_gt1000_zd_gt_3lt0 / sz_gt1000
    # >1000亿 -7%-3%数量
    sz_gt1000_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 -7%-3%数量 比例
    sz_gt1000_zd_gt_7lt_3_ratio = sz_gt1000_zd_gt_7lt_3 / sz_gt1000
    # >1000亿 -10%-7%数量
    sz_gt1000_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 -10%-7%数量 比例
    sz_gt1000_zd_gt_7lt_10_ratio = sz_gt1000_zd_gt_7lt_10 / sz_gt1000
    # >1000亿 -10%%数量
    sz_gt1000_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] < 2000) & (all_info['总市值'] >= 1000)])
    # >1000亿 -10%%数量 比例
    sz_gt1000_zd_lt_10_ratio = sz_gt1000_zd_lt_10 / sz_gt1000
    # >500亿 总量
    sz_gt500 = len(all_info[(all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 10%数量
    sz_gt500_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 10%数量 比例
    sz_gt500_zd_gt10_ratio = sz_gt500_zd_gt10 / sz_gt500
    # >500亿 7%--3%数量
    sz_gt500_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 7%--3%数量 比例
    sz_gt500_zd_lt7gt3_ratio = sz_gt500_zd_lt7gt3 / sz_gt500
    # >500亿 0%--3%数量
    sz_gt500_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 0%--3%数量 比例
    sz_gt500_zd_gt0lt3_ratio = sz_gt500_zd_gt0lt3 / sz_gt500
    # >500亿 -3%-0%%数量
    sz_gt500_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 -3%-0%%数量 比例
    sz_gt500_zd_gt_3lt0_ratio = sz_gt500_zd_gt_3lt0 / sz_gt500
    # >500亿 -7%-3%数量
    sz_gt500_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 -7%-3%数量 比例
    sz_gt500_zd_gt_7lt_3_ratio = sz_gt500_zd_gt_7lt_3 / sz_gt500
    # >500亿 -10%-7%数量
    sz_gt500_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 -10%-7%数量 比例
    sz_gt500_zd_gt_7lt_10_ratio = sz_gt500_zd_gt_7lt_10 / sz_gt500
    # >500亿 -10%%数量
    sz_gt500_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] < 1000) & (all_info['总市值'] >= 500)])
    # >500亿 -10%%数量 比例
    sz_gt500_zd_lt_10_ratio = sz_gt500_zd_lt_10 / sz_gt500
    # >100亿 总量
    sz_gt100 = len(all_info[all_info['总市值'] >= 100])
    # >100亿 10%数量
    sz_gt100_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] >= 100)])
    # >100亿 10%数量 比例
    sz_gt100_zd_gt10_ratio = sz_gt100_zd_gt10 / sz_gt100
    # >100亿 3%-7%数量
    sz_gt100_zd_gt3lt7 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] >= 100)])
    # >100亿 3%-7%数量 比例
    sz_gt100_zd_gt3lt7_ratio = sz_gt100_zd_gt3lt7 / sz_gt100
    # >100亿 0%--3%数量
    sz_gt100_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] >= 100)])
    # >100亿 0%--3%数量 比例
    sz_gt100_zd_gt0lt3_ratio = sz_gt100_zd_gt0lt3 / sz_gt100
    # >100亿 -3%-0%%数量
    sz_gt100_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (all_info['总市值'] >= 100)])
    # >100亿 -3%-0%%数量 比例
    sz_gt100_zd_gt_3lt0_ratio = sz_gt100_zd_gt_3lt0 / sz_gt100
    # >100亿 -7%-3%数量
    sz_gt100_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] >= 100)])
    # >100亿 -7%-3%数量 比例
    sz_gt100_zd_gt_7lt_3_ratio = sz_gt100_zd_gt_7lt_3 / sz_gt100
    # >100亿 -10%-7%数量
    sz_gt100_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (all_info['总市值'] >= 100)])
    # >100亿 -10%-7%数量 比例
    sz_gt100_zd_gt_7lt_10_ratio = sz_gt100_zd_gt_7lt_10 / sz_gt100
    # >100亿 -10%%数量
    sz_gt100_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] <= -10) & (all_info['总市值'] >= 100)])
    # >100亿 -10%%数量 比例
    sz_gt100_zd_lt_10_ratio = sz_gt100_zd_lt_10 / sz_gt100
    # 50-100亿 总量
    sz_gt50lt100 = len(all_info[(all_info['总市值'] < 100) & (all_info['总市值'] >= 50)])
    # 50-100亿 10%数量
    sz_gt50lt100_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] < 100) & (all_info['总市值'] >= 50)])
    # 50-100亿 10%数量 比例
    sz_gt50lt100_zd_gt10_ratio = sz_gt50lt100_zd_gt10 / sz_gt50lt100
    # 50-100亿 7%--3%数量
    sz_gt50lt100_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] >= 3) & (all_info['涨跌(%)'] <= 7) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 7%--3%数量 比例
    sz_gt50lt100_zd_lt7gt3_ratio = sz_gt50lt100_zd_lt7gt3 / sz_gt50lt100
    # 50-100亿 0%--3%数量
    sz_gt50lt100_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] >= 0) & (all_info['涨跌(%)'] <= 3) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 0%--3%数量 比例
    sz_gt50lt100_zd_gt0lt3_ratio = sz_gt50lt100_zd_gt0lt3 / sz_gt50lt100
    # 50-100亿 -3%-0%%数量
    sz_gt50lt100_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] >= -3) & (all_info['涨跌(%)'] <= 0) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -3%-0%%数量 比例
    sz_gt50lt100_zd_gt_3lt0_ratio = sz_gt50lt100_zd_gt_3lt0 / sz_gt50lt100
    # 50-100亿 -7%-3%数量
    sz_gt50lt100_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] >= -7) & (all_info['涨跌(%)'] <= -3) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -7%-3%数量 比例
    sz_gt50lt100_zd_gt_7lt_3_ratio = sz_gt50lt100_zd_gt_7lt_3 / sz_gt50lt100
    # 50-100亿 -10%-7%数量
    sz_gt50lt100_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] >= -10) & (all_info['涨跌(%)'] <= -7) & (all_info['总市值'] >= 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -10%-7%数量 比例
    sz_gt50lt100_zd_gt_7lt_10_ratio = sz_gt50lt100_zd_gt_7lt_10 / sz_gt50lt100
    # 50-100亿 -10%%数量
    sz_gt50lt100_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] < -10) & (all_info['总市值'] > 50) & (all_info['总市值'] < 100)])
    # 50-100亿 -10%%数量 比例
    sz_gt50lt100_zd_lt_10_ratio = sz_gt50lt100_zd_lt_10 / sz_gt50lt100
    # <50亿 总量
    sz_lt50 = len(all_info[all_info['总市值'] < 50])
    # <50亿 10%数量
    sz_lt50_zd_gt10 = len(all_info[(all_info['涨跌(%)'] >= 10) & (all_info['总市值'] <= 50)])
    # <50亿 10%数量 比例
    sz_lt50_zd_gt10_ratio = sz_lt50_zd_gt10 / sz_lt50

    # <50亿 7%--3%数量
    sz_lt50_zd_lt7gt3 = len(all_info[(all_info['涨跌(%)'] > 3) & (all_info['涨跌(%)'] < 7) & (all_info['总市值'] < 50)])
    # <50亿 7%--3%数量 比例
    sz_lt50_zd_lt7gt3_ratio = sz_lt50_zd_lt7gt3 / sz_lt50
    # <50亿 0%--3%数量
    sz_lt50_zd_gt0lt3 = len(all_info[(all_info['涨跌(%)'] > 0) & (all_info['涨跌(%)'] < 3) & (all_info['总市值'] < 50)])
    # <50亿 0%--3%数量 比例
    sz_lt50_zd_gt0lt3_ratio = sz_lt50_zd_gt0lt3 / sz_lt50
    # <50亿 -3%-0%%数量
    sz_lt50_zd_gt_3lt0 = len(all_info[(all_info['涨跌(%)'] > -3) & (all_info['涨跌(%)'] < 0) & (all_info['总市值'] < 50)])
    # <50亿 -3%-0%%数量 比例
    sz_lt50_zd_gt_3lt0_ratio = sz_lt50_zd_gt_3lt0 / sz_lt50
    # <50亿 -7%-3%数量
    sz_lt50_zd_gt_7lt_3 = len(all_info[(all_info['涨跌(%)'] > -7) & (all_info['涨跌(%)'] < -3) & (all_info['总市值'] < 50)])
    # <50亿 -7%-3%数量 比例
    sz_lt50_zd_gt_7lt_3_ratio = sz_lt50_zd_gt_7lt_3 / sz_lt50
    # <50亿 -10%-7%数量
    sz_lt50_zd_gt_7lt_10 = len(all_info[(all_info['涨跌(%)'] > -10) & (all_info['涨跌(%)'] < -7) & (all_info['总市值'] < 50)])
    # <50亿 -10%-7%数量 比例
    sz_lt50_zd_gt_7lt_10_ratio = sz_lt50_zd_gt_7lt_10 / sz_lt50
    # <50亿 -10%%数量
    sz_lt50_zd_lt_10 = len(all_info[(all_info['涨跌(%)'] < -10) & (all_info['总市值'] < 50)])
    # <50亿 -10%%数量 比例
    sz_lt50_zd_lt_10_ratio = sz_lt50_zd_lt_10 / sz_lt50

    # >100亿 5%数量
    sz_gt100_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] > 100)])
    # >100亿 5%数量 比例
    sz_gt100_zd_gt5_ratio = sz_gt100_zd_gt5 / sz_gt100
    # 50-100亿 5%数量
    sz_gt50lt100_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] < 100) & (all_info['总市值'] > 50)])
    # 50-100亿 5%数量 比例
    sz_gt50lt100_zd_gt5_ratio = sz_gt50lt100_zd_gt5 / sz_gt50lt100
    # <50亿 5%数量
    sz_lt50_zd_gt5 = len(all_info[(all_info['涨跌(%)'] > 5) & (all_info['总市值'] < 50)])
    # <50亿 5%数量 比例
    sz_lt50_zd_gt5_ratio = sz_lt50_zd_gt5 / sz_lt50
    # >10% 数量
    zd_gt10 = len(all_info[all_info['涨跌(%)'] > 10])
    # >10% 数量 比例
    zd_gt10_ratio = zd_gt10 / len(all_info)
    # >5% 数量
    zd_gt5 = len(all_info[all_info['涨跌(%)'] > 5])
    # >5% 数量 比例
    zd_gt5_ratio = zd_gt5 / len(all_info)
    # >3% 数量
    zd_gt3 = len(all_info[all_info['涨跌(%)'] > 3])
    # >3% 数量 比例
    zd_gt3_ratio = zd_gt3 / len(all_info)

    # ---------------------盘后--------------------------------
    # 5日 涨超5%数量
    # res = wc.get(query='5日涨幅超过5%')
    # # 5日 涨超10%数量
    # res = wc.get(query='5日涨幅超过10%')
    # # 跌超 10%数量
    # zd_lt10 = all_info[all_info['涨跌(%)'] < -10]
    return {
        ">2000亿 总量": sz_gt2000,  # >2000亿 总量
        ">2000亿 10%数量": sz_gt2000_zd_gt10,  # >2000亿 10%数量
        ">2000亿 10%数量 比例": sz_gt2000_zd_gt10_ratio,  # >2000亿 10%数量 比例
        ">2000亿 3%-7%数量": sz_gt2000_zd_gt3lt7,  # >2000亿 3%-7%数量
        ">2000亿 3%-7%数量 比例": sz_gt2000_zd_gt3lt7_ratio,  # >2000亿 3%-7%数量 比例
        ">2000亿 0%--3%数量": sz_gt2000_zd_gt0lt3,  # >2000亿 0%--3%数量
        ">2000亿 0%--3%数量 比例": sz_gt2000_zd_gt0lt3_ratio,  # >2000亿 0%--3%数量 比例
        ">2000亿 -3%-0%%数量": sz_gt2000_zd_gt_3lt0,  # >2000亿 -3%-0%%数量
        ">2000亿 -3%-0%%数量 比例": sz_gt2000_zd_gt_3lt0_ratio,  # >2000亿 -3%-0%%数量 比例
        ">2000亿 -7%-3%数量": sz_gt2000_zd_gt_7lt_3,  # >2000亿 -7%-3%数量
        ">2000亿 -7%-3%数量 比例": sz_gt2000_zd_gt_7lt_3_ratio,  # >2000亿 -7%-3%数量 比例
        ">2000亿 -10%-7%数量": sz_gt2000_zd_gt_7lt_10,  # >2000亿 -10%-7%数量
        ">2000亿 -10%-7%数量 比例": sz_gt2000_zd_gt_7lt_10_ratio,  # >2000亿 -10%-7%数量 比例
        ">2000亿 -10%%数量": sz_gt2000_zd_lt_10,  # >2000亿 -10%%数量
        ">2000亿 -10%%数量 比例": sz_gt2000_zd_lt_10_ratio,  # >2000亿 -10%%数量 比例
        ">1000亿 总量": sz_gt1000,  # >1000亿 总量
        ">1000亿 10%数量": sz_gt1000_zd_gt10,  # >1000亿 10%数量
        ">1000亿 10% 比例": sz_gt1000_zd_gt10_ratio,  # >1000亿 10%数量 比例
        ">1000亿 7%--3%数量": sz_gt1000_zd_lt7gt3,  # >1000亿 7%--3%数量
        ">1000亿 7%--3%数量 比例": sz_gt1000_zd_lt7gt3_ratio,  # >1000亿 7%--3%数量 比例
        ">1000亿 0%--3%数量": sz_gt1000_zd_gt0lt3,  # >1000亿 0%--3%数量
        ">1000亿 0%--3%数量 比例": sz_gt1000_zd_gt0lt3_ratio,  # >1000亿 0%--3%数量 比例
        ">1000亿 -3%-0%%数量": sz_gt1000_zd_gt_3lt0,  # >1000亿 -3%-0%%数量
        ">1000亿 -3%-0%%数量 比例": sz_gt1000_zd_gt_3lt0_ratio,  # >1000亿 -3%-0%%数量 比例
        ">1000亿 -7%-3%数量": sz_gt1000_zd_gt_7lt_3,  # >1000亿 -7%-3%数量
        ">1000亿 -7%-3%数量 比例": sz_gt1000_zd_gt_7lt_3_ratio,  # >1000亿 -7%-3%数量 比例
        ">1000亿 -10%-7%数量": sz_gt1000_zd_gt_7lt_10,  # >1000亿 -10%-7%数量
        ">1000亿 -10%-7%数量 比例": sz_gt1000_zd_gt_7lt_10_ratio,  # >1000亿 -10%-7%数量 比例
        ">1000亿 -10%%数量": sz_gt1000_zd_lt_10,  # >1000亿 -10%%数量
        ">1000亿 -10%%数量 比例": sz_gt1000_zd_lt_10_ratio,  # >1000亿 -10%%数量 比例
        ">500亿 总量": sz_gt500,  # >500亿 总量
        ">500亿 10%数量": sz_gt500_zd_gt10,  # >500亿 10%数量
        ">500亿 10%数量 比例": sz_gt500_zd_gt10_ratio,  # >500亿 10%数量 比例
        ">500亿 7%--3%数量": sz_gt500_zd_lt7gt3,  # >500亿 7%--3%数量
        ">500亿 7%--3%数量 比例": sz_gt500_zd_lt7gt3_ratio,  # >500亿 7%--3%数量 比例
        ">500亿 0%--3%数量": sz_gt500_zd_gt0lt3,  # >500亿 0%--3%数量
        ">500亿 0%--3%数量 比例": sz_gt500_zd_gt0lt3_ratio,  # >500亿 0%--3%数量 比例
        ">500亿 -3%-0%%数量": sz_gt500_zd_gt_3lt0,  # >500亿 -3%-0%%数量
        ">500亿 -3%-0%%数量 比例": sz_gt500_zd_gt_3lt0_ratio,  # >500亿 -3%-0%%数量 比例
        ">500亿 -7%-3%数量": sz_gt500_zd_gt_7lt_3,  # >500亿 -7%-3%数量
        ">500亿 -7%-3%数量 比例": sz_gt500_zd_gt_7lt_3_ratio,  # >500亿 -7%-3%数量 比例
        ">500亿 -10%-7%数量": sz_gt500_zd_gt_7lt_10,  # >500亿 -10%-7%数量
        ">500亿 -10%-7%数量 比例": sz_gt500_zd_gt_7lt_10_ratio,  # >500亿 -10%-7%数量 比例
        ">500亿 -10%%数量": sz_gt500_zd_lt_10,  # >500亿 -10%%数量
        ">500亿 -10%%数量 比例": sz_gt500_zd_lt_10_ratio,  # >500亿 -10%%数量 比例
        ">100亿 总量": sz_gt100,  # >100亿 总量
        ">100亿 10%数量": sz_gt100_zd_gt10,  # >100亿 10%数量
        ">100亿 10%数量 比例": sz_gt100_zd_gt10_ratio,  # >100亿 10%数量 比例
        ">100亿 3%-7%数量": sz_gt100_zd_gt3lt7,  # >100亿 3%-7%数量
        ">100亿 3%-7%数量 比例": sz_gt100_zd_gt3lt7_ratio,  # >100亿 3%-7%数量 比例
        ">100亿 0%--3%数量": sz_gt100_zd_gt0lt3,  # >100亿 0%--3%数量
        ">100亿 0%--3%数量 比例": sz_gt100_zd_gt0lt3_ratio,  # >100亿 0%--3%数量 比例
        ">100亿 -3%-0%%数量": sz_gt100_zd_gt_3lt0,  # >100亿 -3%-0%%数量
        ">100亿 -3%-0%%数量 比例": sz_gt100_zd_gt_3lt0_ratio,  # >100亿 -3%-0%%数量 比例
        ">100亿 -7%-3%数量": sz_gt100_zd_gt_7lt_3,  # >100亿 -7%-3%数量
        ">100亿 -7%-3%数量 比例": sz_gt100_zd_gt_7lt_3_ratio,  # >100亿 -7%-3%数量 比例
        ">100亿 -10%-7%数量": sz_gt100_zd_gt_7lt_10,  # >100亿 -10%-7%数量
        ">100亿 -10%-7%数量 比例": sz_gt100_zd_gt_7lt_10_ratio,  # >100亿 -10%-7%数量 比例
        ">100亿 -10%%数量": sz_gt100_zd_lt_10,  # >100亿 -10%%数量
        ">100亿 -10%%数量 比例": sz_gt100_zd_lt_10_ratio,  # >100亿 -10%%数量 比例
        "50-100亿 总量": sz_gt50lt100,  # 50-100亿 总量
        "50-100亿 10%数量": sz_gt50lt100_zd_gt10,  # 50-100亿 10%数量
        "50-100亿 10%数量 比例": sz_gt50lt100_zd_gt10_ratio,  # 50-100亿 10%数量 比例
        "50-100亿 7%--3%数量": sz_gt50lt100_zd_lt7gt3,  # 50-100亿 7%--3%数量
        "50-100亿 7%--3%数量 比例": sz_gt50lt100_zd_lt7gt3_ratio,  # 50-100亿 7%--3%数量 比例
        "50-100亿 0%--3%数量": sz_gt50lt100_zd_gt0lt3,  # 50-100亿 0%--3%数量
        "50-100亿 0%--3%数量 比例": sz_gt50lt100_zd_gt0lt3_ratio,  # 50-100亿 0%--3%数量 比例
        "50-100亿 -3%-0%%数量": sz_gt50lt100_zd_gt_3lt0,  # 50-100亿 -3%-0%%数量
        "50-100亿 -3%-0%%数量 比例": sz_gt50lt100_zd_gt_3lt0_ratio,  # 50-100亿 -3%-0%%数量 比例
        "50-100亿 -7%-3%数量": sz_gt50lt100_zd_gt_7lt_3,  # 50-100亿 -7%-3%数量
        "50-100亿 -7%-3%数量 比例": sz_gt50lt100_zd_gt_7lt_3_ratio,  # 50-100亿 -7%-3%数量 比例
        "50-100亿 -10%-7%数量": sz_gt50lt100_zd_gt_7lt_10,  # 50-100亿 -10%-7%数量
        "50-100亿 -10%-7%数量 比例": sz_gt50lt100_zd_gt_7lt_10_ratio,  # 50-100亿 -10%-7%数量 比例
        "50-100亿 -10%%数量": sz_gt50lt100_zd_lt_10,  # 50-100亿 -10%%数量
        "50-100亿 -10%%数量 比例": sz_gt50lt100_zd_lt_10_ratio,  # 50-100亿 -10%%数量 比例
        "<50亿 总量": sz_lt50,  # <50亿 总量
        "<50亿 10%数量": sz_lt50_zd_gt10,  # <50亿 10%数量
        "<50亿 10%数量 比例": sz_lt50_zd_gt10_ratio,  # <50亿 10%数量 比例
        "<50亿 7%--3%数量": sz_lt50_zd_lt7gt3,  # <50亿 7%--3%数量
        "<50亿 7%--3%数量 比例": sz_lt50_zd_lt7gt3_ratio,  # <50亿 7%--3%数量 比例
        "<50亿 0%--3%数量": sz_lt50_zd_gt0lt3,  # <50亿 0%--3%数量
        "<50亿 0%--3%数量 比例": sz_lt50_zd_gt0lt3_ratio,  # <50亿 0%--3%数量 比例
        "<50亿 -3%-0%%数量": sz_lt50_zd_gt_3lt0,  # <50亿 -3%-0%%数量
        "<50亿 -3%-0%%数量 比例": sz_lt50_zd_gt_3lt0_ratio,  # <50亿 -3%-0%%数量 比例
        "<50亿 -7%-3%数量": sz_lt50_zd_gt_7lt_3,  # <50亿 -7%-3%数量
        "<50亿 -7%-3%数量 比例": sz_lt50_zd_gt_7lt_3_ratio,  # <50亿 -7%-3%数量 比例
        "<50亿 -10%-7%数量": sz_lt50_zd_gt_7lt_10,  # <50亿 -10%-7%数量
        "<50亿 -10%-7%数量 比例": sz_lt50_zd_gt_7lt_10_ratio,  # <50亿 -10%-7%数量 比例
        "<50亿 -10%%数量": sz_lt50_zd_lt_10,  # <50亿 -10%%数量
        "<50亿 -10%%数量 比例": sz_lt50_zd_lt_10_ratio,  # <50亿 -10%%数量 比例
        ">100亿 5%数量": sz_gt100_zd_gt5,  # >100亿 5%数量
        ">100亿 5%数量 比例": sz_gt100_zd_gt5_ratio,  # >100亿 5%数量 比例
        "50-100亿 5%数量": sz_gt50lt100_zd_gt5,  # 50-100亿 5%数量
        "50-100亿 5%数量 比例": sz_gt50lt100_zd_gt5_ratio,  # 50-100亿 5%数量 比例
        "<50亿 5%数量": sz_lt50_zd_gt5,  # <50亿 5%数量
        "<50亿 5%数量 比例": sz_lt50_zd_gt5_ratio,  # <50亿 5%数量 比例
        ">10% 数量": zd_gt10,  # >10% 数量
        ">10% 数量 比例": zd_gt10_ratio,  # >10% 数量 比例
        ">5% 数量": zd_gt5,  # >5% 数量
        ">5% 数量 比例": zd_gt5_ratio,  # >5% 数量 比例
        ">3% 数量": zd_gt3,  # >3% 数量
        ">3% 数量 比例": zd_gt3_ratio  # >3% 数量 比例
    }


quotation = easyquotation.use('tencent')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']


# 获取所有股票行情
# all_data = quotation.market_snapshot(prefix=True)  # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀
# print(all_data)

def download_data():
    # 获取当前日期
    current_datetime = datetime.now()

    # 格式化日期为"YYYY-MM-DD"
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    data = market_data()
    data = {key: [value] for key, value in data.items()}
    # 新列的数据
    new_column_data = [formatted_datetime]
    # 新列的名称
    new_column_name = "日期"

    # 在最前面插入新列
    df = pd.DataFrame(data)
    df.insert(0, new_column_name, new_column_data)
    csv_file_path = 'demo.csv'
    df.to_csv(csv_file_path, index=False, mode='a', header=False)
    # df.to_csv(csv_file_path, index=False)
    print('Done')


while True:
    download_data()
    time.sleep(60)
