"""
中间件管理器
提供统一的中间件配置和管理
"""
from typing import List, Tuple, Type, Any
from tornado.web import Application, RequestHandler
from .auth_middleware import auth_middleware


class MiddlewareManager:
    """中间件管理器"""
    
    def __init__(self):
        self.middlewares: List[Tuple[Type, dict]] = []
    
    def add_middleware(self, middleware_decorator, **kwargs):
        """添加中间件"""
        self.middlewares.append((middleware_decorator, kwargs))
    
    def apply_middlewares(self, routes, **kwargs):
        """应用所有中间件到路由"""
        processed_routes = routes
        
        for middleware_decorator, middleware_kwargs in self.middlewares:
            # 对每个路由的处理器应用中间件装饰器
            new_routes = []
            for pattern, handler_class in processed_routes:
                decorated_handler = middleware_decorator(handler_class)
                new_routes.append((pattern, decorated_handler))
            processed_routes = new_routes
        
        return processed_routes


def create_app_with_middlewares(routes, enable_auth=True, **kwargs):
    """
    创建带中间件的应用
    
    Args:
        routes: 路由列表
        enable_auth: 是否启用认证中间件
        **kwargs: 其他应用参数
    
    Returns:
        配置好中间件的应用实例
    """
    # 创建中间件管理器
    manager = MiddlewareManager()
    
    # 添加认证中间件
    if enable_auth:
        manager.add_middleware(auth_middleware)
    
    # 应用中间件到路由
    processed_routes = manager.apply_middlewares(routes)
    
    # 创建应用
    app = Application(processed_routes, **kwargs)
    
    return app 