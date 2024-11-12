from datetime import datetime, timedelta, time
import os
import sys

from starlette.middleware.cors import CORSMiddleware

from algo.app.api.routers import daly_data
from algo.app.main_s import watch_data_history

# 获取当前文件的目录路径并添加到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)
import queue
import socket
import threading
import time as t
import webbrowser
import pywencai as wc
import pandas as pd
import redis
import qstock as qs
# https://zhuanlan.zhihu.com/p/659430613
import efinance as ef
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
import traceback
import easyquotation


quotation = easyquotation.use('tencent')
from bs4 import BeautifulSoup

import uvicorn
from fastapi import FastAPI

import logging

from fastapi.staticfiles import StaticFiles

from api.routers import stock_strategy, users

load_dotenv()
logging.basicConfig(
    level=logging.NOTSET,
    filename='default.log'
)

wc_cookie = 'other_uid=Ths_iwencai_Xuangu_vt1m3hjjud764awfezv3ezly4t2f9xco; ta_random_userid=38r3s4iaao; PHPSESSID=670fb84a8754b3555e226c6b40c1d831; cid=670fb84a8754b3555e226c6b40c1d8311712721082; ComputerID=670fb84a8754b3555e226c6b40c1d8311712721082; WafStatus=0; u_ukey=A10702B8689642C6BE607730E11E6E4A; u_uver=1.0.0; u_dpass=HDZXnLqPSJ%2FMpvbRfnHhizBr0Y9TGLpA9wXLLjwsvQ09AWJ2DoZsyKUcGwEmAARD%2FsBAGfA5tlbuzYBqqcUNFA%3D%3D; u_did=ED35F01A88274FB59C3D3D607D30FEF0; u_ttype=WEB; ttype=WEB; user=MDptb181NjI3MjgwNzU6Ok5vbmU6NTAwOjU3MjcyODA3NTo3LDExMTExMTExMTExLDQwOzQ0LDExLDQwOzYsMSw0MDs1LDEsNDA7MSwxMDEsNDA7MiwxLDQwOzMsMSw0MDs1LDEsNDA7OCwwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMSw0MDsxMDIsMSw0MDoyNDo6OjU2MjcyODA3NToxNzEyNzIxMTIyOjo6MTYxMDkyNDk0MDo0MDAwNzg6MDoxNTljOTE4ODcwNDMzZjVlZDBhYTA5YWUzZWZiMDZhN2M6ZGVmYXVsdF80OjE%3D; userid=562728075; u_name=mo_562728075; escapename=mo_562728075; ticket=c35f5ff9817c2eee41b92f1a856ae0aa; user_status=0; utk=4261b365b2919c25775389e81aabe8e0; v=Az9jBtnQZWCRhWF8zdmzVs3XzhjMJJPPrXiXutEM2-414FHG2fQjFr1IJwbi'

app = FastAPI()
app.mount("/files", StaticFiles(directory="files"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(users.router)
app.include_router(daly_data.router)
app.include_router(stock_strategy.router)
public_obj = {'code_list': [],
              }



host = os.getenv("HOST")
port = int(os.getenv("PORT"))
if __name__ == '__main__':
    message_queue = queue.Queue()
    brain_thread_list = []
    # brain_thread_list.append(threading.Thread(target=brain_analyse_SH, args=()))           # 主力资金
    brain_thread_list.append(threading.Thread(target=watch_data_history, args=()))                 # 监控数据
    # brain_thread_list.append(threading.Thread(target=download_png_csv, args=()))           # 收集数据
    # brain_thread_list.append(threading.Thread(target=wencai_, args=()))             # 问财
    # brain_thread_list.append(threading.Thread(target=myServer, args=("localhost", 8083,)))
    # brain_thread_list.append(threading.Thread(target=myAnalyse, args=(message_queue,)))
    for i in brain_thread_list:
        i.start()
    # 注意：这里的"main:app"意味着uvicorn会从main.py文件中寻找名为app的FastAPI实例
    uvicorn.run("main:app", host=host, port=port, log_level="info", reload=True)            # 启动web服务器 fastapi
