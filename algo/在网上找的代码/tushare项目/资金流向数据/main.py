import tushare as ts
from sqlalchemy import create_engine
import time

# 初始化pro接口
pro = ts.pro_api('7c0f63e6190327ab6c42d10e24abbab4863d721abc5f76b67a06a020')
# 创建数据库连接
engine = create_engine('postgresql://postgres:611698@localhost:5432/data')
# 个股资金流向
# 拉取数据
# df = pro.moneyflow(**{
#     "ts_code": "",
#     "trade_date": "",
#     "start_date": "",
#     "end_date": "",
#     "limit": "",
#     "offset": ""
# })
# df.to_sql('个股资金流向', engine, if_exists='replace', index=False)


# 定义 SQL 查询语句
# query = "SELECT * FROM 个股资金流向"
#
# # 执行查询并将结果读取到 DataFrame
# df = pd.read_sql_query(query, engine)
#
# # 打印查询结果
# print(df)

# 个股资金流向(THS)
# 拉取数据
# df = pro.moneyflow_ths(**{
#     "ts_code": "",
#     "trade_date": "",
#     "start_date": "",
#     "end_date": "",
#     "limit": "",
#     "offset": ""
# })
# print(df)
# df.to_sql('个股资金流向(THS)', engine, if_exists='replace', index=False)
# 定义 SQL 查询语句
# query = "SELECT * FROM 个股资金流向(THS)"
#
# # 执行查询并将结果读取到 DataFrame
# df = pd.read_sql_query(query, engine)
#
# # 打印查询结果
# print(df)
# 个股资金流向(DC)
# 拉取数据
# df = pro.moneyflow_dc(**{
#     "ts_code": "",
#     "trade_date": "",
#     "start_date": "",
#     "end_date": "",
#     "limit": "",
#     "offset": ""
# })
# print(df)
# df.to_sql('个股资金流向(DC)', engine, if_exists='replace', index=False)
# 定义 SQL 查询语句
# query = "SELECT * FROM 个股资金流向(DC)"
#
# # 执行查询并将结果读取到 DataFrame
# df = pd.read_sql_query(query, engine)
#
# # 打印查询结果
# print(df)
# 行业资金流向(THS)
# 拉取数据
df = pro.moneyflow_ind_ths(**{
    "ts_code": "",
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
})
print(df)
df.to_sql('行业资金流向(THS)', engine, if_exists='replace', index=False)
# 定义 SQL 查询语句
# query = "SELECT * FROM 行业资金流向(THS)"
#
# # 执行查询并将结果读取到 DataFrame
# df = pd.read_sql_query(query, engine)
#
# # 打印查询结果
# print(df)
# 板块资金流向(DC)
# 拉取数据
df = pro.moneyflow_ind_dc(**{
    "ts_code": "",
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
})
print(df)
df.to_sql('板块资金流向(DC)', engine, if_exists='replace', index=False)
# 定义 SQL 查询语句
# query = "SELECT * FROM 行业资金流向(THS)"
#
# # 执行查询并将结果读取到 DataFrame
# df = pd.read_sql_query(query, engine)
#
# # 打印查询结果
# print(df)
# 大盘资金流向(DC)
# 拉取数据
df = pro.moneyflow_mkt_dc(**{
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
})
print(df)
df.to_sql('板块资金流向(DC)', engine, if_exists='replace', index=False)
# 定义 SQL 查询语句
# query = "SELECT * FROM 板块资金流向(DC)"
#
# # 执行查询并将结果读取到 DataFrame
# df = pd.read_sql_query(query, engine)
#
# # 打印查询结果
# print(df)
# 沪深港通资金流向
# 拉取数据
df = pro.moneyflow_hsgt(**{
    "trade_date": "",
    "start_date": "",
    "end_date": "",
    "limit": "",
    "offset": ""
})
print(df)
df.to_sql('沪深港通资金流向', engine, if_exists='replace', index=False)
# 定义 SQL 查询语句
# query = "SELECT * FROM 沪深港通资金流向"
#
# # 执行查询并将结果读取到 DataFrame
# df = pd.read_sql_query(query, engine)
#
# # 打印查询结果
# print(df)


