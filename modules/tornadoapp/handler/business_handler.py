import json
from tornado.web import RequestHandler
from modules.tornadoapp.utils.permission_decorator import (
    require_permission, require_permissions, require_admin, 
    require_role, require_roles, PermissionMixin
)
from modules.tornadoapp.utils.response_model import try_except_async_request, FailedResponse


class DataHandler(RequestHandler, PermissionMixin):
    """数据管理处理器 - 展示权限使用"""
    
    @try_except_async_request
    @require_permission("data:read")
    async def get(self, data_id=None):
        """获取数据 - 需要data:read权限"""
        if data_id:
            # 获取单个数据
            data = {
                "id": data_id,
                "name": f"数据{data_id}",
                "content": f"这是数据{data_id}的内容",
                "created_by": await self.get_current_user_id()
            }
        else:
            # 获取数据列表
            data = [
                {"id": "1", "name": "数据1", "content": "数据1内容"},
                {"id": "2", "name": "数据2", "content": "数据2内容"},
                {"id": "3", "name": "数据3", "content": "数据3内容"}
            ]
        
        return {
            "code": 200,
            "msg": "数据获取成功",
            "data": data
        }
    
    @try_except_async_request
    @require_permission("data:write")
    async def post(self):
        """创建数据 - 需要data:write权限"""
        data = json.loads(self.request.body)
        
        if not data.get("name"):
            return FailedResponse(msg="数据名称不能为空")
        
        new_data = {
            "id": "new_id",
            "name": data["name"],
            "content": data.get("content", ""),
            "created_by": await self.get_current_user_id(),
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        return {
            "code": 201,
            "msg": "数据创建成功",
            "data": new_data
        }
    
    @try_except_async_request
    @require_permission("data:write")
    async def put(self, data_id):
        """更新数据 - 需要data:write权限"""
        data = json.loads(self.request.body)
        
        updated_data = {
            "id": data_id,
            "name": data.get("name", f"数据{data_id}"),
            "content": data.get("content", ""),
            "updated_by": await self.get_current_user_id(),
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        return {
            "code": 200,
            "msg": "数据更新成功",
            "data": updated_data
        }
    
    @try_except_async_request
    @require_permission("data:delete")
    async def delete(self, data_id):
        """删除数据 - 需要data:delete权限"""
        return {
            "code": 200,
            "msg": f"数据{data_id}删除成功",
            "data": {"deleted_id": data_id}
        }


class SystemHandler(RequestHandler, PermissionMixin):
    """系统管理处理器 - 展示管理员权限"""
    
    @try_except_async_request
    @require_permission("system:read")
    async def get(self):
        """获取系统信息 - 需要system:read权限"""
        system_info = {
            "version": "1.0.0",
            "status": "running",
            "uptime": "24小时",
            "memory_usage": "512MB",
            "cpu_usage": "15%"
        }
        
        return {
            "code": 200,
            "msg": "系统信息获取成功",
            "data": system_info
        }
    
    @try_except_async_request
    @require_admin()
    async def post(self):
        """系统配置 - 需要管理员权限"""
        data = json.loads(self.request.body)
        
        config = {
            "setting": data.get("setting", "default"),
            "value": data.get("value", ""),
            "updated_by": await self.get_current_user_id(),
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        return {
            "code": 200,
            "msg": "系统配置更新成功",
            "data": config
        }


class UserManagementHandler(RequestHandler, PermissionMixin):
    """用户管理处理器 - 展示多权限检查"""
    
    @try_except_async_request
    @require_permissions(["user:read", "user:admin"], require_all=False)
    async def get(self, user_id=None):
        """获取用户信息 - 需要user:read或user:admin权限"""
        if user_id:
            user_info = {
                "id": user_id,
                "username": f"user_{user_id}",
                "email": f"user{user_id}@example.com",
                "status": "active"
            }
        else:
            user_info = [
                {"id": "1", "username": "user1", "email": "user1@example.com", "status": "active"},
                {"id": "2", "username": "user2", "email": "user2@example.com", "status": "inactive"}
            ]
        
        return {
            "code": 200,
            "msg": "用户信息获取成功",
            "data": user_info
        }
    
    @try_except_async_request
    @require_permissions(["user:write", "user:admin"], require_all=True)
    async def post(self):
        """创建用户 - 需要user:write和user:admin权限"""
        data = json.loads(self.request.body)
        
        if not data.get("username") or not data.get("email"):
            return FailedResponse(msg="用户名和邮箱不能为空")
        
        new_user = {
            "id": "new_user_id",
            "username": data["username"],
            "email": data["email"],
            "status": "active",
            "created_by": await self.get_current_user_id()
        }
        
        return {
            "code": 201,
            "msg": "用户创建成功",
            "data": new_user
        }


class RoleBasedHandler(RequestHandler, PermissionMixin):
    """基于角色的处理器 - 展示角色权限"""
    
    @try_except_async_request
    @require_role("admin")
    async def get(self):
        """管理员专用接口 - 需要admin角色"""
        admin_data = {
            "admin_panel": True,
            "system_stats": {
                "total_users": 100,
                "active_sessions": 25,
                "system_load": "normal"
            },
            "admin_actions": ["user_management", "system_config", "data_export"]
        }
        
        return {
            "code": 200,
            "msg": "管理员面板数据获取成功",
            "data": admin_data
        }
    
    @try_except_async_request
    @require_roles(["admin", "user_manager"], require_all=False)
    async def post(self):
        """管理员或用户管理员接口 - 需要admin或user_manager角色"""
        data = json.loads(self.request.body)
        
        action = data.get("action", "unknown")
        result = {
            "action": action,
            "executed_by": await self.get_current_user_id(),
            "status": "success",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return {
            "code": 200,
            "msg": f"操作{action}执行成功",
            "data": result
        }


class MixedPermissionHandler(RequestHandler, PermissionMixin):
    """混合权限处理器 - 展示权限混入类的使用"""
    
    @try_except_async_request
    async def get(self):
        """动态权限检查 - 使用权限混入类"""
        # 获取当前用户权限摘要
        permission_summary = await self.get_user_permission_summary()
        
        if not permission_summary:
            return {"code": 401, "msg": "认证失败", "data": {}}
        
        # 动态检查权限
        can_read_data = await self.check_permission("data:read")
        can_write_data = await self.check_permission("data:write")
        is_admin_user = await self.is_admin()
        
        # 检查多个权限
        permissions_check = await self.check_permissions([
            "user:read", "role:read", "permission:read"
        ])
        
        response_data = {
            "user_info": permission_summary,
            "permissions": {
                "data_read": can_read_data,
                "data_write": can_write_data,
                "is_admin": is_admin_user,
                "detailed_check": permissions_check
            }
        }
        
        return {
            "code": 200,
            "msg": "权限信息获取成功",
            "data": response_data
        }
    
    @try_except_async_request
    async def post(self):
        """条件权限检查"""
        data = json.loads(self.request.body)
        action = data.get("action", "")
        
        # 根据操作类型检查不同权限
        if action == "read_data":
            has_permission = await self.check_permission("data:read")
        elif action == "write_data":
            has_permission = await self.check_permission("data:write")
        elif action == "admin_action":
            has_permission = await self.is_admin()
        else:
            has_permission = False
        
        if not has_permission:
            return FailedResponse(msg=f"没有执行{action}的权限")
        
        return {
            "code": 200,
            "msg": f"操作{action}执行成功",
            "data": {
                "action": action,
                "executed_by": await self.get_current_user_id(),
                "permission_granted": has_permission
            }
        } 