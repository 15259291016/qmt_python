import datetime
import io
import json
import logging
import os
import socket
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
from typing import Optional

import requests
import yaml
from loguru import logger as loguru_lg
from rich.console import Console
from rich.logging import RichHandler

from modules.tornadoapp.define.enum.log_enum import LogLevel

URL = "http://log-report-sz.zhiyan.tencent-cloud.net:13001/collect"

console = Console() if os.isatty(1) else Console(width=200)


class Debug:
    def __init__(self):
        self._debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    @property
    def is_debug(self) -> bool:
        return self._debug

    @is_debug.setter
    def is_debug(self, value: bool):
        self._debug = value

    def __bool__(self):
        return self._debug


DEBUG = Debug()


def get_logger(name, level, log_path, max_bytes=1024 * 1024 * 10, backup_count=10):
    level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    logger_ = logging.getLogger(name)
    logger_.propagate = False
    logger_.handlers = []
    logger_.setLevel(level)

    rich_handler = RichHandler(console=console, rich_tracebacks=True, tracebacks_show_locals=DEBUG.is_debug)
    rich_handler.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setLevel(level)

    rich_handler.setFormatter(logging.Formatter("[%(name)s]> %(message)s"))
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s|%(levelname)s|%(process)d|%(filename)s:%(lineno)d|%(message)s")
    )

    logger_.addHandler(rich_handler)
    logger_.addHandler(file_handler)

    # 处理 tornado 的 handler
    for log_name in [
        "tornado.access",
        "tornado.application",
        "tornado.general",
        "tornado.websocket",
        "apscheduler",
        "qcloud_cos.cos_client",
        "rainbow",
    ]:
        logging_logger = logging.getLogger(log_name)
        logging_logger.handlers = []
        logging_logger.addHandler(rich_handler)
        logging_logger.propagate = False

    return logger_


def callback(future, level, msg, *args, cnt, **kwargs):
    if not future.result() is True:
        if cnt > 0:
            print(future.result())
            logger.thread_pool.submit(logger._log, LogLevel.ERROR, "callback deal " + str(future.result()))
        else:
            logger._log(level, msg, *args, cnt=cnt + 1, **kwargs)


class Logger(object):
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor()
        # 直接从环境变量读取配置
        self.config = {
            "log_file": os.getenv("LOG_FILE", "logs/app.log"),
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "log_size_limit": int(os.getenv("LOG_SIZE_LIMIT", 1048576)),
        }
        if not os.path.exists(os.path.dirname(self.config["log_file"])):
            os.makedirs(os.path.dirname(self.config["log_file"]))

        level = self.config.get("level")
        self.logger = get_logger("app", level, self.config["log_file"])

        self.console = console
        self._debug = os.getenv("DEBUG", "false").lower() == "true"
        self.IP = ""
        self.FLAG = ""
        self.TOPIC = ""

    def info(self, msg, *args, **kwargs):
        self._log(LogLevel.INFO, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(LogLevel.ERROR, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log(LogLevel.DEBUG, msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._log(LogLevel.WARNING, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(LogLevel.WARNING, msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._log("EXCEPTION", msg, *args, **kwargs)

    @property
    def is_debug(self):
        return self._debug

    @is_debug.setter
    def is_debug(self, value):
        self._debug = value

    def __getattr__(self, name):
        return getattr(self.logger, name)

    def _log(self, level, msg, *args, cnt=0, **kwargs):
        try:
            env = os.getenv("DEPLOY_ENV")
            log_method = getattr(self.logger, level.lower())

            if not isinstance(msg, str) or "%s" not in msg and len(args) > 3:
                other_msg = ""
                for arg in [msg] + list(args):
                    other_msg = other_msg + "|" + str(arg)

                # 在这里限制上传智研的日志大小为 1M,文件中日志大小限制为 2M，方便回溯
                if len(other_msg) > self.config["log_size_limit"] * 2:
                    other_msg = other_msg[: self.config["log_size_limit"] * 2]
                if len(other_msg) > self.config["log_size_limit"]:
                    other_msg = other_msg[: self.config["log_size_limit"] - 1]
                    other_msg += (
                        f"(the large request body was truncated (to length of"
                        f" {self.config['log_size_limit']}) to prevent the bad effect on web service performance)"
                    )

                msg = "{}|{}|{}|{}|{}|{}".format(
                    level,
                    str((datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S.%03d")),
                    self.FLAG or "",
                    self.IP or "",
                    env,
                    other_msg,
                )
                log_method(msg, stacklevel=3)
            else:
                # log_method(msg, *args, stacklevel=3, **kwargs)
                msg = "{}|{}|{}|{}|{}|||||||{}".format(
                    level,
                    str((datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S.%03d")),
                    self.FLAG,
                    self.IP,
                    env,
                    msg,
                )
                msg = (msg % args) if "%s" in msg and len(args) > 0 else msg

            if level == "EXCEPTION":
                if self.is_debug:
                    print(msg)
                rich_capture_string = io.StringIO()
                Console(file=rich_capture_string, width=100).print_exception(show_locals=self.is_debug)
                msg += "\n" + rich_capture_string.getvalue()

            # if self.report and cnt < 1:
            #     self.thread_pool.submit(self.send_zhiyan, msg).add_done_callback(
            #         lambda x: callback(x, level, msg, *args, cnt=cnt, **kwargs)
            #     )

            if level in {LogLevel.ERROR} and env in {"test", "release"}:
                heads = (
                    "\n执行时间 : ",
                    "\nflag : ",
                    "\nip : ",
                    "\n所属环境 : ",
                    "\nTrace_id : ",
                    "\n用户 : ",
                    "\nbehavior : ",
                    "\n所属管线 : ",
                    "\nstatus : ",
                    "\ntimecost : ",
                    "\n",
                )
                for head in heads:
                    message = msg.replace("|", head, 1)
                self.send_notify("错误级别 : " + message, "v_liqzhong")
        except:
            console.print_exception(show_locals=self.is_debug)

    def send_zhiyan(self, message, timeout=3):
        data = {
            "topic": self.TOPIC,
            "host": self.IP,
            "data": [{"timestamp": int(time.time()) * 1000, "message": message}],
        }
        try:
            # resp = requests.post(URL, json=data, timeout=timeout)
            # if resp.status_code != 200:
            #     self.error("send_zhiyan: ", resp.text, cnt=1)
            # ret = resp.json()
            # if ret["code"] == 0:
            #     return True
            # self.error(ret, cnt=1)
            return False
        except:
            self._log("ERROR", "send_zhiyan", cnt=1)
            return False

    def send_notify(self, message, owner):
        # ret = requests.post(
        #     self.NOTIFY_WEBHOOK,
        #     headers={"Content-Type": "application/json"},
        #     data=json.dumps({"msgtype": "text", "text": {"content": message, "mentioned_list": [owner]}}),
        #     timeout=3,
        # )
        # ret = ret.json()
        # if ret["errcode"] != 0:
        #     raise RuntimeError(f"WeixinAPIError: {ret}")
        # return ret["errcode"]
        return 200


if (env_name := os.getenv("DEPLOY_ENV", "").lower()) == "dev_local":
    logger = Logger()
else:
    logger = Logger()


if __name__ == "__main__":
    ## 必备参数
    trace_id = 1  ## 唯一id，可用task_id
    user = "hanlinwu"  ##使用用户
    ## 可选参数
    behavior = "Chat"
    status = "Start"
    timecost = 0
    others = json.dumps({"other_params": "test"})
    logger.info(trace_id, user, behavior, status, timecost, others)
    logger.debug(trace_id, user, behavior, status, timecost, others)
    logger.warn(trace_id, user, behavior, status, timecost, others)
    logger.warning(trace_id, user, behavior, status, timecost, others)
    logger.error(trace_id, user, behavior, status, timecost, others)
    # logger.fatal(trace_id, user, behavior, status, timecost, others)

    try:
        a = 1
        b = 0
        c = a / b
    except:
        logger.exception(trace_id, user, behavior, status, timecost, others)
    time.sleep(0.1)
