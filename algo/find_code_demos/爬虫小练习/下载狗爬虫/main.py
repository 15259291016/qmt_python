from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any
import requests
import json
import time
import uvicorn
import pywencai as pywc
from queue import Queue
from DrissionPage import ChromiumPage, ChromiumOptions
from threading import Thread
import time

# 创建 FastAPI 应用实例
app = FastAPI()
co = ChromiumOptions().auto_port()  # 指定程序每次使用空闲的端口和临时用户文件夹创建浏览器
co.headless(True)  # 无头模式
co.set_argument('--no-sandbox')  # 无沙盒模式
co.set_argument('--headless=new')  # 无界面系统添加
co.set_paths(browser_path="/usr/bin/google-chrome")  # 设置浏览器路径
page = ChromiumPage(co)
page.get("https://www.xiazaitool.com/dy")
tab1 = page.get_tab()
q = Queue()
res = dict()
tab1('x://html/body/div[1]/nav/div/div/ul[2]/li[1]/a').click('js')  # 简化写法
jym = tab1.ele('#verifyImg', timeout=5).src
jym_str = ""
while jym_str == "":
    jym_str = str(jym).split(" ")[8][5:-1]
    print(jym_str)
    time.sleep(1)
a = input("请输入一个值:")
print(a)

tab1.ele("#account").input("19026045487")
tab1.ele("#password").input("6116988.niu")
tab1.ele("#imgCode").input(a)
tab1.ele("#get_login").click('js')
tab1.wait.doc_loaded()
def consumer(tab1, q):
    while True:
        word_list = q.get()
        count = 0
        tab1.ele("#button-addon2").click('js')          # 清楚输入框
        tab1.ele("#urlInput").input(word_list)          # 输入查询条件
        def pac(tab1):
            tab1.ele("#downloadButton").click('js')         # 点击查询
            tab1.wait.ele_hidden("#waitAnimation")          # 等待查询结果        
            time.sleep(1)    
            # tab1.wait.load_start()  # 等待页面进入加载状态
            # time.sleep(10)
            source = tab1.ele('tag:source')
            images = tab1.eles('.preview-image')
            if source:
                res["a"] = {"videourl": source.attr("src"), "type": "video"}
            if images:
                res["a"] = {"imagesurl": [image.attr("src") for image in images], "type": "image"}
        while "a" not in res and count < 5:
            count += 1
            pac(tab1)
            
        print(res["a"])
        time.sleep(10)


# 创建一个 POST 接口来接收 User 数据
@app.post("/pc")
async def pc(item: Dict[str, Any]):
    info = item.get("user", "")
    if info == "":
        return {"error": "User info is empty!"}
    global q
    q.put(info)
    while True:
        if "a" in res:
            re = res["a"]
            res.pop("a")
            return {
                "data": re
                }
        time.sleep(0.1)


@app.post("/wc")
async def wc(item: Dict[str, Any]):
    stock_name = item['params'].get("stock_name", "")
    res = pywc.get(query=f"{stock_name}散户指标")
    return {
        "data": str(res)
        }

# 运行应用程序的命令
if __name__ == "__main__":
    # 绑定特定的 IP 地址和端口
    Thread(target=consumer, args=(tab1,q)).start()          # chrome浏览器
    uvicorn.run(app, host="0.0.0.0", port=8000)