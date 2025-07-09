class ErrorCode(object):
    SUCCESS = 0
    UNKONW_ERROR = -1
    SESSION_TIMEOUT_ERROR = -2
    PARAMS_ERROR = 100
    SERVICE_ERROR = 200
    RESULT_ERROR = 300
    CHECK_ERROR = 400
    NO_MODE = 1001
    NO_FILE = 1002
    NO_USER = 1003
    NO_TASK = 1004
    DIR_EXISTED = 1005
    NOT_EXIST = 1006


class ErrorMsg(object):
    SUCCESS = "success"
    UNKONW_ERROR = "未知错误，请联系相关人员"
    SESSION_TIMEOUT_ERROR = "session 已过期，请重新创建 session"
    PARAMS_ERROR = "参数检验错误"
    SERVICE_ERROR = "服务调用异常"
    RESULT_ERROR = "服务执行结果异常"
    CHECK_ERROR = "文件检查错误"
    NO_MODE = "未找到对应管线"
    NO_FILE = "未找到对应文件"
    NO_USER = "未找到该用户"
    NO_TASK = "未找到该任务"
    DIR_EXISTED = "目录已存在"
    NOT_EXIST = "对象不存在"
