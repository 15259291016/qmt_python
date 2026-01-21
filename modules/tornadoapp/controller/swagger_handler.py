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
                {"name": "行情数据", "description": "市场行情数据接口"},
                {"name": "定时任务", "description": "定时任务管理接口"}
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
                        "description": "获取当前的风险控制配置参数，包括单笔订单限额、每日限额和黑名单",
                        "responses": {
                            "200": {
                                "description": "风险配置信息",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "max_single_order_amount": {
                                                    "type": "number",
                                                    "description": "单笔订单最大金额"
                                                },
                                                "max_daily_amount": {
                                                    "type": "number",
                                                    "description": "每日最大交易金额"
                                                },
                                                "blacklist": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "description": "黑名单股票代码列表"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "tags": ["风险管理"],
                        "summary": "更新风险配置",
                        "description": "更新风险控制配置参数，可以更新单笔订单限额和每日限额",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "max_single_order_amount": {
                                                "type": "number",
                                                "description": "单笔订单最大金额",
                                                "example": 100000
                                            },
                                            "max_daily_amount": {
                                                "type": "number",
                                                "description": "每日最大交易金额",
                                                "example": 1000000
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "配置更新成功",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "msg": {
                                                    "type": "string",
                                                    "example": "风控参数已更新"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/risk/blacklist": {
                    "get": {
                        "tags": ["风险管理"],
                        "summary": "获取黑名单",
                        "description": "获取当前的黑名单股票代码列表",
                        "responses": {
                            "200": {
                                "description": "黑名单列表",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "blacklist": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "description": "黑名单股票代码列表",
                                                    "example": ["000001.SZ", "600000.SH"]
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "tags": ["风险管理"],
                        "summary": "添加股票到黑名单",
                        "description": "将指定股票添加到黑名单，禁止对该股票进行交易",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["symbol"],
                                        "properties": {
                                            "symbol": {
                                                "type": "string",
                                                "description": "股票代码",
                                                "example": "000001.SZ"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "添加成功",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "msg": {
                                                    "type": "string",
                                                    "example": "000001.SZ 已加入黑名单"
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
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "msg": {
                                                    "type": "string",
                                                    "example": "缺少symbol参数"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "delete": {
                        "tags": ["风险管理"],
                        "summary": "从黑名单移除股票",
                        "description": "将指定股票从黑名单中移除，允许对该股票进行交易",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["symbol"],
                                        "properties": {
                                            "symbol": {
                                                "type": "string",
                                                "description": "股票代码",
                                                "example": "000001.SZ"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "移除成功",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "msg": {
                                                    "type": "string",
                                                    "example": "000001.SZ 已移除黑名单"
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
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "msg": {
                                                    "type": "string",
                                                    "example": "缺少symbol参数"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
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
                },
                "/api/scheduler/jobs": {
                    "get": {
                        "tags": ["定时任务"],
                        "summary": "获取定时任务列表",
                        "description": "获取所有定时任务列表，支持分页和过滤",
                        "parameters": [
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
                            },
                            {
                                "name": "status",
                                "in": "query",
                                "schema": {"type": "string", "enum": ["active", "paused", "removed"]},
                                "description": "状态过滤"
                            },
                            {
                                "name": "is_active",
                                "in": "query",
                                "schema": {"type": "boolean"},
                                "description": "是否激活过滤"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "任务列表",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "jobs": {
                                                    "type": "array",
                                                    "items": {"$ref": "#/components/schemas/ScheduledJob"}
                                                },
                                                "pagination": {"$ref": "#/components/schemas/Pagination"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "tags": ["定时任务"],
                        "summary": "创建定时任务",
                        "description": "创建新的定时任务，支持Cron、Interval、Date三种触发器类型",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CreateJobRequest"}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "任务创建成功",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ScheduledJob"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/scheduler/jobs/{job_id}": {
                    "get": {
                        "tags": ["定时任务"],
                        "summary": "获取任务详情",
                        "description": "根据任务ID获取任务详细信息",
                        "parameters": [
                            {
                                "name": "job_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "任务ID"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "任务详情",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ScheduledJob"}
                                    }
                                }
                            }
                        }
                    },
                    "put": {
                        "tags": ["定时任务"],
                        "summary": "更新定时任务",
                        "description": "更新现有定时任务的配置",
                        "parameters": [
                            {
                                "name": "job_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "任务ID"
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UpdateJobRequest"}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "任务更新成功",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ScheduledJob"}
                                    }
                                }
                            }
                        }
                    },
                    "delete": {
                        "tags": ["定时任务"],
                        "summary": "删除定时任务",
                        "description": "删除指定的定时任务",
                        "parameters": [
                            {
                                "name": "job_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "任务ID"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "任务删除成功",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {"type": "string"},
                                                "job_id": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/scheduler/jobs/{job_id}/{action}": {
                    "post": {
                        "tags": ["定时任务"],
                        "summary": "任务控制操作",
                        "description": "对任务执行控制操作：暂停、恢复或立即触发",
                        "parameters": [
                            {
                                "name": "job_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "任务ID"
                            },
                            {
                                "name": "action",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string", "enum": ["pause", "resume", "trigger"]},
                                "description": "操作类型：pause(暂停)、resume(恢复)、trigger(立即触发)"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "操作成功",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {"type": "string"},
                                                "job_id": {"type": "string"},
                                                "action": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/scheduler/stats": {
                    "get": {
                        "tags": ["定时任务"],
                        "summary": "获取任务统计信息",
                        "description": "获取定时任务的统计信息，包括总数、状态分布、执行统计等",
                        "responses": {
                            "200": {
                                "description": "统计信息",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/SchedulerStats"}
                                    }
                                }
                            }
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
                    },
                    "ScheduledJob": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "数据库ID"},
                            "name": {"type": "string", "description": "任务名称"},
                            "job_id": {"type": "string", "description": "任务ID（唯一）"},
                            "func_path": {"type": "string", "description": "函数路径，格式：module.path:function_name"},
                            "trigger_type": {"type": "string", "enum": ["cron", "interval", "date"], "description": "触发器类型"},
                            "status": {"type": "string", "enum": ["active", "paused", "removed"], "description": "任务状态"},
                            "is_active": {"type": "boolean", "description": "是否激活"},
                            "args": {"type": "array", "items": {}, "description": "位置参数列表"},
                            "kwargs": {"type": "object", "description": "关键字参数字典"},
                            "description": {"type": "string", "description": "任务描述"},
                            "next_run_time": {"type": "string", "format": "date-time", "description": "下次执行时间"},
                            "last_run_time": {"type": "string", "format": "date-time", "description": "上次执行时间"},
                            "run_count": {"type": "integer", "description": "执行次数"},
                            "error_count": {"type": "integer", "description": "错误次数"},
                            "last_error": {"type": "string", "description": "最后错误信息"},
                            "trigger": {
                                "type": "object",
                                "description": "触发器配置（根据trigger_type不同而不同）",
                                "oneOf": [
                                    {
                                        "type": "object",
                                        "title": "Cron触发器",
                                        "properties": {
                                            "day_of_week": {"type": "string", "example": "0-4", "description": "星期几"},
                                            "hour": {"type": "integer", "example": 15, "description": "小时 (0-23)"},
                                            "minute": {"type": "integer", "example": 40, "description": "分钟 (0-59)"},
                                            "second": {"type": "integer", "example": 0, "description": "秒 (0-59)"}
                                        }
                                    },
                                    {
                                        "type": "object",
                                        "title": "Interval触发器",
                                        "properties": {
                                            "seconds": {"type": "integer", "description": "间隔秒数"},
                                            "minutes": {"type": "integer", "description": "间隔分钟数"},
                                            "hours": {"type": "integer", "description": "间隔小时数"},
                                            "days": {"type": "integer", "description": "间隔天数"}
                                        }
                                    },
                                    {
                                        "type": "object",
                                        "title": "Date触发器",
                                        "properties": {
                                            "run_date": {"type": "string", "format": "date-time", "description": "执行日期时间"}
                                        }
                                    }
                                ]
                            }
                        }
                    },
                    "CreateJobRequest": {
                        "type": "object",
                        "required": ["name", "job_id", "func_path", "trigger_type"],
                        "properties": {
                            "name": {"type": "string", "example": "数据下载任务", "description": "任务名称"},
                            "job_id": {"type": "string", "example": "download_data", "description": "任务ID（唯一）"},
                            "func_path": {"type": "string", "example": "utils.data:download_all_data", "description": "函数路径"},
                            "trigger_type": {"type": "string", "enum": ["cron", "interval", "date"], "description": "触发器类型"},
                            "description": {"type": "string", "example": "每周一至周五15:40执行数据下载", "description": "任务描述"},
                            "args": {"type": "array", "items": {}, "default": [], "description": "位置参数列表"},
                            "kwargs": {"type": "object", "default": {}, "description": "关键字参数字典"},
                            "day_of_week": {"type": "string", "example": "0-4", "description": "Cron触发器：星期几"},
                            "hour": {"type": "integer", "example": 15, "description": "Cron触发器：小时 (0-23)"},
                            "minute": {"type": "integer", "example": 40, "description": "Cron触发器：分钟 (0-59)"},
                            "second": {"type": "integer", "example": 0, "description": "Cron触发器：秒 (0-59)"},
                            "interval_seconds": {"type": "integer", "description": "Interval触发器：间隔秒数"},
                            "interval_minutes": {"type": "integer", "description": "Interval触发器：间隔分钟数"},
                            "interval_hours": {"type": "integer", "description": "Interval触发器：间隔小时数"},
                            "interval_days": {"type": "integer", "description": "Interval触发器：间隔天数"},
                            "run_date": {"type": "string", "format": "date-time", "description": "Date触发器：执行日期时间"}
                        },
                        "oneOf": [
                            {
                                "title": "Cron触发器请求",
                                "description": "使用Cron触发器时，需要提供day_of_week、hour、minute等参数"
                            },
                            {
                                "title": "Interval触发器请求",
                                "description": "使用Interval触发器时，需要提供至少一个interval_*参数"
                            },
                            {
                                "title": "Date触发器请求",
                                "description": "使用Date触发器时，需要提供run_date参数"
                            }
                        ]
                    },
                    "UpdateJobRequest": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "任务名称"},
                            "description": {"type": "string", "description": "任务描述"},
                            "args": {"type": "array", "items": {}, "description": "位置参数列表"},
                            "kwargs": {"type": "object", "description": "关键字参数字典"},
                            "day_of_week": {"type": "string", "description": "Cron触发器：星期几"},
                            "hour": {"type": "integer", "description": "Cron触发器：小时"},
                            "minute": {"type": "integer", "description": "Cron触发器：分钟"},
                            "second": {"type": "integer", "description": "Cron触发器：秒"},
                            "interval_seconds": {"type": "integer", "description": "Interval触发器：间隔秒数"},
                            "interval_minutes": {"type": "integer", "description": "Interval触发器：间隔分钟数"},
                            "interval_hours": {"type": "integer", "description": "Interval触发器：间隔小时数"},
                            "interval_days": {"type": "integer", "description": "Interval触发器：间隔天数"},
                            "run_date": {"type": "string", "format": "date-time", "description": "Date触发器：执行日期时间"}
                        }
                    },
                    "Pagination": {
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer", "description": "当前页码"},
                            "limit": {"type": "integer", "description": "每页数量"},
                            "total": {"type": "integer", "description": "总记录数"},
                            "pages": {"type": "integer", "description": "总页数"}
                        }
                    },
                    "SchedulerStats": {
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer", "description": "任务总数"},
                            "active": {"type": "integer", "description": "激活任务数"},
                            "paused": {"type": "integer", "description": "暂停任务数"},
                            "removed": {"type": "integer", "description": "已删除任务数"},
                            "by_trigger_type": {
                                "type": "object",
                                "properties": {
                                    "cron": {"type": "integer", "description": "Cron触发器任务数"},
                                    "interval": {"type": "integer", "description": "Interval触发器任务数"},
                                    "date": {"type": "integer", "description": "Date触发器任务数"}
                                }
                            },
                            "execution_stats": {
                                "type": "object",
                                "properties": {
                                    "total_runs": {"type": "integer", "description": "总执行次数"},
                                    "total_errors": {"type": "integer", "description": "总错误次数"},
                                    "error_rate": {"type": "number", "description": "错误率"}
                                }
                            }
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

