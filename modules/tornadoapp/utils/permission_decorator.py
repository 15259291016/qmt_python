import functools
from typing import List, Optional, Union, Dict
from tornado.web import RequestHandler
from modules.tornadoapp.utils.auth import AuthUtils
from modules.tornadoapp.utils.permission_utils import PermissionUtils
from modules.tornadoapp.utils.response_model import try_except_async_request


def require_permission(permission: str):
    """要求单个权限的装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: RequestHandler, *args, **kwargs):
            # 获取当前用户ID
            user_id = await get_current_user_id(self)
            if not user_id:
                return {"code": 401, "msg": "Authentication required", "data": {}}
            
            # 检查权限
            has_permission = await PermissionUtils.check_permission(user_id, permission)
            if not has_permission:
                return {"code": 403, "msg": f"Permission denied: {permission}", "data": {}}
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_permissions(permissions: List[str], require_all: bool = True):
    """要求多个权限的装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: RequestHandler, *args, **kwargs):
            # 获取当前用户ID
            user_id = await get_current_user_id(self)
            if not user_id:
                return {"code": 401, "msg": "Authentication required", "data": {}}
            
            # 检查权限
            if require_all:
                has_permissions = await PermissionUtils.has_all_permissions(user_id, permissions)
                if not has_permissions:
                    return {"code": 403, "msg": f"Permission denied: requires all of {permissions}", "data": {}}
            else:
                has_permissions = await PermissionUtils.has_any_permission(user_id, permissions)
                if not has_permissions:
                    return {"code": 403, "msg": f"Permission denied: requires any of {permissions}", "data": {}}
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """要求管理员权限的装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: RequestHandler, *args, **kwargs):
            # 获取当前用户ID
            user_id = await get_current_user_id(self)
            if not user_id:
                return {"code": 401, "msg": "Authentication required", "data": {}}
            
            # 检查管理员权限
            is_admin = await PermissionUtils.is_admin(user_id)
            if not is_admin:
                return {"code": 403, "msg": "Admin permission required", "data": {}}
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """要求特定角色的装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: RequestHandler, *args, **kwargs):
            # 获取当前用户ID
            user_id = await get_current_user_id(self)
            if not user_id:
                return {"code": 401, "msg": "Authentication required", "data": {}}
            
            # 获取用户角色
            roles = await PermissionUtils.get_user_roles(user_id)
            role_names = [role.name for role in roles]
            
            if role_name not in role_names:
                return {"code": 403, "msg": f"Role required: {role_name}", "data": {}}
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_roles(role_names: List[str], require_all: bool = True):
    """要求多个角色的装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: RequestHandler, *args, **kwargs):
            # 获取当前用户ID
            user_id = await get_current_user_id(self)
            if not user_id:
                return {"code": 401, "msg": "Authentication required", "data": {}}
            
            # 获取用户角色
            roles = await PermissionUtils.get_user_roles(user_id)
            user_role_names = [role.name for role in roles]
            
            # 检查角色
            if require_all:
                has_roles = all(role_name in user_role_names for role_name in role_names)
                if not has_roles:
                    return {"code": 403, "msg": f"Roles required: all of {role_names}", "data": {}}
            else:
                has_roles = any(role_name in user_role_names for role_name in role_names)
                if not has_roles:
                    return {"code": 403, "msg": f"Roles required: any of {role_names}", "data": {}}
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


async def get_current_user_id(self: RequestHandler) -> Optional[str]:
    """获取当前用户ID"""
    auth_header = self.request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = AuthUtils.verify_token(token)
    
    if not payload:
        return None
    
    return payload.get("sub")


class PermissionMixin:
    """权限混入类，提供权限检查方法"""
    
    async def get_current_user_id(self) -> Optional[str]:
        """获取当前用户ID"""
        return await get_current_user_id(self)
    
    async def check_permission(self, permission: str) -> bool:
        """检查当前用户是否有指定权限"""
        user_id = await self.get_current_user_id()
        if not user_id:
            return False
        
        return await PermissionUtils.check_permission(user_id, permission)
    
    async def check_permissions(self, permissions: List[str]) -> Dict[str, bool]:
        """检查当前用户是否有指定权限列表"""
        user_id = await self.get_current_user_id()
        if not user_id:
            return {permission: False for permission in permissions}
        
        return await PermissionUtils.check_permissions(user_id, permissions)
    
    async def is_admin(self) -> bool:
        """检查当前用户是否是管理员"""
        user_id = await self.get_current_user_id()
        if not user_id:
            return False
        
        return await PermissionUtils.is_admin(user_id)
    
    async def get_user_permission_summary(self) -> Optional[Dict]:
        """获取当前用户权限摘要"""
        user_id = await self.get_current_user_id()
        if not user_id:
            return None
        
        return await PermissionUtils.get_user_permission_summary(user_id) 