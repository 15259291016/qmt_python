import time
import pandas as pd
import os
import pywencai as pywc

# 获取并打印当前工作目录
current_directory = os.getcwd()
print("当前工作目录是:", current_directory)
df = pywc.get(query=f"人气个股排名")
print(df)
result_list = pd.DataFrame()
for i in range(0, len(df)+1, 10):
    if f"散户指标:{','.join(df[i:i+10]['股票简称'].to_list())}" != "散户指标:":
        rs = pywc.get(query=f"散户指标:{','.join(df[i:i+10]['股票简称'].to_list())}")
        print(rs)
        rs_df = rs[[o for o in  rs.keys()][0]]
        rs_df["dde散户数量"] = rs_df["dde散户数量"].astype(float)
        result_list = pd.concat([result_list, rs_df[rs_df["dde散户数量"]<0]])

print(result_list)
result_list.sort_values(["dde散户数量"])