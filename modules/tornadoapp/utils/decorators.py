import functools
from typing import Optional
from tornado.web import RequestHandler, HTTPError
from modules.tornadoapp.utils.auth import AuthUtils
from modules.tornadoapp.model.user_model import User, UserSession


def require_auth(admin_only: bool = False):
    """认证装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: RequestHandler, *args, **kwargs):
            # 获取token
            auth_header = self.request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPError(401, "Missing or invalid authorization header")
            
            token = auth_header.split(" ")[1]
            
            # 验证token
            payload = AuthUtils.verify_token(token)
            if not payload:
                raise HTTPError(401, "Invalid or expired token")
            
            # 检查token类型
            if payload.get("type") != "access":
                raise HTTPError(401, "Invalid token type")
            
            # 获取用户信息
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPError(401, "Invalid token payload")
            
            user = await User.get(user_id)
            if not user or not user.is_active:
                raise HTTPError(401, "User not found or inactive")
            
            # 检查管理员权限
            if admin_only and not user.is_admin:
                raise HTTPError(403, "Admin access required")
            
            # 将用户信息添加到请求中
            self.current_user = user
            self.user_id = user_id
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


def optional_auth(func):
    """可选认证装饰器（不强制要求登录）"""
    @functools.wraps(func)
    async def wrapper(self: RequestHandler, *args, **kwargs):
        # 获取token
        auth_header = self.request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = AuthUtils.verify_token(token)
            
            if payload and payload.get("type") == "access":
                user_id = payload.get("sub")
                if user_id:
                    user = await User.get(user_id)
                    if user and user.is_active:
                        self.current_user = user
                        self.user_id = user_id
        
        return await func(self, *args, **kwargs)
    return wrapper 