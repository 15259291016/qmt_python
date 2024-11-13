# 文档地址
# https://akshare.akfamily.xyz/data/stock/stock.html
import akshare as ak
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用于Linux和macOS，也可以是'SimSun'或其他支持中文的字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 或者直接为特定元素设置字体
font = FontProperties(fname=r'path_to_your_font_file.ttf', size=12)  # 替换为你的字体文件路径
# 股票市场总貌

# stock_sse_summary_df = ak.stock_sse_summary()
# print(stock_sse_summary_df)
# # 证券类别统计
# stock_szse_summary_df = ak.stock_szse_summary(date="20240621")
# print(stock_szse_summary_df)
# # 地区交易排序
# stock_szse_area_summary_df = ak.stock_szse_area_summary(date="202405")
# print(stock_szse_area_summary_df)

# 期货展期收益率
# get_roll_yield_bar_df = ak.get_roll_yield_bar(type_method="date", var="RB", start_day="20240518", end_day="20240624")
# print(get_roll_yield_bar_df)
# stock_intraday_em_df = ak.stock_intraday_em(symbol="000001")
# print(stock_intraday_em_df)
# stock_intraday_sina_df = ak.stock_intraday_sina(symbol="sz000001", date="20240321")
# print(stock_intraday_sina_df)

# stock_zh_a_hist_pre_min_em_df = ak.stock_zh_a_hist_pre_min_em(symbol="000001", start_time="09:00:00", end_time="15:40:00")
# print(stock_zh_a_hist_pre_min_em_df)

# stock_zh_a_tick_tx_js_df = ak.stock_zh_a_tick_tx_js(symbol="sz000001")
# print(stock_zh_a_tick_tx_js_df)

# stock_zh_a_st_em_df = ak.stock_zh_a_st_em()
# print(stock_zh_a_st_em_df)
# IPO 受益股
# stock_ipo_benefit_ths_df = ak.stock_ipo_benefit_ths()
# print(stock_ipo_benefit_ths_df)

# 主营业务介绍
# stock_zyjs_ths_df = ak.stock_zyjs_ths(symbol="002338")
# print("主营业务")
# print(stock_zyjs_ths_df)
# 千股千评
# stock_comment_em_df = ak.stock_comment_em()
# print(stock_comment_em_df)
# 资金流向 -- 同花顺
# 个股
# stock_fund_flow_individual_df = ak.stock_fund_flow_individual(symbol="即时")
# print(stock_fund_flow_individual_df)
# # 数据示例-3日、5日、10日和20日
# stock_fund_flow_individual_df = ak.stock_fund_flow_individual(symbol="3日排行")
# print(stock_fund_flow_individual_df)
# # 板块
# stock_fund_flow_concept_df = ak.stock_fund_flow_concept(symbol="即时")
# print(stock_fund_flow_concept_df)
# # 3日排行
# stock_fund_flow_concept_df = ak.stock_fund_flow_concept(symbol="3日排行")
# print(stock_fund_flow_concept_df)
# # industry
# stock_fund_flow_industry_df = ak.stock_fund_flow_industry(symbol="即时")
# print(stock_fund_flow_industry_df)
# stock_fund_flow_industry_df = ak.stock_fund_flow_industry(symbol="3日排行")
# print(stock_fund_flow_industry_df)

# 大单追踪
# stock_fund_flow_big_deal_df = ak.stock_fund_flow_big_deal()
# print(stock_fund_flow_big_deal_df)
# # 个股资金流排名
# stock_individual_fund_flow_rank_df = ak.stock_individual_fund_flow_rank(indicator="今日")
# print(stock_individual_fund_flow_rank_df)
# # 可以有3日,5日10日
# stock_individual_fund_flow_rank_df = ak.stock_individual_fund_flow_rank(indicator="3日")
# print(stock_individual_fund_flow_rank_df)

# 大盘资金流
# stock_market_fund_flow_df = ak.stock_market_fund_flow()
# print(stock_market_fund_flow_df)
# # 行业资金流-今日
# stock_sector_fund_flow_rank_df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
# print(stock_sector_fund_flow_rank_df)
# 东方财富网-数据中心-资金流向-主力净流入排名
# stock_sector_fund_flow_summary_df = ak.stock_sector_fund_flow_summary(symbol="电源设备", indicator="今日")
# print(stock_sector_fund_flow_summary_df)
# 筹码分布
# stock_cyq_em_df = ak.stock_cyq_em(symbol="000001", adjust="")
# print(stock_cyq_em_df)
# 活跃营业部统计
# stock_dzjy_hyyybtj_df = ak.stock_dzjy_hyyybtj(symbol='近3日')
# print(stock_dzjy_hyyybtj_df)
# 标的证券名单及保证金比例查询
# stock_margin_ratio_pa_df = ak.stock_margin_ratio_pa(date="20231013")
# print(stock_margin_ratio_pa_df)
# 股票热度 - 雪球-关注排行榜
# stock_hot_follow_xq_df = ak.stock_hot_follow_xq(symbol="最热门")
# for i, r in stock_hot_follow_xq_df.iterrows():
#     data = ak.stock_cyq_em(symbol=r['股票代码'][2:], adjust="")
#     x = np.array([str(i) for i in data['日期']])
#     y1 = np.array([f'{round(i * 100, 2)}%' for i in data['获利比例']])
#     plt.plot(y1, label='获利比例', color='red')
#     # y2 = np.array([i for i in data['平均成本']])
#     # plt.plot(x, y2, label='平均成本', color='red')
#     # y3 = np.array([i for i in data['90成本-低']])
#     # plt.plot(x, y3, label='90成本-低', color='green')
#     # y4 = np.array([i for i in data['90成本-高']])
#     # plt.plot(x, y4, label='90成本-高', color='green')
#     y5 = np.array([i for i in data['90集中度']])
#     plt.plot(y5, label='90集中度', color='red')
#     # y6 = np.array([i for i in data['70成本-低']])
#     # plt.plot(x, y6, label='70成本-低', color='red')
#     # y7 = np.array([i for i in data['70成本-高']])
#     # plt.plot(x, y7, label='70成本-高', color='blue')
#     y8 = np.array([i for i in data['70集中度']])
#     plt.plot(y8, label='70集中度', color='blue')
#     plt.title(r['股票简称'])
#     # plt.figure()
#     # 添加图例
#     # plt.legend()
#     # 设置标题和坐标轴标签
#     # plt.xlabel('x-axis')
#     # plt.ylabel('y-axis')
#
#     # 显示网格
#     # plt.grid(True)
#
#     # 显示图形
#     plt.show()
#     print('画完了')
# print(stock_hot_follow_xq_df)
# 讨论排行榜
# stock_hot_tweet_xq_df = ak.stock_hot_tweet_xq(symbol="最热门")
# print(stock_hot_tweet_xq_df)
# 交易排行榜
stock_hot_deal_xq_df = ak.stock_hot_deal_xq(symbol="最热门")
print(stock_hot_deal_xq_df.head(50))
# 股票热度 - 问财

# 获取当前日期和时间
now = datetime.now()

# 格式化日期为"YYYYMMDD"
formatted_date = now.strftime("%Y%m%d")

stock_hot_rank_wc_df = ak.stock_hot_rank_wc(date=formatted_date)
# print(stock_hot_rank_wc_df.head(700))
print(stock_hot_rank_wc_df.head(70))
# 股票热度 - 东财
# 人气榜-A股
stock_hot_rank_em_df = ak.stock_hot_rank_em()
print(stock_hot_rank_em_df)
# 飙升榜-A股
stock_hot_up_em_df = ak.stock_hot_up_em()
print(stock_hot_up_em_df)
# 连续上涨
stock_rank_lxsz_ths_df = ak.stock_rank_lxsz_ths()
print(stock_rank_lxsz_ths_df)

# 量价齐升
stock_rank_ljqs_ths_df = ak.stock_rank_ljqs_ths()
print(stock_rank_ljqs_ths_df)

# 持续放量
stock_rank_cxfl_ths_df = ak.stock_rank_cxfl_ths()
print(stock_rank_cxfl_ths_df)
