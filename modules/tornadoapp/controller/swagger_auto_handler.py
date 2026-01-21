"""
自动生成Swagger文档的处理器
使用装饰器自动收集API文档信息
"""
import json
from typing import Dict, Any
from modules.tornadoapp.define.base.handler import BaseHandler
from modules.tornadoapp.utils.swagger_decorator import generate_openapi_spec


class AutoOpenAPIHandler(BaseHandler):
    """自动生成OpenAPI规范的处理器"""
    
    async def get(self):
        """返回自动生成的 OpenAPI 规范 JSON"""
        host = self.request.host.split(':')[0]
        port = self.request.host.split(':')[1] if ':' in self.request.host else '8888'
        base_url = f"http://{host}:{port}"
        
        spec = generate_openapi_spec(
            title="量化交易系统 API",
            version="1.0.0",
            description="多策略量化交易系统 RESTful API 文档（自动生成）",
            base_url=base_url
        )
        
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(spec, ensure_ascii=False, indent=2))

