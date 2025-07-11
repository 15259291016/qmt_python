from beanie import Document, Indexed
from typing import Optional
from datetime import datetime
from pydantic import Field


class User(Document):
    """用户模型"""
    
    username: Indexed(str, unique=True) = Field(..., description="用户名")
    email: Indexed(str, unique=True) = Field(..., description="邮箱")
    password_hash: str = Field(..., description="密码哈希")
    full_name: Optional[str] = Field(None, description="全名")
    is_active: bool = Field(default=True, description="是否激活")
    is_admin: bool = Field(default=False, description="是否管理员")
    is_super_admin: bool = Field(default=False, description="是否超级管理员")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    subscription_expire_at: Optional[datetime] = Field(None, description="订阅到期时间")
    
    class Settings:
        name = "users"
        indexes = [
            "username",
            "email",
            ("username", "email"),
            "is_admin",
            "is_super_admin",
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "is_active": True,
                "is_admin": False,
                "is_super_admin": False
            }
        }


class UserSession(Document):
    """用户会话模型"""
    
    user_id: str = Field(..., description="用户ID")
    token: str = Field(..., description="JWT token")
    refresh_token: str = Field(..., description="刷新token")
    expires_at: datetime = Field(..., description="过期时间")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    is_active: bool = Field(default=True, description="是否有效")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    class Settings:
        name = "user_sessions"
        indexes = [
            "user_id",
            "token",
            "refresh_token",
            ("user_id", "is_active"),
        ] 