# 生成tornado app
import tornado.gen
import tornado.httpclient
import tornado.httpserver
import tornado.httputil
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket

from modules.tornadoapp.handler.mainHandler import MainHandler

app = tornado.web.Application([
    (r"/", MainHandler),
])
# 
