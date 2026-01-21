"""
Swagger 自动文档生成工具
使用装饰器自动生成 OpenAPI 文档，避免手动维护
"""
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
import inspect
from dataclasses import dataclass, field


# 全局存储所有API的文档信息
_api_docs: Dict[str, Dict[str, Any]] = {}


@dataclass
class SwaggerDoc:
    """Swagger文档配置"""
    summary: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    deprecated: bool = False
    security: Optional[List[Dict[str, List[str]]]] = None


def swagger_doc(
    path: str,
    method: str = "get",
    summary: str = "",
    description: str = "",
    tags: Optional[List[str]] = None,
    parameters: Optional[List[Dict[str, Any]]] = None,
    request_body: Optional[Dict[str, Any]] = None,
    responses: Optional[Dict[str, Dict[str, Any]]] = None,
    deprecated: bool = False,
    security: Optional[List[Dict[str, List[str]]]] = None
):
    """
    Swagger文档装饰器
    
    Args:
        path: API路径（支持路径参数，如 /api/users/{user_id}）
        method: HTTP方法（get, post, put, delete等）
        summary: 接口摘要
        description: 接口详细描述
        tags: 标签列表
        parameters: 参数列表
        request_body: 请求体定义
        responses: 响应定义
        deprecated: 是否已废弃
        security: 安全要求
    
    Example:
        @swagger_doc(
            path="/api/users/{user_id}",
            method="get",
            summary="获取用户信息",
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
                                    "id": {"type": "string"},
                                    "username": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        )
        async def get(self, user_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # 注册API文档
        key = f"{method.upper()}:{path}"
        _api_docs[key] = {
            "path": path,
            "method": method.lower(),
            "summary": summary or func.__doc__ or "",
            "description": description or func.__doc__ or "",
            "tags": tags or [],
            "parameters": parameters or [],
            "request_body": request_body,
            "responses": responses or {
                "200": {
                    "description": "成功"
                }
            },
            "deprecated": deprecated,
            "security": security,
            "handler": func
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_all_api_docs() -> Dict[str, Dict[str, Any]]:
    """获取所有注册的API文档"""
    return _api_docs.copy()


def generate_openapi_spec(
    title: str = "量化交易系统 API",
    version: str = "1.0.0",
    description: str = "多策略量化交易系统 RESTful API 文档",
    base_url: str = "http://localhost:8888"
) -> Dict[str, Any]:
    """
    自动生成 OpenAPI 规范文档
    
    Args:
        title: API标题
        version: API版本
        description: API描述
        base_url: 基础URL
    
    Returns:
        OpenAPI 3.0 规范字典
    """
    # 收集所有标签
    all_tags = set()
    for doc in _api_docs.values():
        all_tags.update(doc.get("tags", []))
    
    # 按路径组织API
    paths: Dict[str, Dict[str, Any]] = {}
    for key, doc in _api_docs.items():
        path = doc["path"]
        method = doc["method"]
        
        if path not in paths:
            paths[path] = {}
        
        paths[path][method] = {
            "summary": doc["summary"],
            "description": doc["description"],
            "tags": doc["tags"],
            "deprecated": doc["deprecated"],
        }
        
        if doc.get("parameters"):
            paths[path][method]["parameters"] = doc["parameters"]
        
        if doc.get("request_body"):
            paths[path][method]["requestBody"] = doc["request_body"]
        
        if doc.get("responses"):
            paths[path][method]["responses"] = doc["responses"]
        
        if doc.get("security"):
            paths[path][method]["security"] = doc["security"]
    
    return {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": description,
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            }
        },
        "servers": [
            {
                "url": base_url,
                "description": "本地开发服务器"
            }
        ],
        "tags": [
            {"name": tag, "description": f"{tag}相关接口"}
            for tag in sorted(all_tags)
        ],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT 认证令牌，格式：Bearer {token}"
                }
            },
            "schemas": {
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "description": "错误码"},
                        "msg": {"type": "string", "description": "错误消息"},
                        "data": {"type": "object", "description": "错误详情"}
                    }
                },
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "description": "状态码，0表示成功"},
                        "msg": {"type": "string", "description": "状态消息"},
                        "data": {"type": "object", "description": "响应数据"}
                    }
                }
            }
        },
        "security": [
            {
                "BearerAuth": []
            }
        ]
    }

