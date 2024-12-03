from DrissionPage import Chromium
import time
import pandas as pd
import os

# 获取并打印当前工作目录
current_directory = os.getcwd()
print("当前工作目录是:", current_directory)
filepath = u'./algo/find_code_demos/tushare项目/data/基础数据/股票列表.csv'
# 读取CSV文件并创建一个DataFrame
df = pd.read_csv(filepath,)
df[(df["market"]=="主板") | (df["market"]=="创业板")]["ts_code"]
# 启动或接管浏览器，并创建标签页对象
tab = Chromium().latest_tab
# 跳转到登录页面
tab.get('https://i.finance.sina.com.cn/zixuan,all')

tab.listen.start('https://stocknews.cj.sina.cn/stocknews/api/news_mult/list')

 # 查找 id 为 dataContainer 的元素
time.sleep(3)
# container = tab.ele('#dataContainer')

data_symbol_list = [i.split(".")[1].lower() + i.split(".")[0] for i in df[(df["market"]=="主板") | (df["market"]=="创业板")]["ts_code"].to_list()]
print(data_symbol_list)
# children = container.children()
# for i in data_symbol_list:  
#     # time.sleep(1)
#     # 获取并打印标签名、文本、href 属性
#     url_name = i.attrs["data-symbol"]
#     data_symbol_list.append(url_name)


for i in range(0, len(data_symbol_list)):
    try:
        print(i)
        if data_symbol_list[i][0:2] == 'sh' or data_symbol_list[i][0:2] == 'sz':
            tab.get(f"https://finance.sina.com.cn/realstock/company/{data_symbol_list[i]}/nc.shtml")
            # 在页面内查找元素
            ele1 = tab.ele('#h5Container')

            # 在元素内查找后代元素
            ele2 = ele1.ele('B/S点')
            ele2.parent().click()
            time.sleep(6)
    except:
        print("error")
        continue
