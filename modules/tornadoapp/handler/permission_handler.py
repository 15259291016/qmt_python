import json
from datetime import datetime
from tornado.web import RequestHandler
from modules.tornadoapp.model.permission_model import Role, Permission, UserRole, PermissionGroup
from modules.tornadoapp.utils.permission_utils import PermissionUtils
from modules.tornadoapp.utils.permission_decorator import (
    require_permission, require_permissions, require_admin, 
    require_role, PermissionMixin
)
from modules.tornadoapp.utils.response_model import try_except_async_request, FailedResponse


class RoleHandler(RequestHandler, PermissionMixin):
    """角色管理处理器"""
    
    @try_except_async_request
    @require_permission("role:read")
    async def get(self, role_id=None):
        """获取角色列表或单个角色"""
        if role_id:
            # 获取单个角色
            role = await Role.get(role_id)
            if not role:
                return FailedResponse(msg="角色不存在")
            
            return {
                "code": 200,
                "msg": "获取角色成功",
                "data": {
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                    "permissions": role.permissions,
                    "is_active": role.is_active,
                    "is_system": role.is_system,
                    "created_at": role.created_at.isoformat(),
                    "updated_at": role.updated_at.isoformat()
                }
            }
        else:
            # 获取角色列表
            page = int(self.get_argument("page", 1))
            limit = int(self.get_argument("limit", 10))
            skip = (page - 1) * limit
            
            roles = await Role.find({"is_active": True}).skip(skip).limit(limit).to_list()
            total = len(await Role.find({"is_active": True}).to_list())
            
            role_list = []
            for role in roles:
                role_list.append({
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                    "permissions": role.permissions,
                    "is_system": role.is_system,
                    "created_at": role.created_at.isoformat()
                })
            
            return {
                "code": 200,
                "msg": "获取角色列表成功",
                "data": {
                    "roles": role_list,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "pages": (total + limit - 1) // limit
                    }
                }
            }
    
    @try_except_async_request
    @require_permission("role:write")
    async def post(self):
        """创建角色"""
        data = json.loads(self.request.body)
        
        # 验证必填字段
        if not data.get("name"):
            return FailedResponse(msg="角色名称为必填项")
        
        # 检查角色名是否已存在
        existing_role = await Role.find_one({"name": data["name"]})
        if existing_role:
            return FailedResponse(msg="角色名称已存在")
        
        # 创建角色
        current_user_id = await self.get_current_user_id()
        role = Role(
            name=data["name"],
            description=data.get("description"),
            permissions=data.get("permissions", []),
            created_by=current_user_id
        )
        
        await role.insert()
        
        return {
            "code": 201,
            "msg": "角色创建成功",
            "data": {"role_id": str(role.id)}
        }
    
    @try_except_async_request
    @require_permission("role:write")
    async def put(self, role_id):
        """更新角色"""
        role = await Role.get(role_id)
        if not role:
            return FailedResponse(msg="角色不存在")
        
        # 系统角色不允许修改
        if role.is_system:
            return FailedResponse(msg="系统角色不允许修改")
        
        data = json.loads(self.request.body)
        
        # 更新字段
        if "name" in data:
            # 检查新名称是否已被其他角色使用
            existing_role = await Role.find_one({
                "name": data["name"],
                "_id": {"$ne": role.id}
            })
            if existing_role:
                return FailedResponse(msg="角色名称已存在")
            role.name = data["name"]
        
        if "description" in data:
            role.description = data["description"]
        
        if "permissions" in data:
            role.permissions = data["permissions"]
        
        role.updated_at = datetime.utcnow()
        await role.save()
        
        return {
            "code": 200,
            "msg": "角色更新成功",
            "data": {"role_id": str(role.id)}
        }
    
    @try_except_async_request
    @require_permission("role:delete")
    async def delete(self, role_id):
        """删除角色"""
        role = await Role.get(role_id)
        if not role:
            return FailedResponse(msg="角色不存在")
        
        # 系统角色不允许删除
        if role.is_system:
            return FailedResponse(msg="系统角色不允许删除")
        
        # 软删除
        role.is_active = False
        role.updated_at = datetime.utcnow()
        await role.save()
        
        return {
            "code": 200,
            "msg": "角色删除成功",
            "data": {}
        }


class PermissionHandler(RequestHandler, PermissionMixin):
    """权限管理处理器"""
    
    @try_except_async_request
    @require_permission("permission:read")
    async def get(self, permission_id=None):
        """获取权限列表或单个权限"""
        if permission_id:
            # 获取单个权限
            permission = await Permission.get(permission_id)
            if not permission:
                return FailedResponse(msg="权限不存在")
            
            return {
                    "id": str(permission.id),
                    "name": permission.name,
                    "resource": permission.resource,
                    "action": permission.action,
                    "description": permission.description,
                    "is_active": permission.is_active,
                    "created_at": permission.created_at.isoformat()
                }
        else:
            # 获取权限列表
            page = int(self.get_argument("page", 1))
            limit = int(self.get_argument("limit", 10))
            skip = (page - 1) * limit
            
            permissions = await Permission.find({"is_active": True}).skip(skip).limit(limit).to_list()
            total = len(await Permission.find({"is_active": True}).to_list())
            
            permission_list = []
            for permission in permissions:
                permission_list.append({
                    "id": str(permission.id),
                    "name": permission.name,
                    "resource": permission.resource,
                    "action": permission.action,
                    "description": permission.description,
                    "created_at": permission.created_at.isoformat()
                })
            
            return {
                    "permissions": permission_list,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "pages": (total + limit - 1) // limit
                    }
                }
    
    @try_except_async_request
    @require_permission("permission:write")
    async def post(self):
        """创建权限"""
        data = json.loads(self.request.body)
        
        # 验证必填字段
        if not data.get("name") or not data.get("resource") or not data.get("action"):
            return FailedResponse(msg="权限名称、资源和操作为必填项")
        
        # 检查权限名是否已存在
        existing_permission = await Permission.find_one({"name": data["name"]})
        if existing_permission:
            return FailedResponse(msg="权限名称已存在")
        
        # 创建权限
        permission = Permission(
            name=data["name"],
            resource=data["resource"],
            action=data["action"],
            description=data.get("description")
        )
        
        await permission.insert()
        
        return {
            "code": 201,
            "msg": "权限创建成功",
            "data": {"permission_id": str(permission.id)}
        }
    
    @try_except_async_request
    @require_permission("permission:delete")
    async def delete(self, permission_id):
        """删除权限"""
        permission = await Permission.get(permission_id)
        if not permission:
            return FailedResponse(msg="权限不存在")
        
        # 检查是否有角色在使用此权限
        roles_using_permission = await Role.find({
            "permissions": permission_id,
            "is_active": True
        }).to_list()
        
        if roles_using_permission:
            role_names = [role.name for role in roles_using_permission]
            return {
                "code": 400, 
                "msg": f"权限正在被以下角色使用，无法删除：{', '.join(role_names)}", 
                "data": {}
            }
        
        # 软删除
        permission.is_active = False
        permission.updated_at = datetime.utcnow()
        await permission.save()
        
        return {
            "code": 200,
            "msg": "权限删除成功",
            "data": {}
        }


class UserRoleHandler(RequestHandler, PermissionMixin):
    """用户角色管理处理器"""
    
    @try_except_async_request
    @require_permission("user:read")
    async def get(self, user_id):
        """获取用户的角色列表"""
        roles = await PermissionUtils.get_user_roles(user_id)
        
        role_list = []
        for role in roles:
            role_list.append({
                "id": str(role.id),
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions,
                "is_system": role.is_system
            })
        
        return {
            "code": 200,
            "msg": "获取用户角色成功",
            "data": {"roles": role_list}
        }
    
    @try_except_async_request
    @require_permission("user:write")
    async def post(self, user_id):
        """为用户分配角色"""
        data = json.loads(self.request.body)
        
        if not data.get("role_id"):
            return FailedResponse(msg="角色ID为必填项")
        
        current_user_id = await self.get_current_user_id()
        expires_at = None
        
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        success = await PermissionUtils.assign_role_to_user(
            user_id, 
            data["role_id"], 
            current_user_id,
            expires_at
        )
        
        if success:
            return {
                "code": 200,
                "msg": "角色分配成功",
                "data": {}
            }
        else:
            return FailedResponse(msg="分配角色失败")
    
    @try_except_async_request
    @require_permission("user:write")
    async def delete(self, user_id, role_id):
        """移除用户的角色"""
        success = await PermissionUtils.remove_role_from_user(user_id, role_id)
        
        if success:
            return {
                "code": 200,
                "msg": "角色移除成功",
                "data": {}
            }
        else:
            return FailedResponse(msg="移除角色失败")


class UserPermissionHandler(RequestHandler, PermissionMixin):
    """用户权限管理处理器"""
    
    @try_except_async_request
    @require_permission("user:read")
    async def get(self, user_id=None):
        """获取用户权限信息"""
        if user_id:
            # 获取指定用户的权限
            summary = await PermissionUtils.get_user_permission_summary(user_id)
            if not summary:
                return FailedResponse(msg="用户不存在")
        else:
            # 获取当前用户的权限
            summary = await self.get_user_permission_summary()
            if not summary:
                return FailedResponse(msg="未认证，请先登录")
        
        return {
            "code": 200,
            "msg": "获取用户权限成功",
            "data": summary
        }
    
    @try_except_async_request
    @require_permission("user:read")
    async def post(self, user_id):
        """检查用户是否有指定权限"""
        data = json.loads(self.request.body)
        
        if not data.get("permissions"):
            return FailedResponse(msg="权限列表为必填项")
        
        permissions = data["permissions"]
        if isinstance(permissions, str):
            permissions = [permissions]
        
        result = await PermissionUtils.check_permissions(user_id, permissions)
        
        return {
            "code": 200,
            "msg": "权限检查完成",
            "data": {"permissions": result}
        } 