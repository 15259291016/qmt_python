import json
from datetime import datetime, timedelta
from tornado.web import RequestHandler
from modules.tornadoapp.utils.auth import AuthUtils
from modules.tornadoapp.model.user_model import User, UserSession
from modules.tornadoapp.utils.response_model import try_except_async_request, FailedResponse
from modules.tornadoapp.middleware.auth_middleware import SilentRefreshMixin


class RegisterHandler(RequestHandler):
    """用户注册处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        # 验证必填字段
        if not data.get("username") or not data.get("email") or not data.get("password"):
            return FailedResponse(code=400, msg="用户名、邮箱和密码为必填项")
        
        # 检查用户名是否已存在
        existing_user = await User.find_one({"username": data["username"]})
        if existing_user:
            return FailedResponse(code=400, msg="用户名已存在")
        
        # 创建用户
        user = User(
            username=data["username"],
            email=data["email"],
            password_hash=AuthUtils.hash_password(data["password"]),
            full_name=data.get("full_name"),
            last_login=None,  # 新用户没有登录记录
            subscription_expire_at=None  # 新用户没有订阅
        )
        
        await user.insert()
        
        return {"user_id": str(user.id)}


class LoginHandler(RequestHandler):
    """用户登录处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        if not data.get("username") or not data.get("password"):
            return FailedResponse(code=400, msg="用户名和密码为必填项")
        
        # 查找用户
        user = await User.find_one({"username": data["username"]})
        if not user or not AuthUtils.verify_password(data["password"], user.password_hash):
            return FailedResponse(code=401, msg="用户名或密码错误")
        
        # 移除订阅到期校验，允许订阅过期的用户也能登录
        # if not user.subscription_expire_at or user.subscription_expire_at < datetime.utcnow():
        #     return FailedResponse(code=403, msg="订阅已到期，请续费")
        
        # 创建token对
        token_pair = AuthUtils.create_token_pair(str(user.id), user.username, user.is_admin)
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        await user.save()
        
        # 返回前端期望的格式
        return {
            "access_token": token_pair["access_token"],
            "refresh_token": token_pair["refresh_token"],
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "subscription_expire_at": user.subscription_expire_at.isoformat() if user.subscription_expire_at else None,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
        }


class RefreshTokenHandler(RequestHandler):
    """刷新token处理器"""
    
    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body)
        
        if not data.get("refresh_token"):
            return FailedResponse(code=400, msg="刷新令牌为必填项")
        
        # 验证刷新token
        payload = AuthUtils.verify_token(data["refresh_token"])
        if not payload or payload.get("type") != "refresh":
            return FailedResponse(code=401, msg="刷新令牌无效")
        
        # 查找用户
        user = await User.get(payload.get("sub"))
        if not user or not user.is_active:
            return FailedResponse(code=401, msg="用户不存在或已禁用")
        
        # 创建新的token对
        new_token_pair = AuthUtils.create_token_pair(str(user.id), user.username, user.is_admin)
        
        return {
            "access_token": new_token_pair["access_token"],
            "refresh_token": new_token_pair["refresh_token"]
        }


class LogoutHandler(RequestHandler):
    """用户登出处理器"""
    
    @try_except_async_request
    async def post(self):
        auth_header = self.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return FailedResponse(code=400, msg="缺少Authorization头")
        
        token = auth_header.split(" ")[1]
        
        # 查找并停用会话
        session = await UserSession.find_one({
            "token": token,
            "is_active": True
        })
        
        if session:
            session.is_active = False
            await session.save()
        
        return {"msg": "退出登录成功"}


class ProfileHandler(RequestHandler, SilentRefreshMixin):
    """用户资料处理器（支持无感刷新）"""
    
    @try_except_async_request
    async def get(self):
        # 需要认证
        auth_header = self.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return FailedResponse(code=401, msg="未认证，请先登录")
        
        token = auth_header.split(" ")[1]
        
        # 处理无感刷新
        new_tokens = await self.handle_silent_refresh(token)
        
        # 获取用户信息
        user_info = self.get_auth_user(token)
        if not user_info:
            return FailedResponse(code=401, msg="令牌无效")
        
        user = await User.get(user_info.get("sub"))
        if not user:
            return FailedResponse(code=404, msg="用户不存在")
        
        response_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "subscription_expire_at": user.subscription_expire_at.isoformat() if user.subscription_expire_at else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        # 如果token被刷新了，在响应中提示
        if new_tokens:
            response_data["token_refreshed"] = True
            response_data["new_tokens"] = new_tokens
        
        return response_data 