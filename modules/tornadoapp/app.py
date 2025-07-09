# 生成tornado app
import json
import tornado.gen
import tornado.httpclient
import tornado.httpserver
import tornado.httputil
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from datetime import datetime, timedelta

from modules.tornadoapp.handler.mainHandler import MainHandler
from modules.tornadoapp.utils.auth import AuthUtils
from modules.tornadoapp.model.user_model import User, UserSession
from modules.tornadoapp.utils.response_model import try_except_async_request


class RegisterHandler(tornado.web.RequestHandler):
    """用户注册处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        # 验证必填字段
        if not data.get("username") or not data.get("email") or not data.get("password"):
            return {"code": 400, "msg": "Username, email and password are required", "data": {}}
        
        # 检查用户名是否已存在
        existing_user = await User.find_one({"username": data["username"]})
        if existing_user:
            return {"code": 400, "msg": "Username already exists", "data": {}}
        
        # 创建用户
        user = User(
            username=data["username"],
            email=data["email"],
            password_hash=AuthUtils.hash_password(data["password"]),
            full_name=data.get("full_name")
        )
        
        await user.insert()
        
        return {
            "code": 201,
            "msg": "User registered successfully",
            "data": {"user_id": str(user.id)}
        }


class LoginHandler(tornado.web.RequestHandler):
    """用户登录处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        if not data.get("username") or not data.get("password"):
            return {"code": 400, "msg": "Username and password are required", "data": {}}
        
        # 查找用户
        user = await User.find_one({"username": data["username"]})
        if not user or not AuthUtils.verify_password(data["password"], user.password_hash):
            return {"code": 401, "msg": "Invalid username or password", "data": {}}
        
        # 创建token对
        token_pair = AuthUtils.create_token_pair(str(user.id), user.username, user.is_admin)
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        await user.save()
        
        return {
            "code": 200,
            "msg": "Login successful",
            "data": {
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin
                },
                "tokens": token_pair
            }
        }


class RefreshTokenHandler(tornado.web.RequestHandler):
    """刷新token处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        if not data.get("refresh_token"):
            return {"code": 400, "msg": "Refresh token is required", "data": {}}
        
        # 验证刷新token
        payload = AuthUtils.verify_token(data["refresh_token"])
        if not payload or payload.get("type") != "refresh":
            return {"code": 401, "msg": "Invalid refresh token", "data": {}}
        
        # 查找用户
        user = await User.get(payload.get("sub"))
        if not user or not user.is_active:
            return {"code": 401, "msg": "User not found or inactive", "data": {}}
        
        # 创建新的token对
        new_token_pair = AuthUtils.create_token_pair(str(user.id), user.username, user.is_admin)
        
        return {
            "code": 200,
            "msg": "Token refreshed successfully",
            "data": {"tokens": new_token_pair}
        }


app = tornado.web.Application([
    # 主页面
    (r"/", MainHandler),
    
    # 用户认证相关路由
    (r"/api/auth/register", RegisterHandler),
    (r"/api/auth/login", LoginHandler),
    (r"/api/auth/refresh", RefreshTokenHandler),
])
# 
