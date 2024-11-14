from datetime import datetime, timedelta, time
import os
import sys

from starlette.middleware.cors import CORSMiddleware

from main_s import wencai_

# 获取当前文件的目录路径并添加到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from app.api.routers import daly_data
from app.main_s import watch_data_history

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
    # brain_thread_list.append(threading.Thread(target=watch_data_history, args=()))                 # 监控数据
    # brain_thread_list.append(threading.Thread(target=download_png_csv, args=()))           # 收集数据
    brain_thread_list.append(threading.Thread(target=wencai_, args=()))             # 问财
    # brain_thread_list.append(threading.Thread(target=myServer, args=("localhost", 8083,)))
    # brain_thread_list.append(threading.Thread(target=myAnalyse, args=(message_queue,)))
    for i in brain_thread_list:
        i.start()
    # 注意：这里的"main:app"意味着uvicorn会从main.py文件中寻找名为app的FastAPI实例
    uvicorn.run("main:app", host=host, port=port, log_level="info", reload=True)            # 启动web服务器 fastapi
