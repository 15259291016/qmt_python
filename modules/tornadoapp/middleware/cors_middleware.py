"""
CORS 中间件
处理跨域请求，解决前端访问后端的跨域问题
"""
import functools
from typing import Type, Callable
from tornado.web import RequestHandler


def cors_middleware(handler_class: Type[RequestHandler]) -> Type[RequestHandler]:
    """
    CORS 中间件装饰器
    
    Args:
        handler_class: 处理器类
    
    Returns:
        装饰后的处理器类
    """
    
    class CORSHandler(handler_class):
        """添加 CORS 支持的处理器"""
        
        def set_default_headers(self):
            """设置默认响应头"""
            super().set_default_headers()
            
            # 允许的源
            origin = self.request.headers.get('Origin', '*')
            self.set_header('Access-Control-Allow-Origin', origin)
            
            # 允许的请求方法
            self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH')
            
            # 允许的请求头
            self.set_header('Access-Control-Allow-Headers', 
                          'Content-Type, Authorization, X-Requested-With, Accept, Origin, X-CSRF-Token')
            
            # 允许发送凭证
            self.set_header('Access-Control-Allow-Credentials', 'true')
            
            # 预检请求缓存时间
            self.set_header('Access-Control-Max-Age', '86400')
        
        def options(self, *args, **kwargs):
            """处理 OPTIONS 预检请求"""
            self.set_status(204)
            self.finish()
    
    return CORSHandler


def enable_cors(handler_class: Type[RequestHandler]) -> Type[RequestHandler]:
    """
    启用 CORS 的装饰器（简化版本）
    
    Args:
        handler_class: 处理器类
    
    Returns:
        装饰后的处理器类
    """
    return cors_middleware(handler_class) 