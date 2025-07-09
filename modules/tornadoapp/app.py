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
from modules.tornadoapp.handler.auth_handler import (
    RegisterHandler,
    LoginHandler,
    RefreshTokenHandler,
    LogoutHandler,
    ProfileHandler
)

app = tornado.web.Application([
    # 主页面
    (r"/", MainHandler),
    
    # 用户认证相关路由
    (r"/api/auth/register", RegisterHandler),
    (r"/api/auth/login", LoginHandler),
    (r"/api/auth/refresh", RefreshTokenHandler),
    (r"/api/auth/logout", LogoutHandler),
    (r"/api/auth/profile", ProfileHandler),
])
# 
