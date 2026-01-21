"""
基于类型注解和Pydantic的自动Swagger生成
比装饰器更优雅：从代码自动推断，无需手动写文档
"""
from typing import Dict, Any, Optional, List, Type, get_type_hints, get_origin, get_args
from inspect import signature, Parameter
from dataclasses import dataclass, field
import inspect
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def pydantic_model_to_openapi_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """将Pydantic模型转换为OpenAPI Schema"""
    if not issubclass(model, BaseModel):
        return {}
    
    schema = model.model_json_schema()
    return schema


def python_type_to_openapi_type(python_type: Type) -> Dict[str, Any]:
    """将Python类型转换为OpenAPI类型"""
    type_mapping = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    
    # 处理基础类型
    if python_type in type_mapping:
        return type_mapping[python_type]
    
    # 处理Optional
    origin = get_origin(python_type)
    if origin is Optional or (hasattr(origin, '__origin__') and origin.__origin__ is type(None)):
        args = get_args(python_type)
        if args:
            return python_type_to_openapi_type(args[0])
    
    # 处理List
    if origin is list or origin is List:
        args = get_args(python_type)
        if args:
            return {
                "type": "array",
                "items": python_type_to_openapi_type(args[0])
            }
        return {"type": "array"}
    
    # 处理Dict
    if origin is dict or origin is Dict:
        return {"type": "object"}
    
    # 处理Pydantic模型
    if inspect.isclass(python_type) and issubclass(python_type, BaseModel):
        return pydantic_model_to_openapi_schema(python_type)
    
    # 默认返回object
    return {"type": "object"}


def extract_route_params(handler_class: Type, method_name: str) -> List[Dict[str, Any]]:
    """从Handler方法签名提取路由参数"""
    if not hasattr(handler_class, method_name):
        return []
    
    method = getattr(handler_class, method_name)
    sig = signature(method)
    params = []
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        
        param_info = {
            "name": param_name,
            "in": "query",  # 默认是query参数
            "required": param.default == Parameter.empty,
            "schema": python_type_to_openapi_type(param.annotation) if param.annotation != Parameter.empty else {"type": "string"}
        }
        
        # 如果有默认值，添加example
        if param.default != Parameter.empty:
            param_info["schema"]["default"] = param.default
        
        params.append(param_info)
    
    return params


def extract_request_body(handler_class: Type, method_name: str) -> Optional[Dict[str, Any]]:
    """从Handler方法签名提取请求体（如果使用Pydantic模型）"""
    method = getattr(handler_class, method_name)
    sig = signature(method)
    
    # 查找类型为BaseModel的参数
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        
        if inspect.isclass(param.annotation) and issubclass(param.annotation, BaseModel):
            return {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": pydantic_model_to_openapi_schema(param.annotation)
                    }
                }
            }
    
    return None


def extract_response_model(handler_class: Type, method_name: str) -> Optional[Dict[str, Any]]:
    """从Handler方法返回类型注解提取响应模型"""
    method = getattr(handler_class, method_name)
    return_annotation = signature(method).return_annotation
    
    if return_annotation == inspect.Signature.empty:
        return None
    
    # 处理Union类型（如Optional）
    origin = get_origin(return_annotation)
    if origin is Optional or (hasattr(origin, '__origin__') and origin.__origin__ is type(None)):
        args = get_args(return_annotation)
        if args:
            return_annotation = args[0]
    
    # 如果是Pydantic模型
    if inspect.isclass(return_annotation) and issubclass(return_annotation, BaseModel):
        return {
            "200": {
                "description": "成功",
                "content": {
                    "application/json": {
                        "schema": pydantic_model_to_openapi_schema(return_annotation)
                    }
                }
            }
        }
    
    return None


def auto_generate_openapi_spec(
    handlers: List[Type],
    title: str = "量化交易系统 API",
    version: str = "1.0.0",
    description: str = "多策略量化交易系统 RESTful API 文档（自动生成）",
    base_url: str = "http://localhost:8888"
) -> Dict[str, Any]:
    """
    自动从Handler类生成OpenAPI规范
    
    Args:
        handlers: Handler类列表
        title: API标题
        version: API版本
        description: API描述
        base_url: 基础URL
    
    Returns:
        OpenAPI 3.0 规范字典
    """
    paths: Dict[str, Any] = {}
    all_tags = set()
    
    for handler_class in handlers:
        # 从类名提取tag
        tag = handler_class.__name__.replace("Handler", "").replace("_", " ").title()
        all_tags.add(tag)
        
        # 扫描所有HTTP方法
        http_methods = ['get', 'post', 'put', 'delete', 'patch']
        for method_name in http_methods:
            if not hasattr(handler_class, method_name):
                continue
            
            method = getattr(handler_class, method_name)
            
            # 从docstring提取信息
            doc = inspect.getdoc(method) or ""
            summary = doc.split('\n')[0] if doc else f"{method_name.upper()} {handler_class.__name__}"
            description = doc if doc else ""
            
            # 提取路径（需要从路由配置中获取，这里简化处理）
            # 实际使用时需要从app.py的路由配置中提取
            path = f"/api/{handler_class.__name__.lower().replace('handler', '')}"
            
            if path not in paths:
                paths[path] = {}
            
            # 提取参数
            parameters = extract_route_params(handler_class, method_name)
            
            # 提取请求体
            request_body = extract_request_body(handler_class, method_name)
            
            # 提取响应模型
            responses = extract_response_model(handler_class, method_name) or {
                "200": {"description": "成功"}
            }
            
            paths[path][method_name] = {
                "summary": summary,
                "description": description,
                "tags": [tag],
                "responses": responses
            }
            
            if parameters:
                paths[path][method_name]["parameters"] = parameters
            
            if request_body:
                paths[path][method_name]["requestBody"] = request_body
    
    return {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": description
        },
        "servers": [{"url": base_url, "description": "本地开发服务器"}],
        "tags": [{"name": tag, "description": f"{tag}相关接口"} for tag in sorted(all_tags)],
        "paths": paths,
        "components": {
            "schemas": {}
        }
    }

