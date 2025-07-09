from enum import Enum


class Status(int, Enum):
    """响应业务状态码"""

    SUCCESS = 0  # 成功
    UNKNOWN_ERROR = -1  # 异常
    FAILED = UNKNOWN_ERROR


class Message(str, Enum):
    """响应业务信息"""

    SUCCESS = "成功"
    UNKNOWN_ERROR = "服务器异常"
    PARAMETER_ERROR = "请求参数错误"
    ALGORITHMS_ERROR = "算法服务异常"
    ALGORITHMS_TIMEOUT = "算法服务超时"
    FILE_MODIFIED = "配置文件更新中"
    NOT_MODEL = "没有可用模型"
    ALREADY_EXISTS_OBJECT = "对象已存在"
    NOT_FIND_OBJECT = "找不到该对象"
    NOT_FIND_USER = "找不到该用户"
    NOT_ALLOW = "不允许访问"
    AUTH_FAIL = "认证失败"
    ZHIYAN_TIMEOUT = "获取智研日志超时"
    ZHIYAN_ERROR = "智研服务器异常"
    NO_ACCESS = "没有权限"


class StatisticEnum(Enum):
    """ aigc-web-platform功能模块使用"""
    YM_COLOR_CHANGE_EVALUATION = 1  # 元梦关卡换色测评
    YM_2D_REF_GRAPH_EVALUATION = 2  # 元梦2d参考图测评
    LLM_EVALUATION = 3  # LLM测评
    EVAL_TASK_GSB = 4  # 测评任务GSB测评
    EVAL_TASK_MOS = 5  # 测评任务MOS测评
    TDOC_LLM_SINGLE_EVALUATION = 6  # 腾讯文档LLM单独测评任务
    TDOC_LLM_COMPARE_EVALUATION = 7  # 腾讯文档LLM对比测评任务
    HOKI_EVALUATION = 8 # 视频骨骼测评
    AIAGENT_USE_STATISTICS = 9 # AIAGENT平台使用统计
    SCRIPT_MANAGEMENT = 10  # 话术版本管理
    KNOWLEDGE_BASE = 11  # 知识库
