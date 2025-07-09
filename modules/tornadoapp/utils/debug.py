import functools
import os
import time
from datetime import datetime

import tornado.ioloop
from line_profiler import LineProfiler
from tornado.web import RequestHandler

from modules.tornadoapp.utils.logger import DEBUG, logger

turn_off_handler = None


class DebugHandler(RequestHandler):
    def turn_on_debug(self, expired=60 * 20):
        global turn_off_handler

        os.environ["DEBUG"] = "true"
        DEBUG.is_debug = True
        if turn_off_handler:
            tornado.ioloop.IOLoop.current().remove_timeout(turn_off_handler)
        if expired > 0:
            turn_off_handler = tornado.ioloop.IOLoop.current().add_timeout(time.time() + expired, self.turn_off_debug)
        logger.info("turn on debug: expired: %s", expired)

    def turn_off_debug(self):
        logger.info("turn off debug")
        os.environ["DEBUG"] = "false"
        DEBUG.is_debug = False

    async def get(self):
        self.set_header("Content-Type", "application/json")
        if (log_level := self.get_argument("log_level", "")) in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.setLevel(log_level)

        if (expired := self.get_argument("expired", "-1")) == "-1":
            self.turn_off_debug()
            self.write({"code": 0, "msg": "调试已关闭"})
            return

        self.turn_on_debug(expired=int(expired))
        self.write({"code": 0, "msg": "调试已开启", "expired": int(expired)})


def add_debug_handler(app):
    app.add_handlers(r".*", [("/api/debug", DebugHandler)])


profiler = LineProfiler()
prof_fn = datetime.now().strftime("%Y-%m-%d") + ".lprof"


def line_prof(func):
    """
    启用性能分析:
    根目录执行 python3 -m line_profiler -rmt  xxxx-xx-xx.lprof 即可输出分析
    时间单位: 微秒(us)
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if DEBUG.is_debug:
            profiler.add_function(func)
            curr_func = func
            while True:
                if original_func := getattr(curr_func, "__wrapped__", None):
                    profiler.add_function(original_func)
                    curr_func = original_func
                else:
                    break
            profiler.enable_by_count()
            try:
                return await func(*args, **kwargs)
            finally:
                profiler.disable_by_count()
                # 将分析结果保存到文件
                profiler.dump_stats(prof_fn)
        else:
            return await func(*args, **kwargs)

    return wrapper
