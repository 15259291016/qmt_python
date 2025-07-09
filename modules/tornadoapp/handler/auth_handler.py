import json
from datetime import datetime, timedelta
from tornado.web import RequestHandler
from modules.tornadoapp.utils.auth import AuthUtils
from modules.tornadoapp.model.user_model import User, UserSession
from modules.tornadoapp.utils.response_model import try_except_async_request
from modules.tornadoapp.middleware.auth_middleware import SilentRefreshMixin


class RegisterHandler(RequestHandler):
    """用户注册处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        # 验证必填字段
        if not data.get("username") or not data.get("email") or not data.get("password"):
            return {"code": 400, "msg": "用户名、邮箱和密码为必填项", "data": {}}
        
        # 检查用户名是否已存在
        existing_user = await User.find_one({"username": data["username"]})
        if existing_user:
            return {"code": 400, "msg": "用户名已存在", "data": {}}
        
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
            "msg": "用户注册成功",
            "data": {"user_id": str(user.id)}
        }


class LoginHandler(RequestHandler):
    """用户登录处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        if not data.get("username") or not data.get("password"):
            return {"code": 400, "msg": "用户名和密码为必填项", "data": {}}
        
        # 查找用户
        user = await User.find_one({"username": data["username"]})
        if not user or not AuthUtils.verify_password(data["password"], user.password_hash):
            return {"code": 401, "msg": "用户名或密码错误", "data": {}}
        
        # 创建token对
        token_pair = AuthUtils.create_token_pair(str(user.id), user.username, user.is_admin)
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        await user.save()
        
        return {
            "code": 200,
            "msg": "登录成功",
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


class RefreshTokenHandler(RequestHandler):
    """刷新token处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        if not data.get("refresh_token"):
            return {"code": 400, "msg": "刷新令牌为必填项", "data": {}}
        
        # 验证刷新token
        payload = AuthUtils.verify_token(data["refresh_token"])
        if not payload or payload.get("type") != "refresh":
            return {"code": 401, "msg": "刷新令牌无效", "data": {}}
        
        # 查找用户
        user = await User.get(payload.get("sub"))
        if not user or not user.is_active:
            return {"code": 401, "msg": "用户不存在或已禁用", "data": {}}
        
        # 创建新的token对
        new_token_pair = AuthUtils.create_token_pair(str(user.id), user.username, user.is_admin)
        
        return {
            "code": 200,
            "msg": "令牌刷新成功",
            "data": {"tokens": new_token_pair}
        }


class LogoutHandler(RequestHandler):
    """用户登出处理器"""
    
    @try_except_async_request
    async def post(self):
        auth_header = self.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"code": 400, "msg": "缺少Authorization头", "data": {}}
        
        token = auth_header.split(" ")[1]
        
        # 查找并停用会话
        session = await UserSession.find_one({
            "token": token,
            "is_active": True
        })
        
        if session:
            session.is_active = False
            await session.save()
        
        return {
            "code": 200,
            "msg": "退出登录成功",
            "data": {}
        }


class ProfileHandler(RequestHandler, SilentRefreshMixin):
    """用户资料处理器（支持无感刷新）"""
    
    @try_except_async_request
    async def get(self):
        # 需要认证
        auth_header = self.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"code": 401, "msg": "未认证，请先登录", "data": {}}
        
        token = auth_header.split(" ")[1]
        
        # 处理无感刷新
        new_tokens = await self.handle_silent_refresh(token)
        
        # 获取用户信息
        user_info = self.get_auth_user(token)
        if not user_info:
            return {"code": 401, "msg": "令牌无效", "data": {}}
        
        user = await User.get(user_info.get("sub"))
        if not user:
            return {"code": 404, "msg": "用户不存在", "data": {}}
        
        response_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        # 如果token被刷新了，在响应中提示
        if new_tokens:
            response_data["token_refreshed"] = True
            response_data["new_tokens"] = new_tokens
        
        return {
            "code": 200,
            "msg": "获取用户信息成功",
            "data": response_data
        }
    
    @try_except_async_request
    async def put(self):
        # 需要认证
        auth_header = self.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"code": 401, "msg": "未认证，请先登录", "data": {}}
        
        token = auth_header.split(" ")[1]
        
        # 处理无感刷新
        new_tokens = await self.handle_silent_refresh(token)
        
        # 获取用户信息
        user_info = self.get_auth_user(token)
        if not user_info:
            return {"code": 401, "msg": "令牌无效", "data": {}}
        
        user = await User.get(user_info.get("sub"))
        if not user:
            return {"code": 404, "msg": "用户不存在", "data": {}}
        
        data = json.loads(self.request.body)
        
        # 更新允许的字段
        if "full_name" in data:
            user.full_name = data["full_name"]
        
        if "email" in data:
            # 检查邮箱是否已被其他用户使用
            existing_email = await User.find_one({
                "email": data["email"],
                "_id": {"$ne": user.id}
            })
            if existing_email:
                return {"code": 400, "msg": "邮箱已存在", "data": {}}
            user.email = data["email"]
        
        user.updated_at = datetime.utcnow()
        await user.save()
        
        response_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin
        }
        
        # 如果token被刷新了，在响应中提示
        if new_tokens:
            response_data["token_refreshed"] = True
            response_data["new_tokens"] = new_tokens
        
        return {
            "code": 200,
            "msg": "用户信息更新成功",
            "data": response_data
        } 