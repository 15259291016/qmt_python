"""
中间件管理器
提供统一的中间件配置和管理
"""
from typing import List, Tuple, Type, Any
from tornado.web import Application, RequestHandler
from .auth_middleware import AuthMiddleware


class MiddlewareManager:
    """中间件管理器"""
    
    def __init__(self):
        self.middlewares: List[Tuple[Type, dict]] = []
    
    def add_middleware(self, middleware_class: Type, **kwargs):
        """添加中间件"""
        self.middlewares.append((middleware_class, kwargs))
    
    def apply_middlewares(self, app: Application) -> Application:
        """应用所有中间件到应用"""
        current_app = app
        
        for middleware_class, kwargs in self.middlewares:
            current_app = middleware_class(current_app, **kwargs)
        
        return current_app


def create_app_with_middlewares(routes, enable_auth=True, **kwargs):
    """
    创建带中间件的应用
    
    Args:
        routes: 路由列表
        enable_auth: 是否启用认证中间件
        **kwargs: 其他中间件参数
    
    Returns:
        配置好中间件的应用实例
    """
    # 创建基础应用
    base_app = Application(routes, **kwargs)
    
    # 创建中间件管理器
    manager = MiddlewareManager()
    
    # 添加认证中间件
    if enable_auth:
        manager.add_middleware(AuthMiddleware)
    
    # 应用中间件
    app = manager.apply_middlewares(base_app)
    
    return app 