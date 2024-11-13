"""
链接：https://baike.baidu.com/item/%E6%A6%82%E7%8E%87%E8%AE%A1%E7%AE%97/90249
"""
import requests

url = 'https://baike.baidu.com/item/%E6%A6%82%E7%8E%87%E8%AE%A1%E7%AE%97/90249'

response = requests.get(url)
print(response.text)