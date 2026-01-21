"""
Swagger装饰器使用示例
展示如何使用装饰器自动生成API文档
"""
from modules.tornadoapp.utils.swagger_decorator import swagger_doc
from modules.tornadoapp.define.base.handler import BaseHandler


class ExampleHandler(BaseHandler):
    """示例处理器，展示如何使用Swagger装饰器"""
    
    @swagger_doc(
        path="/api/example/users",
        method="get",
        summary="获取用户列表",
        description="获取所有用户列表，支持分页和过滤",
        tags=["用户管理"],
        parameters=[
            {
                "name": "page",
                "in": "query",
                "schema": {"type": "integer", "default": 1},
                "description": "页码"
            },
            {
                "name": "limit",
                "in": "query",
                "schema": {"type": "integer", "default": 20},
                "description": "每页数量"
            }
        ],
        responses={
            "200": {
                "description": "成功",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer"},
                                "msg": {"type": "string"},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "users": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "username": {"type": "string"},
                                                    "email": {"type": "string"}
                                                }
                                            }
                                        },
                                        "total": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    async def get(self):
        """获取用户列表"""
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 20))
        # 实际业务逻辑...
        self.write({"code": 200, "msg": "success", "data": {"users": [], "total": 0}})
    
    @swagger_doc(
        path="/api/example/users/{user_id}",
        method="get",
        summary="获取用户详情",
        description="根据用户ID获取用户详细信息",
        tags=["用户管理"],
        parameters=[
            {
                "name": "user_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "用户ID"
            }
        ],
        responses={
            "200": {
                "description": "成功",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer"},
                                "msg": {"type": "string"},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "username": {"type": "string"},
                                        "email": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "404": {
                "description": "用户不存在",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            }
        }
    )
    async def get_user(self, user_id: str):
        """获取用户详情"""
        # 实际业务逻辑...
        self.write({"code": 200, "msg": "success", "data": {}})
    
    @swagger_doc(
        path="/api/example/users",
        method="post",
        summary="创建用户",
        description="创建新用户",
        tags=["用户管理"],
        request_body={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["username", "password", "email"],
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "用户名",
                                "example": "john_doe"
                            },
                            "password": {
                                "type": "string",
                                "description": "密码",
                                "example": "password123"
                            },
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "邮箱",
                                "example": "john@example.com"
                            }
                        }
                    }
                }
            }
        },
        responses={
            "200": {
                "description": "创建成功",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer"},
                                "msg": {"type": "string"},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "username": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "400": {
                "description": "参数错误",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            }
        }
    )
    async def post(self):
        """创建用户"""
        # 实际业务逻辑...
        self.write({"code": 200, "msg": "success", "data": {}})

