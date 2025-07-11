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
from modules.tornadoapp.utils.response_model import try_except_async_request, FailedResponse


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
                return FailedResponse(msg="用户不存在")
            
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
                    "is_super_admin": user.is_super_admin,
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
            
            # 构建查询条件
            query = {}
            if search:
                query["$or"] = [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"full_name": {"$regex": search, "$options": "i"}}
                ]
            
            # 计算总数
            total = len(await User.find(query).to_list())
            
            # 获取用户列表
            users = await User.find(query).skip((page - 1) * limit).limit(limit).to_list()
            
            user_list = []
            for user in users:
                # 获取用户的角色信息
                user_roles = await UserRole.find({"user_id": str(user.id), "is_active": True}).to_list()
                roles = []
                for user_role in user_roles:
                    role = await Role.get(user_role.role_id)
                    if role and role.is_active:
                        roles.append({
                            "id": str(role.id),
                            "name": role.name,
                            "description": role.description
                        })
                
                user_list.append({
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "is_super_admin": user.is_super_admin,
                    "roles": roles,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None
                })
            
            return {
                    "users": user_list,
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
            return FailedResponse(msg="用户名、邮箱和密码为必填项")
        
        # 检查用户名是否已存在
        existing_user = await User.find_one({"username": data["username"]})
        if existing_user:
            return FailedResponse(msg="用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = await User.find_one({"email": data["email"]})
        if existing_email:
            return FailedResponse(msg="邮箱已存在")
        
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
        """更新用户信息"""
        data = json.loads(self.request.body)
        
        user = await User.get(user_id)
        if not user:
            return FailedResponse(msg="用户不存在")
        
        # 检查当前用户权限
        current_user_id = await self.get_current_user_id()
        current_user = await User.get(current_user_id)
        
        # 只有超级管理员可以修改超级管理员状态
        if "is_super_admin" in data and not current_user.is_super_admin:
            return FailedResponse(msg="只有超级管理员可以修改超级管理员状态")
        
        # 普通管理员不能修改超级管理员的其他信息
        if not current_user.is_super_admin and user.is_super_admin:
            return FailedResponse(msg="普通管理员不能修改超级管理员信息")
        
        # 更新用户信息
        update_data = {}
        if "email" in data:
            # 检查邮箱是否已被其他用户使用
            existing_user = await User.find_one({"email": data["email"], "_id": {"$ne": user_id}})
            if existing_user:
                return FailedResponse(msg="邮箱已被使用")
            update_data["email"] = data["email"]
        
        if "full_name" in data:
            update_data["full_name"] = data["full_name"]
        
        if "is_active" in data:
            update_data["is_active"] = data["is_active"]
        
        if "is_admin" in data:
            update_data["is_admin"] = data["is_admin"]
        
        if "is_super_admin" in data and current_user.is_super_admin:
            update_data["is_super_admin"] = data["is_super_admin"]
        
        update_data["updated_at"] = datetime.utcnow()
        
        await user.update({"$set": update_data})
        
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
            return FailedResponse(msg="用户不存在")
        
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
            return FailedResponse(msg="用户不存在")
        
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
            return FailedResponse(msg="用户不存在")
        
        data = json.loads(self.request.body)
        
        if not data.get("role_id"):
            return FailedResponse(msg="角色ID为必填项")
        
        # 检查角色是否存在
        role = await Role.get(data["role_id"])
        if not role or not role.is_active:
            return FailedResponse(msg="角色不存在或已禁用")
        
        # 检查是否已经分配了该角色
        existing_role = await UserRole.find_one({
            "user_id": user_id,
            "role_id": data["role_id"],
            "is_active": True
        })
        if existing_role:
            return FailedResponse(msg="用户已拥有该角色")
        
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
            return FailedResponse(msg="用户不存在")
        
        # 查找并移除角色
        user_role = await UserRole.find_one({
            "user_id": user_id,
            "role_id": role_id,
            "is_active": True
        })
        
        if not user_role:
            return FailedResponse(msg="用户未拥有该角色")
        
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
                return FailedResponse(msg="用户不存在")
        else:
            # 获取当前用户的权限
            current_user_id = await self.get_current_user_id()
            if not current_user_id:
                return FailedResponse(msg="未认证，请先登录")
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
            return FailedResponse(msg="用户不存在")
        
        data = json.loads(self.request.body)
        
        if not data.get("permissions"):
            return FailedResponse(msg="权限列表为必填项")
        
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
        total_users = len(await User.find({"is_active": True}).to_list())
        
        # 管理员数量
        admin_count = len(await User.find({"is_active": True, "is_admin": True}).to_list())
        
        # 今日新增用户
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users = len(await User.find({
            "is_active": True,
            "created_at": {"$gte": today}
        }).to_list())
        
        # 活跃用户（有登录记录的用户）
        active_users = len(await User.find({
            "is_active": True,
            "last_login": {"$exists": True, "$ne": None}
        }).to_list())
        
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


 