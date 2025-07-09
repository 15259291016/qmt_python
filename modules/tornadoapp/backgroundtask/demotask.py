# 创建一个定时任务
import tornado.gen
import tornado.ioloop
import tornado.web


class DemoTask(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")