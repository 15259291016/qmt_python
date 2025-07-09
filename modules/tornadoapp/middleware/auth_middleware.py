import json
from typing import Optional, Dict, Any
from tornado.web import RequestHandler
from modules.tornadoapp.utils.auth import AuthUtils
from modules.tornadoapp.model.user_model import User


def auth_middleware(handler_class):
    """认证中间件装饰器"""
    class AuthMiddlewareHandler(handler_class):
        async def prepare(self):
            """在每个请求处理前调用"""
            # 安全地调用父类的prepare方法
            try:
                parent_prepare = super().prepare
                if parent_prepare is not None:
                    result = parent_prepare()
                    if hasattr(result, '__await__'):
                        await result
            except AttributeError:
                # 父类没有prepare方法，忽略
                pass
            
            # 跳过不需要认证的路径
            if self._should_skip_auth():
                return
            
            auth_header = self.request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return
            
            token = auth_header.split(" ")[1]
            
            # 检查token状态
            token_status = await self._check_token_status(token)
            
            if token_status["action"] == "refresh":
                # 自动刷新token
                new_tokens = await self._refresh_token(token_status["user_id"])
                if new_tokens:
                    # 在响应头中返回新的token
                    self.set_header("X-New-Access-Token", new_tokens["access_token"])
                    self.set_header("X-New-Refresh-Token", new_tokens["refresh_token"])
                    self.set_header("X-Token-Refreshed", "true")
            
            elif token_status["action"] == "expired":
                # token已过期，需要重新登录
                self.set_status(401)
                self.write(json.dumps({
                    "code": 401,
                    "msg": "Token has expired, please login again",
                    "data": {}
                }))
                self.finish()
                return
        
        def _should_skip_auth(self) -> bool:
            """判断是否需要跳过认证"""
            skip_paths = [
                "/api/auth/login",
                "/api/auth/register",
                "/api/auth/refresh",
                "/",
                "/health",
                "/docs"
            ]
            
            for path in skip_paths:
                if self.request.uri.startswith(path):
                    return True
            return False
        
        async def _check_token_status(self, token: str) -> Dict[str, Any]:
            """检查token状态，决定是否需要刷新"""
            token_info = AuthUtils.verify_token_with_expiry(token)
            
            if not token_info["valid"]:
                return {"action": "expired"}
            
            # 如果token还有超过5分钟的有效期，不需要刷新
            if token_info["remaining_seconds"] > 300:
                return {"action": "valid"}
            
            # 如果token还有超过30秒的有效期，可以刷新
            if token_info["remaining_seconds"] > 30:
                payload = token_info["payload"]
                user_id = payload.get("sub")
                if user_id:
                    return {
                        "action": "refresh",
                        "user_id": user_id,
                        "username": payload.get("username"),
                        "is_admin": payload.get("is_admin", False)
                    }
            
            # token即将过期，需要重新登录
            return {"action": "expired"}
        
        async def _refresh_token(self, user_id: str) -> Optional[Dict[str, str]]:
            """刷新token"""
            try:
                user = await User.get(user_id)
                if not user or not user.is_active:
                    return None
                
                # 创建新的token对
                new_tokens = AuthUtils.create_token_pair(
                    str(user.id), 
                    user.username, 
                    user.is_admin
                )
                
                return new_tokens
            except Exception:
                return None
    
    return AuthMiddlewareHandler


class SilentRefreshMixin:
    """无感刷新混入类，可以在处理器中使用"""
    
    async def handle_silent_refresh(self, token: str) -> Optional[Dict[str, str]]:
        """处理无感刷新"""
        token_info = AuthUtils.verify_token_with_expiry(token)
        
        if not token_info["valid"]:
            return None
        
        # 如果token还有超过5分钟的有效期，不需要刷新
        if token_info["remaining_seconds"] > 300:
            return None
        
        # 如果token还有超过30秒的有效期，可以刷新
        if token_info["remaining_seconds"] > 30:
            payload = token_info["payload"]
            user_id = payload.get("sub")
            if user_id:
                user = await User.get(user_id)
                if user and user.is_active:
                    new_tokens = AuthUtils.create_token_pair(
                        str(user.id), 
                        user.username, 
                        user.is_admin
                    )
                    
                    # 在响应头中设置新token
                    if hasattr(self, 'set_header'):
                        self.set_header("X-New-Access-Token", new_tokens["access_token"])
                        self.set_header("X-New-Refresh-Token", new_tokens["refresh_token"])
                        self.set_header("X-Token-Refreshed", "true")
                    
                    return new_tokens
        
        return None
    
    def get_auth_user(self, token: str) -> Optional[Dict[str, Any]]:
        """获取认证用户信息"""
        token_info = AuthUtils.verify_token_with_expiry(token)
        
        if not token_info["valid"]:
            return None
        
        return token_info["payload"] 