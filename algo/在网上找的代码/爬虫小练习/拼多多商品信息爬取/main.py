
# https://mobile.yangkeduo.com/goods.html?goods_id=667048089669&_oak_rcto=YWKn_3Kw0Ac6s_Rf1bWdoq5kVKOqHvCLzLE&_oak_gallery_token=f9130b284b0564a24a9450f30f8d2486&_oak_gallery=https%3A%2F%2Fimg.pddpic.com%2Fgarner-api-new%2Fc419a15a07572c315bb29db9b74dcc8f.png&page_from=401&thumb_url=https%3A%2F%2Fimg.pddpic.com%2Fgarner-api-new%2Fc419a15a07572c315bb29db9b74dcc8f.png%3FimageView2%2F2%2Fw%2F1300%2Fq%2F80&refer_page_name=goods_detail&refer_page_id=10014_1730941806497_5qszz6d81o&refer_page_sn=10014&uin=MDAHW2AIH6FJGGIXLJ7B7WZAX4_GEXDA
import requests
from bs4 import BeautifulSoup
import pandas as pd
url = "https://mobile.yangkeduo.com/goods.html?goods_id=667048089669&_oak_rcto=YWKn_3Kw0Ac6s_Rf1bWdoq5kVKOqHvCLzLE&_oak_gallery_token=f9130b284b0564a24a9450f30f8d2486&_oak_gallery=https%3A%2F%2Fimg.pddpic.com%2Fgarner-api-new%2Fc419a15a07572c315bb29db9b74dcc8f.png&page_from=401&thumb_url=https%3A%2F%2Fimg.pddpic.com%2Fgarner-api-new%2Fc419a15a07572c315bb29db9b74dcc8f.png%3FimageView2%2F2%2Fw%2F1300%2Fq%2F80&refer_page_name=goods_detail&refer_page_id=10014_1730941806497_5qszz6d81o&refer_page_sn=10014&uin=MDAHW2AIH6FJGGIXLJ7B7WZAX4_GEXDA"
url = url.split("&")
url = url[0] + url[1] + url[-1]
# https://mobile.yangkeduo.com/goods.html?goods_id=667048089669&_oak_rcto=YWKn_3Kw0Ac6s_Rf1bWdoq5kVKOqHvCLzLE
# https://mobile.yangkeduo.com/goods.html?goods_id=667048089669&_oak_gallery_token=f9130b284b0564a24a9450f30f8d2486
# 目标商品的URL
# url = 'https://mobile.pinduoduo.com/goods.html?goods_id=667048089669'

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

https://item.pinduoduo.com/658530754329?from=singlemessage&wxref=mp.weixin.qq.com&uin=MDAHW2AIH6FJGGIXLJ7B7WZAX4_GEXDA

# 发送GET请求
response = requests.get(url, headers=headers)

# 解析HTML内容
soup = BeautifulSoup(response.text, 'html.parser')

# 提取商品信息
try:
    title = soup.find('h1', {'class': 'goods-title'}).text.strip()
    price = soup.find('span', {'class': 'goods-price'}).text.strip()
    sales = soup.find('span', {'class': 'goods-sales'}).text.strip()
except AttributeError:
    # 如果找不到相应的元素，输出错误信息
    print("未能找到商品信息")
else:
    # 输出商品信息
    print(f'商品标题：{title}')
    print(f'商品价格：{price}')
    print(f'销量：{sales}')

    # 存储到DataFrame
    data = {'标题': [title], '价格': [price], '销量': [sales]}
    df = pd.DataFrame(data)
    # 保存为CSV文件
    df.to_csv('pdd_goods_info.csv', index=False, encoding='utf-8-sig')
