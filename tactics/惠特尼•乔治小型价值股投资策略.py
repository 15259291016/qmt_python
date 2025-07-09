# import pandas as pd

# def calculate_value_factor(pe_ratio, pb_ratio):
#     """
#     计算价值因子
#     参数：
#         pe_ratio (float): 市盈率（PE）
#         pb_ratio (float): 市净率（PB）
#     返回：
#         float: 价值因子
#     """
#     # 对市盈率和市净率进行标准化处理
#     normalized_pe = 1 / pe_ratio if pe_ratio != 0 else 0
#     normalized_pb = 1 / pb_ratio if pb_ratio != 0 else 0
#     return (normalized_pe + normalized_pb) / 2

# def screen_small_cap_value_stocks(data_file, market_cap_threshold=200, value_factor_threshold=0.3):
#     """
#     筛选小型价值股
#     参数：
#         data_file (str): 数据文件路径
#         market_cap_threshold (float): 市值阈值（亿元）
#         value_factor_threshold (float): 价值因子阈值
#     返回：
#         DataFrame: 符合条件的股票
#     """
#     # 读取数据
#     df = pd.read_csv(data_file)
    
#     # 计算价值因子
#     df['价值因子'] = df.apply(lambda row: calculate_value_factor(row['市盈率（PE）'], row['市净率（PB）']), axis=1)
    
#     # 筛选小型价值股
#     # 市值小于阈值，且价值因子大于行业前30%
#     filtered_df = df[
#         (df['市值（亿元）'] < market_cap_threshold) &
#         (df['价值因子'] > df['价值因子'].quantile(1 - value_factor_threshold))  # 前30%价值因子
#     ]
    
#     return filtered_df

# # 调用示例
# filtered_stocks = screen_small_cap_value_stocks('algo/tactics/000001.csv', market_cap_threshold=200, value_factor_threshold=0.3)
# print("符合筛选条件的股票：")
# print(filtered_stocks[['股票代码', '股票名称', '市值（亿元）', '市盈率（PE）', '市净率（PB）', '价值因子']])