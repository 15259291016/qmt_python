import logging
import logging
import os
import uvicorn
import logging
import nest_asyncio

from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.api.routers import daly_data, stock_strategy, users
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from app.api.routers.tasks import morning_analysis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
import sys
import threading

nest_asyncio.apply()
load_dotenv()
logging.basicConfig(
    level=logging.NOTSET,
    filename='default.log'
)
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化调度器"""
    # 添加定时任务
    scheduler.start()
    print("调度器已启动")
    # 添加定时任务
    scheduler.add_job(
        morning_analysis,
        trigger=CronTrigger(day_of_week="0-4", hour=9,minute=26),
        id="morning_analysis",
        replace_existing=True
    )
    # morning_analysis()
    
    # scheduler.add_job(
    #     morning_analysis,
    #     morning_analysis,
    #     trigger=CronTrigger(day_of_week="0-4",minute="*",timezone="Asia/Shanghai"),
    #     id="morning_analysis",
    #     replace_existing=True
    # )
    print("定时任务已启动")
    yield
    """关闭时停止调度器"""
    scheduler.shutdown()
    print("定时任务已关闭")

app = FastAPI(docs_url=None,lifespan=lifespan)  # 禁用默认的 /docs 路由
app.mount("/static", StaticFiles(directory="algo/static"), name="static")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css"
    )
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

def start_fastapi():
    host = os.getenv("HOST")
    port = int(os.getenv("PORT"))
    uvicorn.run("fastapiapp:app", host=host, port=port, log_level="info")            # 启动web服务器 fastapi
