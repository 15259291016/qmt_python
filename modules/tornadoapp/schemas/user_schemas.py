"""
用户管理API的Pydantic模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., description="用户名", min_length=3, max_length=50, example="john_doe")
    email: EmailStr = Field(..., description="邮箱", example="john@example.com")
    password: str = Field(..., description="密码", min_length=6, max_length=100, example="password123")
    full_name: Optional[str] = Field(None, description="全名", max_length=100, example="John Doe")
    is_active: bool = Field(True, description="是否激活", example=True)
    is_admin: bool = Field(False, description="是否管理员", example=False)


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = Field(None, description="邮箱", example="john@example.com")
    full_name: Optional[str] = Field(None, description="全名", max_length=100, example="John Doe")
    is_active: Optional[bool] = Field(None, description="是否激活", example=True)
    is_admin: Optional[bool] = Field(None, description="是否管理员", example=False)
    is_super_admin: Optional[bool] = Field(None, description="是否超级管理员", example=False)


class RoleInfo(BaseModel):
    """角色信息"""
    id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_system: bool = Field(..., description="是否系统角色")


class UserResponse(BaseModel):
    """用户响应"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    is_active: bool = Field(..., description="是否激活")
    is_admin: bool = Field(..., description="是否管理员")
    is_super_admin: bool = Field(..., description="是否超级管理员")
    roles: Optional[List[RoleInfo]] = Field(None, description="角色列表")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    last_login: Optional[str] = Field(None, description="最后登录时间")
    subscription_expire_at: Optional[str] = Field(None, description="订阅过期时间")


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserResponse] = Field(..., description="用户列表")
    pagination: Dict[str, Any] = Field(..., description="分页信息")


class UserQueryParams(BaseModel):
    """用户查询参数（GET）"""
    page: int = Field(1, description="页码", ge=1, example=1)
    limit: int = Field(10, description="每页数量", ge=1, le=100, example=10)
    search: Optional[str] = Field(None, description="搜索关键词（用户名/邮箱/全名）", example="john")


class UserRoleAssignRequest(BaseModel):
    """分配用户角色请求"""
    role_id: str = Field(..., description="角色ID", example="role_001")
    expires_at: Optional[str] = Field(None, description="过期时间 (ISO格式)", example="2024-12-31T23:59:59")


class UserPermissionCheckRequest(BaseModel):
    """检查用户权限请求"""
    permissions: List[str] = Field(..., description="权限列表", min_items=1, example=["user:read", "user:write"])


class UserPermissionCheckResponse(BaseModel):
    """检查用户权限响应"""
    permissions: Dict[str, bool] = Field(..., description="权限检查结果", example={"user:read": True, "user:write": False})


class UserStatsResponse(BaseModel):
    """用户统计响应"""
    total_users: int = Field(..., description="总用户数")
    admin_count: int = Field(..., description="管理员数量")
    today_users: int = Field(..., description="今日新增用户")
    active_users: int = Field(..., description="活跃用户数")

