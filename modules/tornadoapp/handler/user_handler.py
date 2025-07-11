import json
from datetime import datetime
from tornado.web import RequestHandler
from modules.tornadoapp.model.user_model import User
from modules.tornadoapp.model.permission_model import Role, Permission, UserRole
from modules.tornadoapp.utils.auth import AuthUtils
from modules.tornadoapp.utils.permission_decorator import (
    require_permission, require_permissions, require_admin, 
    require_role, PermissionMixin
)
from modules.tornadoapp.utils.response_model import try_except_async_request


class UserHandler(RequestHandler, PermissionMixin):
    """用户管理处理器"""
    
    @try_except_async_request
    @require_permission("user:read")
    async def get(self, user_id=None):
        """获取用户列表或单个用户"""
        if user_id:
            # 获取单个用户
            user = await User.get(user_id)
            if not user:
                return {"code": 404, "msg": "用户不存在", "data": {}}
            
            return {
                "code": 200,
                "msg": "获取用户成功",
                "data": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "subscription_expire_at": user.subscription_expire_at.isoformat() if user.subscription_expire_at else None
                }
            }
        else:
            # 获取用户列表
            page = int(self.get_argument("page", 1))
            limit = int(self.get_argument("limit", 10))
            search = self.get_argument("search", "")
            skip = (page - 1) * limit
            
            # 构建查询条件
            query = {"is_active": True}
            if search:
                query["$or"] = [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"full_name": {"$regex": search, "$options": "i"}}
                ]
            
            users = await User.find(query).skip(skip).limit(limit).to_list()
            total = await User.count_documents(query)
            
            user_list = []
            for user in users:
                user_list.append({
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "subscription_expire_at": user.subscription_expire_at.isoformat() if user.subscription_expire_at else None
                })
            
            return {
                "code": 200,
                "msg": "获取用户列表成功",
                "data": user_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
    
    @try_except_async_request
    @require_permission("user:write")
    async def post(self):
        """创建用户"""
        data = json.loads(self.request.body)
        
        # 验证必填字段
        if not data.get("username") or not data.get("email") or not data.get("password"):
            return {"code": 400, "msg": "用户名、邮箱和密码为必填项", "data": {}}
        
        # 检查用户名是否已存在
        existing_user = await User.find_one({"username": data["username"]})
        if existing_user:
            return {"code": 400, "msg": "用户名已存在", "data": {}}
        
        # 检查邮箱是否已存在
        existing_email = await User.find_one({"email": data["email"]})
        if existing_email:
            return {"code": 400, "msg": "邮箱已存在", "data": {}}
        
        # 创建用户
        user = User(
            username=data["username"],
            email=data["email"],
            password_hash=AuthUtils.hash_password(data["password"]),
            full_name=data.get("full_name"),
            is_active=data.get("is_active", True),
            is_admin=data.get("is_admin", False)
        )
        
        await user.insert()
        
        return {
            "code": 201,
            "msg": "用户创建成功",
            "data": {"user_id": str(user.id)}
        }
    
    @try_except_async_request
    @require_permission("user:write")
    async def put(self, user_id):
        """更新用户"""
        user = await User.get(user_id)
        if not user:
            return {"code": 404, "msg": "用户不存在", "data": {}}
        
        data = json.loads(self.request.body)
        
        # 更新字段
        if "email" in data and data["email"] != user.email:
            # 检查新邮箱是否已被其他用户使用
            existing_email = await User.find_one({
                "email": data["email"],
                "_id": {"$ne": user.id}
            })
            if existing_email:
                return {"code": 400, "msg": "邮箱已存在", "data": {}}
            user.email = data["email"]
        
        if "full_name" in data:
            user.full_name = data["full_name"]
        
        if "is_active" in data:
            user.is_active = data["is_active"]
        
        if "is_admin" in data:
            user.is_admin = data["is_admin"]
        
        user.updated_at = datetime.utcnow()
        await user.save()
        
        return {
            "code": 200,
            "msg": "用户更新成功",
            "data": {"user_id": str(user.id)}
        }
    
    @try_except_async_request
    @require_permission("user:delete")
    async def delete(self, user_id):
        """删除用户"""
        user = await User.get(user_id)
        if not user:
            return {"code": 404, "msg": "用户不存在", "data": {}}
        
        # 软删除
        user.is_active = False
        user.updated_at = datetime.utcnow()
        await user.save()
        
        return {
            "code": 200,
            "msg": "用户删除成功",
            "data": {}
        }


class UserRoleManagementHandler(RequestHandler, PermissionMixin):
    """用户角色管理处理器"""
    
    @try_except_async_request
    @require_permission("user:read")
    async def get(self, user_id):
        """获取用户的角色列表"""
        # 检查用户是否存在
        user = await User.get(user_id)
        if not user:
            return {"code": 404, "msg": "用户不存在", "data": {}}
        
        # 获取用户角色
        user_roles = await UserRole.find({"user_id": user_id, "is_active": True}).to_list()
        
        role_list = []
        for user_role in user_roles:
            role = await Role.get(user_role.role_id)
            if role and role.is_active:
                role_list.append({
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                    "permissions": role.permissions,
                    "is_system": role.is_system,
                    "assigned_at": user_role.created_at.isoformat(),
                    "expires_at": user_role.expires_at.isoformat() if user_role.expires_at else None
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
        # 检查用户是否存在
        user = await User.get(user_id)
        if not user:
            return {"code": 404, "msg": "用户不存在", "data": {}}
        
        data = json.loads(self.request.body)
        
        if not data.get("role_id"):
            return {"code": 400, "msg": "角色ID为必填项", "data": {}}
        
        # 检查角色是否存在
        role = await Role.get(data["role_id"])
        if not role or not role.is_active:
            return {"code": 400, "msg": "角色不存在或已禁用", "data": {}}
        
        # 检查是否已经分配了该角色
        existing_role = await UserRole.find_one({
            "user_id": user_id,
            "role_id": data["role_id"],
            "is_active": True
        })
        if existing_role:
            return {"code": 400, "msg": "用户已拥有该角色", "data": {}}
        
        # 分配角色
        current_user_id = await self.get_current_user_id()
        expires_at = None
        
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        user_role = UserRole(
            user_id=user_id,
            role_id=data["role_id"],
            assigned_by=current_user_id,
            expires_at=expires_at
        )
        
        await user_role.insert()
        
        return {
            "code": 200,
            "msg": "角色分配成功",
            "data": {}
        }
    
    @try_except_async_request
    @require_permission("user:write")
    async def delete(self, user_id, role_id):
        """移除用户的角色"""
        # 检查用户是否存在
        user = await User.get(user_id)
        if not user:
            return {"code": 404, "msg": "用户不存在", "data": {}}
        
        # 查找并移除角色
        user_role = await UserRole.find_one({
            "user_id": user_id,
            "role_id": role_id,
            "is_active": True
        })
        
        if not user_role:
            return {"code": 400, "msg": "用户未拥有该角色", "data": {}}
        
        # 软删除
        user_role.is_active = False
        user_role.updated_at = datetime.utcnow()
        await user_role.save()
        
        return {
            "code": 200,
            "msg": "角色移除成功",
            "data": {}
        }


class UserPermissionHandler(RequestHandler, PermissionMixin):
    """用户权限管理处理器"""
    
    @try_except_async_request
    @require_permission("user:read")
    async def get(self, user_id=None):
        """获取用户权限信息"""
        if user_id:
            # 获取指定用户的权限
            user = await User.get(user_id)
            if not user:
                return {"code": 404, "msg": "用户不存在", "data": {}}
        else:
            # 获取当前用户的权限
            current_user_id = await self.get_current_user_id()
            if not current_user_id:
                return {"code": 401, "msg": "未认证，请先登录", "data": {}}
            user_id = current_user_id
        
        # 获取用户角色
        user_roles = await UserRole.find({"user_id": user_id, "is_active": True}).to_list()
        
        # 收集所有权限
        all_permissions = set()
        role_list = []
        
        for user_role in user_roles:
            role = await Role.get(user_role.role_id)
            if role and role.is_active:
                role_list.append({
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                    "is_system": role.is_system
                })
                # 添加角色权限
                if role.permissions:
                    all_permissions.update(role.permissions)
        
        # 获取权限详情
        permission_list = []
        for perm_id in all_permissions:
            permission = await Permission.get(perm_id)
            if permission and permission.is_active:
                permission_list.append({
                    "id": str(permission.id),
                    "name": permission.name,
                    "resource": permission.resource,
                    "action": permission.action,
                    "description": permission.description
                })
        
        return {
            "code": 200,
            "msg": "获取用户权限成功",
            "data": {
                "roles": role_list,
                "permissions": permission_list
            }
        }
    
    @try_except_async_request
    @require_permission("user:read")
    async def post(self, user_id):
        """检查用户是否有指定权限"""
        # 检查用户是否存在
        user = await User.get(user_id)
        if not user:
            return {"code": 404, "msg": "用户不存在", "data": {}}
        
        data = json.loads(self.request.body)
        
        if not data.get("permissions"):
            return {"code": 400, "msg": "权限列表为必填项", "data": {}}
        
        permissions = data["permissions"]
        if isinstance(permissions, str):
            permissions = [permissions]
        
        # 获取用户所有权限
        user_roles = await UserRole.find({"user_id": user_id, "is_active": True}).to_list()
        user_permissions = set()
        
        for user_role in user_roles:
            role = await Role.get(user_role.role_id)
            if role and role.is_active and role.permissions:
                user_permissions.update(role.permissions)
        
        # 检查权限
        result = {}
        for perm in permissions:
            result[perm] = perm in user_permissions
        
        return {
            "code": 200,
            "msg": "权限检查完成",
            "data": {"permissions": result}
        }


class UserStatsHandler(RequestHandler, PermissionMixin):
    """用户统计处理器"""
    
    @try_except_async_request
    @require_permission("user:read")
    async def get(self):
        """获取用户统计信息"""
        # 总用户数
        total_users = await User.count_documents({"is_active": True})
        
        # 管理员数量
        admin_count = await User.count_documents({"is_active": True, "is_admin": True})
        
        # 今日新增用户
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users = await User.count_documents({
            "is_active": True,
            "created_at": {"$gte": today}
        })
        
        # 活跃用户（有登录记录的用户）
        active_users = await User.count_documents({
            "is_active": True,
            "last_login": {"$exists": True, "$ne": None}
        })
        
        return {
            "code": 200,
            "msg": "获取用户统计成功",
            "data": {
                "total_users": total_users,
                "admin_count": admin_count,
                "today_users": today_users,
                "active_users": active_users
            }
        } 