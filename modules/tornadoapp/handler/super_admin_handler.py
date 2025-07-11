import json
from datetime import datetime
from tornado.web import RequestHandler
from modules.tornadoapp.model.user_model import User
from modules.tornadoapp.utils.permission_decorator import (
    require_permission, PermissionMixin
)
from modules.tornadoapp.utils.response_model import try_except_async_request, FailedResponse


class SuperAdminHandler(RequestHandler, PermissionMixin):
    """超级管理员管理处理器"""
    
    @try_except_async_request
    @require_permission("user:admin")
    async def get(self):
        """获取超级管理员列表"""
        # 只有超级管理员可以查看超级管理员列表
        current_user_id = await self.get_current_user_id()
        current_user = await User.get(current_user_id)
        
        if not current_user:
            return FailedResponse(msg="未认证用户")
        if not current_user.is_super_admin:
            return FailedResponse(msg="只有超级管理员可以查看超级管理员列表")
        
        super_admins = await User.find({"is_super_admin": True}).to_list()
        
        admin_list = []
        for admin in super_admins:
            admin_list.append({
                "id": str(admin.id),
                "username": admin.username,
                "email": admin.email,
                "full_name": admin.full_name,
                "is_active": admin.is_active,
                "is_admin": admin.is_admin,
                "is_super_admin": admin.is_super_admin,
                "created_at": admin.created_at.isoformat(),
                "last_login": admin.last_login.isoformat() if admin.last_login else None
            })
        
        return {
            "code": 200,
            "msg": "获取超级管理员列表成功",
            "data": {"super_admins": admin_list}
        }
    
    @try_except_async_request
    @require_permission("user:admin")
    async def post(self):
        """设置用户为超级管理员"""
        # 只有超级管理员可以设置其他超级管理员
        current_user_id = await self.get_current_user_id()
        current_user = await User.get(current_user_id)
        
        if not current_user:
            return FailedResponse(msg="未认证用户")
        if not current_user.is_super_admin:
            return FailedResponse(msg="只有超级管理员可以设置超级管理员")
        
        data = json.loads(self.request.body)
        user_id = data.get("user_id")
        
        if not user_id:
            return FailedResponse(msg="用户ID为必填项")
        
        user = await User.get(user_id)
        if not user:
            return FailedResponse(msg="用户不存在")
        
        if user.is_super_admin:
            return FailedResponse(msg="用户已经是超级管理员")
        
        # 设置为超级管理员
        user.is_super_admin = True
        user.is_admin = True  # 超级管理员同时也是管理员
        user.updated_at = datetime.utcnow()
        await user.save()
        
        return {
            "code": 200,
            "msg": "设置超级管理员成功",
            "data": {"user_id": str(user.id)}
        }
    
    @try_except_async_request
    @require_permission("user:admin")
    async def delete(self, user_id):
        """取消用户的超级管理员权限"""
        # 只有超级管理员可以取消其他超级管理员权限
        current_user_id = await self.get_current_user_id()
        current_user = await User.get(current_user_id)
        
        if not current_user:
            return FailedResponse(msg="未认证用户")
        if not current_user.is_super_admin:
            return FailedResponse(msg="只有超级管理员可以取消超级管理员权限")
        if current_user_id == user_id:
            return FailedResponse(msg="不能取消自己的超级管理员权限")
        
        user = await User.get(user_id)
        if not user:
            return FailedResponse(msg="用户不存在")
        
        if not user.is_super_admin:
            return FailedResponse(msg="用户不是超级管理员")
        
        # 取消超级管理员权限
        user.is_super_admin = False
        user.updated_at = datetime.utcnow()
        await user.save()
        
        return {
            "code": 200,
            "msg": "取消超级管理员权限成功",
            "data": {"user_id": str(user.id)}
        } 