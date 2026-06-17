import pywencai as wc
data = wc.get(query="最近热点题材，突破十日均线，散户数量小于-100，剔除st，剔除退市警告股")
print(data)