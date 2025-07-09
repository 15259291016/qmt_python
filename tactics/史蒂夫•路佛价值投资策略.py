# import pandas as pd
# import tushare as ts
# import matplotlib.pyplot as plt

# # 设置 Tushare API 密钥
# ts.set_token('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')
# pro = ts.pro_api()

# def get_stock_basic():
#     """
#     获取股票基本信息
#     """
#     df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,area,industry,pe,eps,dv_ratio')
#     return df

# def get_stock_financial_data(ts_code, start_year, end_year):
#     """
#     获取股票财务数据
#     :param ts_code: 股票代码
#     :param start_year: 开始年份
#     :param end_year: 结束年份
#     :return: 财务数据 DataFrame
#     """
#     financial_data = pd.DataFrame()
    
#     for year in range(start_year, end_year + 1):
#         for quarter in [1, 2, 3, 4]:
#             df = pro.stk_list(field='ts_code,name,industry,area,fullname')
#             df_financial = pro.income_vip(ts_code=ts_code, period=f'{year}Q{quarter}', fields='ts_code,total_revenue,operate_profit,total_profit')
            
#             if not df_financial.empty:
#                 df_financial['year'] = year
#                 df_financial['quarter'] = quarter
#                 financial_data = pd.concat([financial_data, df_financial], ignore_index=True)
    
#     return financial_data

# def steve_kovacs_value_strategy(stock_basic_df, min_pe=0, max_pe=15, min_dv_ratio=2):
#     """
#     史蒂夫・柯维价值投资策略筛选股票
#     :param stock_basic_df: 股票基本信息 DataFrame
#     :param min_pe: 最小市盈率
#     :param max_pe: 最大市盈率
#     :param min_dv_ratio: 最小股息率
#     :return: 筛选后的股票列表
#     """
#     # 初步筛选：市盈率低、股息率高
#     filtered_stocks = stock_basic_df[
#         (stock_basic_df['pe'] >= min_pe) &
#         (stock_basic_df['pe'] <= max_pe) &
#         (stock_basic_df['dv_ratio'] >= min_dv_ratio)
#     ]
    
#     # 获取财务数据并进一步筛选
#     for index, row in filtered_stocks.iterrows():
#         ts_code = row['ts_code']
#         try:
#             financial_data = get_stock_financial_data(ts_code, 2018, 2025)
#             # 判断营收和利润增长是否稳定
#             financial_data['revenue_growth'] = financial_data['total_revenue'].pct_change()
#             financial_data['profit_growth'] = financial_data['total_profit'].pct_change()
            
#             # 计算平均增长率
#             avg_revenue_growth = financial_data['revenue_growth'].mean()
#             avg_profit_growth = financial_data['profit_growth'].mean()
            
#             # 筛选营收和利润增长稳定的公司
#             if avg_revenue_growth > 0 and avg_profit_growth > 0:
#                 filtered_stocks.loc[index, 'avg_revenue_growth'] = avg_revenue_growth
#                 filtered_stocks.loc[index, 'avg_profit_growth'] = avg_profit_growth
#             else:
#                 filtered_stocks.drop(index, inplace=True)
#         except Exception as e:
#             print(f"Error processing {ts_code}: {e}")
#             filtered_stocks.drop(index, inplace=True)
    
#     # 按股息率排序，选择前十只股票
#     selected_stocks = filtered_stocks.nlargest(10, 'dv_ratio')
#     return selected_stocks

# def plot_stock_trend(selected_stocks):
#     """
#     绘制股票价格趋势图
#     :param selected_stocks: 选定的股票列表
#     """
#     for stock in selected_stocks.itertuples():
#         ts_code = stock.ts_code
#         name = stock.name
        
#         # 获取历史价格数据
#         df = pro.daily(ts_code=ts_code, start_date='20240101', end_date='20250101')
#         df['trade_date'] = pd.to_datetime(df['trade_date'])
#         df.set_index('trade_date', inplace=True)
        
#         plt.figure(figsize=(12, 6))
#         plt.plot(df.index, df['close'], label=name)
#         plt.title(f"Stock Price Trend - {name}")
#         plt.xlabel("Date")
#         plt.ylabel("Price")
#         plt.legend()
#         plt.show()

# # 主程序
# if __name__ == "__main__":
#     # 获取股票基本信息
#     stock_basic = get_stock_basic()
    
#     # 应用史蒂夫・柯维价值投资策略
#     selected_stocks = steve_kovacs_value_strategy(stock_basic, min_pe=0, max_pe=15, min_dv_ratio=2)
#     print("Selected stocks based on Steve Kovacs' value investing strategy:")
#     print(selected_stocks[['ts_code', 'name', 'pe', 'dv_ratio', 'avg_revenue_growth', 'avg_profit_growth']])
    
#     # 绘制股票价格趋势图
#     plot_stock_trend(selected_stocks)