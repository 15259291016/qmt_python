from beanie import Document, Indexed
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field
from enum import Enum


class PermissionType(str, Enum):
    """权限类型枚举"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """资源类型枚举"""
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SYSTEM = "system"
    DATA = "data"


class Role(Document):
    """角色模型"""
    
    name: Indexed(str, unique=True) = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    permissions: List[str] = Field(default=[], description="权限列表")
    is_active: bool = Field(default=True, description="是否激活")
    is_system: bool = Field(default=False, description="是否系统角色")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者ID")
    
    class Settings:
        name = "roles"
        indexes = [
            "name",
            "is_active",
            ("name", "is_active"),
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "name": "admin",
                "description": "系统管理员",
                "permissions": ["user:read", "user:write", "role:admin"],
                "is_active": True,
                "is_system": True
            }
        }


class Permission(Document):
    """权限模型"""
    
    name: Indexed(str, unique=True) = Field(..., description="权限名称")
    resource: str = Field(..., description="资源类型")
    action: str = Field(..., description="操作类型")
    description: Optional[str] = Field(None, description="权限描述")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    class Settings:
        name = "permissions"
        indexes = [
            "name",
            "resource",
            "action",
            "is_active",
            ("resource", "action"),
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "name": "user:read",
                "resource": "user",
                "action": "read",
                "description": "读取用户信息",
                "is_active": True
            }
        }


class UserRole(Document):
    """用户角色关联模型"""
    
    user_id: Indexed(str) = Field(..., description="用户ID")
    role_id: Indexed(str) = Field(..., description="角色ID")
    assigned_by: Optional[str] = Field(None, description="分配者ID")
    assigned_at: datetime = Field(default_factory=datetime.utcnow, description="分配时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: bool = Field(default=True, description="是否激活")
    
    class Settings:
        name = "user_roles"
        indexes = [
            "user_id",
            "role_id",
            "is_active",
            ("user_id", "role_id"),
            ("user_id", "is_active"),
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "role_id": "role456",
                "assigned_by": "admin123",
                "expires_at": "2024-12-31T23:59:59Z",
                "is_active": True
            }
        }


class PermissionGroup(Document):
    """权限组模型"""
    
    name: Indexed(str, unique=True) = Field(..., description="权限组名称")
    description: Optional[str] = Field(None, description="权限组描述")
    permissions: List[str] = Field(default=[], description="权限列表")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者ID")
    
    class Settings:
        name = "permission_groups"
        indexes = [
            "name",
            "is_active",
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "name": "user_management",
                "description": "用户管理权限组",
                "permissions": ["user:read", "user:write", "user:delete"],
                "is_active": True
            }
        } 