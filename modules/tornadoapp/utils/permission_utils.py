from typing import List, Optional, Dict, Any
from datetime import datetime
from modules.tornadoapp.model.user_model import User
from modules.tornadoapp.model.permission_model import Role, Permission, UserRole, PermissionGroup


class PermissionUtils:
    """权限管理工具类"""
    
    @staticmethod
    async def get_user_roles(user_id: str) -> List[Role]:
        """获取用户的所有角色"""
        user_roles = await UserRole.find(
            {"user_id": user_id, "is_active": True}
        ).to_list()
        
        if not user_roles:
            return []
        
        role_ids = [ur.role_id for ur in user_roles]
        roles = await Role.find({"_id": {"$in": role_ids}, "is_active": True}).to_list()
        
        return roles
    
    @staticmethod
    async def get_user_permissions(user_id: str) -> List[str]:
        """获取用户的所有权限"""
        roles = await PermissionUtils.get_user_roles(user_id)
        
        permissions = set()
        for role in roles:
            permissions.update(role.permissions)
        
        return list(permissions)
    
    @staticmethod
    async def check_permission(user_id: str, required_permission: str) -> bool:
        """检查用户是否有指定权限"""
        user_permissions = await PermissionUtils.get_user_permissions(user_id)
        return required_permission in user_permissions
    
    @staticmethod
    async def check_permissions(user_id: str, required_permissions: List[str]) -> Dict[str, bool]:
        """检查用户是否有指定权限列表"""
        user_permissions = await PermissionUtils.get_user_permissions(user_id)
        
        result = {}
        for permission in required_permissions:
            result[permission] = permission in user_permissions
        
        return result
    
    @staticmethod
    async def has_any_permission(user_id: str, required_permissions: List[str]) -> bool:
        """检查用户是否有任意一个指定权限"""
        user_permissions = await PermissionUtils.get_user_permissions(user_id)
        return any(permission in user_permissions for permission in required_permissions)
    
    @staticmethod
    async def has_all_permissions(user_id: str, required_permissions: List[str]) -> bool:
        """检查用户是否有所有指定权限"""
        user_permissions = await PermissionUtils.get_user_permissions(user_id)
        return all(permission in user_permissions for permission in required_permissions)
    
    @staticmethod
    async def assign_role_to_user(user_id: str, role_id: str, assigned_by: str, expires_at: Optional[datetime] = None) -> bool:
        """为用户分配角色"""
        try:
            # 检查角色是否存在
            role = await Role.get(role_id)
            if not role or not role.is_active:
                return False
            
            # 检查是否已经分配过该角色
            existing_role = await UserRole.find_one({
                "user_id": user_id,
                "role_id": role_id,
                "is_active": True
            })
            
            if existing_role:
                # 更新现有分配
                existing_role.assigned_by = assigned_by
                existing_role.expires_at = expires_at
                await existing_role.save()
            else:
                # 创建新的分配
                user_role = UserRole(
                    user_id=user_id,
                    role_id=role_id,
                    assigned_by=assigned_by,
                    expires_at=expires_at
                )
                await user_role.insert()
            
            return True
        except Exception:
            return False
    
    @staticmethod
    async def remove_role_from_user(user_id: str, role_id: str) -> bool:
        """移除用户的角色"""
        try:
            user_role = await UserRole.find_one({
                "user_id": user_id,
                "role_id": role_id,
                "is_active": True
            })
            
            if user_role:
                user_role.is_active = False
                await user_role.save()
                return True
            
            return False
        except Exception:
            return False
    
    @staticmethod
    async def get_role_permissions(role_id: str) -> List[str]:
        """获取角色的所有权限"""
        role = await Role.get(role_id)
        if not role or not role.is_active:
            return []
        
        return role.permissions
    
    @staticmethod
    async def add_permission_to_role(role_id: str, permission: str) -> bool:
        """为角色添加权限"""
        try:
            role = await Role.get(role_id)
            if not role or not role.is_active:
                return False
            
            if permission not in role.permissions:
                role.permissions.append(permission)
                role.updated_at = datetime.utcnow()
                await role.save()
            
            return True
        except Exception:
            return False
    
    @staticmethod
    async def remove_permission_from_role(role_id: str, permission: str) -> bool:
        """从角色移除权限"""
        try:
            role = await Role.get(role_id)
            if not role or not role.is_active:
                return False
            
            if permission in role.permissions:
                role.permissions.remove(permission)
                role.updated_at = datetime.utcnow()
                await role.save()
            
            return True
        except Exception:
            return False
    
    @staticmethod
    async def is_admin(user_id: str) -> bool:
        """检查用户是否是管理员"""
        return await PermissionUtils.check_permission(user_id, "system:admin")
    
    @staticmethod
    async def get_user_permission_summary(user_id: str) -> Dict[str, Any]:
        """获取用户权限摘要"""
        roles = await PermissionUtils.get_user_roles(user_id)
        permissions = await PermissionUtils.get_user_permissions(user_id)
        is_admin = await PermissionUtils.is_admin(user_id)
        
        return {
            "user_id": user_id,
            "roles": [{"id": str(role.id), "name": role.name, "description": role.description} for role in roles],
            "permissions": permissions,
            "is_admin": is_admin,
            "total_roles": len(roles),
            "total_permissions": len(permissions)
        } 