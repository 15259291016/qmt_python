from DrissionPage import Chromium
import time
# 启动或接管浏览器，并创建标签页对象
tab = Chromium().latest_tab
# 跳转到登录页面
tab.get('https://i.finance.sina.com.cn/zixuan,all')

tab.listen.start('https://stocknews.cj.sina.cn/stocknews/api/news_mult/list')

 # 查找 id 为 dataContainer 的元素
time.sleep(3)
container = tab.ele('#dataContainer')

data_symbol_list = []
children = container.children()
for i in children:  
    # time.sleep(1)
    # 获取并打印标签名、文本、href 属性
    url_name = i.attrs["data-symbol"]
    print(url_name)
    data_symbol_list.append(url_name)


for i in data_symbol_list:
    tab.get(f"https://finance.sina.com.cn/realstock/company/{i}/nc.shtml")
    # 在页面内查找元素
    ele1 = tab.ele('#h5Container')

    # 在元素内查找后代元素
    ele2 = ele1.ele('B/S点')
    ele2.parent().click()
    time.sleep(10)
