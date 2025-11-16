"""
Swagger API 文档处理器
提供 OpenAPI 规范和 Swagger UI 界面
"""
import json
from typing import Dict, Any
from tornado.web import RequestHandler
from modules.tornadoapp.define.base.handler import BaseHandler


class SwaggerUIHandler(BaseHandler):
    """Swagger UI 界面处理器"""
    
    async def get(self):
        """返回 Swagger UI HTML 页面"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>量化交易系统 API 文档</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/api-docs/swagger.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                docExpansion: "list",
                filter: true,
                showExtensions: true,
                showCommonExtensions: true
            });
        };
    </script>
</body>
</html>
        """
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.write(html_content)


class OpenAPIHandler(BaseHandler):
    """OpenAPI 规范 JSON 处理器"""
    
    def get_openapi_spec(self) -> Dict[str, Any]:
        """生成 OpenAPI 3.0 规范文档"""
        host = self.request.host.split(':')[0]
        port = self.request.host.split(':')[1] if ':' in self.request.host else '8888'
        base_url = f"http://{host}:{port}"
        
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "量化交易系统 API",
                "description": "多策略量化交易系统 RESTful API 文档",
                "version": "1.0.0",
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
                {"name": "认证", "description": "用户认证相关接口"},
                {"name": "用户管理", "description": "用户信息管理"},
                {"name": "权限管理", "description": "角色和权限管理"},
                {"name": "持仓分析", "description": "持仓数据分析和报告"},
                {"name": "技术分析", "description": "技术指标分析和交易信号"},
                {"name": "选股", "description": "股票筛选和推荐"},
                {"name": "风险管理", "description": "风险配置和黑名单管理"},
                {"name": "合规审计", "description": "合规日志和审计记录"},
                {"name": "行情数据", "description": "市场行情数据接口"}
            ],
            "paths": {
                "/api/auth/login": {
                    "post": {
                        "tags": ["认证"],
                        "summary": "用户登录",
                        "description": "用户登录获取访问令牌",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "username": {"type": "string", "example": "admin"},
                                            "password": {"type": "string", "example": "password123"}
                                        },
                                        "required": ["username", "password"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "登录成功",
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
                                                        "token": {"type": "string"},
                                                        "refresh_token": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/auth/register": {
                    "post": {
                        "tags": ["认证"],
                        "summary": "用户注册",
                        "description": "注册新用户账号",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "username": {"type": "string"},
                                            "password": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {"description": "注册成功"}
                        }
                    }
                },
                "/api/position/analysis": {
                    "get": {
                        "tags": ["持仓分析"],
                        "summary": "获取持仓分析",
                        "description": "分析当前账户持仓情况",
                        "parameters": [
                            {
                                "name": "account_id",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "账户ID"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "持仓分析结果",
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
                                                        "summary": {"type": "object"},
                                                        "risk": {"type": "object"},
                                                        "positions": {"type": "array"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/technical/analysis": {
                    "get": {
                        "tags": ["技术分析"],
                        "summary": "获取技术分析",
                        "description": "获取持仓股票的技术分析结果",
                        "parameters": [
                            {
                                "name": "account_id",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "账户ID"
                            },
                            {
                                "name": "symbol",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "string"},
                                "description": "股票代码（可选，不传则分析所有持仓）"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "技术分析结果",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "code": {"type": "integer"},
                                                "msg": {"type": "string"},
                                                "data": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/stock/select": {
                    "get": {
                        "tags": ["选股"],
                        "summary": "股票筛选",
                        "description": "根据条件筛选股票",
                        "parameters": [
                            {
                                "name": "top_n",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "integer", "default": 10},
                                "description": "返回前N只股票"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "筛选结果",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "code": {"type": "integer"},
                                                "msg": {"type": "string"},
                                                "data": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/risk/config": {
                    "get": {
                        "tags": ["风险管理"],
                        "summary": "获取风险配置",
                        "responses": {
                            "200": {"description": "风险配置信息"}
                        }
                    },
                    "post": {
                        "tags": ["风险管理"],
                        "summary": "更新风险配置",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "max_position": {"type": "number"},
                                            "max_daily_loss": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {"description": "配置更新成功"}
                        }
                    }
                },
                "/api/compliance/logs": {
                    "get": {
                        "tags": ["合规审计"],
                        "summary": "获取合规日志",
                        "parameters": [
                            {
                                "name": "page",
                                "in": "query",
                                "schema": {"type": "integer", "default": 1}
                            },
                            {
                                "name": "page_size",
                                "in": "query",
                                "schema": {"type": "integer", "default": 20}
                            }
                        ],
                        "responses": {
                            "200": {"description": "合规日志列表"}
                        }
                    }
                },
                "/api/audit/logs": {
                    "get": {
                        "tags": ["合规审计"],
                        "summary": "获取审计日志",
                        "responses": {
                            "200": {"description": "审计日志列表"}
                        }
                    }
                },
                "/api/bar_data": {
                    "get": {
                        "tags": ["行情数据"],
                        "summary": "获取K线数据",
                        "parameters": [
                            {
                                "name": "symbol",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "股票代码"
                            },
                            {
                                "name": "start_date",
                                "in": "query",
                                "schema": {"type": "string"},
                                "description": "开始日期"
                            },
                            {
                                "name": "end_date",
                                "in": "query",
                                "schema": {"type": "string"},
                                "description": "结束日期"
                            }
                        ],
                        "responses": {
                            "200": {"description": "K线数据"}
                        }
                    }
                }
            },
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
    
    async def get(self):
        """返回 OpenAPI 规范 JSON"""
        spec = self.get_openapi_spec()
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(spec, ensure_ascii=False, indent=2))

