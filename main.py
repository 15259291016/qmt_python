# coding=utf-8
import asyncio
import logging
import threading
import time

import tornado
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import configs.ConfigServer as Cs
from user_strategy import auto_Buy, select_stock, sell
from utils.callback import MyXtQuantTraderCallback
from utils.data import download_all_data
from modules.tornadoapp.app import app
from modules.tornadoapp.db.dbUtil import init_beanie
from modules.tornadoapp.oms.order_manager import OrderManager
from modules.tornadoapp.risk.risk_manager import RiskManager
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
from modules.tornadoapp.audit.audit_logger import AuditLogger

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_config():
    """获取配置信息"""
    try:
        configData = Cs.returnConfigData()
        path = configData["QMT_PATH"][0]
        account = configData["account"][0]
        return path, account
    except Exception as e:
        logger.error(f"配置读取失败: {e}")
        raise


def run_tornado_server():
    """启动Tornado Web 服务"""
    try:
        logger.info("正在启动 Tornado 服务...")
        tornado.ioloop.IOLoop.current().run_sync(init_beanie)
        http_server = tornado.httpserver.HTTPServer(app, max_body_size=1024 * 5)
        http_server.listen(8888)
        logger.info("Tornado 服务启动成功，监听端口: 8888")
        tornado.ioloop.IOLoop.current().start()
    except Exception as e:
        logger.error(f"Tornado 服务启动失败: {e}")
        raise


async def run_trader_system(path, account):
    """动量化交易系统"""
    try:
        logger.info("正在启动量化交易系统...")
        
        # 初始化调度器
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            download_all_data,
            trigger=CronTrigger(day_of_week="0-4", hour=15, minute=40),
            id="morning_analysis",
            replace_existing=True
        )
        scheduler.start()
        logger.info("数据下载调度器启动成功")
        
        # 初始化交易账户
        acc = StockAccount(account, 'STOCK')
        session_id = int(time.time())
        xt_trader = XtQuantTrader(path, session_id)
        xt_trader.start()
        xt_trader.connect()
        
        # 集成风控、合规、审计
        risk_manager = RiskManager()
        compliance_manager = ComplianceManager()
        audit_logger = AuditLogger()
        order_manager = OrderManager(xt_trader, risk_manager, compliance_manager, audit_logger)
        
        # 注册回调
        callback = MyXtQuantTraderCallback(order_manager)
        xt_trader.register_callback(callback)
        
        # 订阅账户
        subscribe_result = xt_trader.subscribe(acc)
        if subscribe_result == -1:
            logger.error("账户订阅失败，请重新打开QMT")
            raise Exception('重新打开qmt')
        
        logger.info("交易账户连接成功")
        
        # 启动策略线程
        thread_list = []
        # thread_list.append(threading.Thread(target=auto_Buy.run_strategy, args=(acc, xt_trader, order_manager)))
        # thread_list.append(threading.Thread(target=select_stock.run_strategy, args=()))
        thread_list.append(threading.Thread(target=sell.run_strategy, args=("000011.SZ", acc, xt_trader, order_manager)))
        
        for thread in thread_list:
            thread.daemon = True
            thread.start()
            logger.info(f"策略线程启动: {thread.name}")
        
        logger.info("量化交易系统启动完成")
        xt_trader.run_forever()
        
    except Exception as e:
        logger.error(f"量化交易系统启动失败: {e}")
        raise
    finally:
        try:
            scheduler.shutdown()
            logger.info("调度器已关闭")
        except Exception as e:
            logger.error(f"调度器关闭失败: {e}")


async def main():
    """主程序入口"""
    try:
        # 获取配置
        path, account = get_config()
        logger.info(f"配置加载成功 - QMT路径: {path}, 账户: {account}")
        
        # 启动量化交易系统（在后台线程中运行）
        trader_task = asyncio.create_task(run_trader_system(path, account))
        
        # 启动 Tornado 服务（在后台线程中运行）
        # tornado_task = asyncio.create_task(
        #     asyncio.to_thread(run_tornado_server)
        # )
        
        # 等待两个服务运行
        # await asyncio.gather(trader_task, tornado_task)
        await asyncio.gather(trader_task)
        
    except Exception as e:
        logger.error(f"主程序运行异常: {e}")
        raise


if __name__ == "__main__":
    try:
        logger.info("程序启动中...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.exception(f"程序异常退出: {e}")
        exit(1)

