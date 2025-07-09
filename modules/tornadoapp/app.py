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
from modules.tornadoapp.middleware.middleware_manager import create_app_with_middlewares


# 定义路由
routes = [
    # 主页面
    (r"/", MainHandler),
    
    # 用户认证相关路由
    (r"/api/auth/register", RegisterHandler),
    (r"/api/auth/login", LoginHandler),
    (r"/api/auth/refresh", RefreshTokenHandler),
    (r"/api/auth/logout", LogoutHandler),
    (r"/api/auth/profile", ProfileHandler),
]

# 创建带中间件的应用
app = create_app_with_middlewares(
    routes=routes,
    enable_auth=True,  # 启用认证中间件
    debug=True  # 开发模式
)
# 
