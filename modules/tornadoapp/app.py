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
from modules.tornadoapp.handler.permission_handler import (
    RoleHandler,
    PermissionHandler,
    UserRoleHandler,
    UserPermissionHandler
)
from modules.tornadoapp.handler.user_handler import (
    UserHandler,
    UserRoleManagementHandler,
    UserStatsHandler
)
from modules.tornadoapp.handler.business_handler import (
    DataHandler,
    SystemHandler,
    UserManagementHandler,
    RoleBasedHandler,
    MixedPermissionHandler
)
from modules.tornadoapp.handler.subscribe_handler import SubscribeHandler
from modules.tornadoapp.middleware.middleware_manager import create_app_with_middlewares
from modules.tornadoapp.handler.super_admin_handler import SuperAdminHandler


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
    (r"/api/user/subscribe", SubscribeHandler),
    
    # 权限管理相关路由
    (r"/api/roles", RoleHandler),
    (r"/api/roles/([^/]+)", RoleHandler),
    (r"/api/permissions", PermissionHandler),
    (r"/api/permissions/([^/]+)", PermissionHandler),
    (r"/api/users/([^/]+)/roles", UserRoleHandler),
    (r"/api/users/([^/]+)/roles/([^/]+)", UserRoleHandler),
    (r"/api/users/([^/]+)/permissions", UserPermissionHandler),
    (r"/api/permissions", UserPermissionHandler),  # 当前用户权限
    
    # 用户管理相关路由
    (r"/api/users", UserHandler),
    (r"/api/users/([^/]+)", UserHandler),
    (r"/api/users/([^/]+)/roles", UserRoleManagementHandler),
    (r"/api/users/([^/]+)/roles/([^/]+)", UserRoleManagementHandler),
    (r"/api/users/stats", UserStatsHandler),
    
    # 超级管理员管理路由
    (r"/api/super-admin", SuperAdminHandler),
    (r"/api/super-admin/([^/]+)", SuperAdminHandler),
    
    # 业务处理器路由 - 展示权限使用
    (r"/api/data", DataHandler),
    (r"/api/data/([^/]+)", DataHandler),
    (r"/api/system", SystemHandler),
    (r"/api/admin", RoleBasedHandler),
    (r"/api/mixed-permissions", MixedPermissionHandler),
]

# 创建带中间件的应用
app = create_app_with_middlewares(
    routes=routes,
    enable_auth=True,  # 启用认证中间件
    enable_cors=True,  # 启用 CORS 中间件
    debug=True  # 开发模式
)
# 
