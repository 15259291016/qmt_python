"""
基于Pydantic和类型注解的自动Swagger生成示例
无需装饰器，从代码自动推断文档
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from modules.tornadoapp.define.base.handler import BaseHandler


# 定义请求/响应模型（Pydantic会自动生成Schema）
class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., description="用户名", example="john_doe")
    password: str = Field(..., description="密码", min_length=6, example="password123")
    email: str = Field(..., description="邮箱", example="john@example.com")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    created_at: str = Field(..., description="创建时间")


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")


class UserHandler(BaseHandler):
    """用户管理Handler - 无需装饰器，自动从类型注解生成文档"""
    
    async def get(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> UserListResponse:
        """
        获取用户列表或单个用户
        
        Args:
            user_id: 用户ID（可选，不传则返回列表）
            page: 页码
            limit: 每页数量
        
        Returns:
            用户列表或用户详情
        """
        if user_id:
            # 返回单个用户
            return UserResponse(
                id=user_id,
                username="test",
                email="test@example.com",
                created_at="2024-01-01"
            )
        else:
            # 返回用户列表
            return UserListResponse(
                users=[],
                total=0,
                page=page,
                limit=limit
            )
    
    async def post(self, request: UserCreateRequest) -> UserResponse:
        """
        创建新用户
        
        Args:
            request: 创建用户请求
        
        Returns:
            创建的用户信息
        """
        # 业务逻辑
        return UserResponse(
            id="123",
            username=request.username,
            email=request.email,
            created_at="2024-01-01"
        )
    
    async def put(self, user_id: str, request: UserUpdateRequest) -> UserResponse:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            request: 更新请求
        
        Returns:
            更新后的用户信息
        """
        # 业务逻辑
        return UserResponse(
            id=user_id,
            username=request.username or "default",
            email=request.email or "default@example.com",
            created_at="2024-01-01"
        )

