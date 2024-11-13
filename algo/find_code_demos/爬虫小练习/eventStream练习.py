"""
未完成
"""
import requests
url = 'https://qianwen.biz.aliyun.com/dialog/conversation'
headers = {
    'Accept': 'text/event-stream',
    'Content-Type': 'application/json',
    'Connection': 'keep-alive',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67',
}
response = requests.get(url, stream=True, headers=headers)
print(response.text)
# from sseclient import SSEClient
#
# messages = SSEClient(url)
#
# for msg in messages:
#     print(msg.data)