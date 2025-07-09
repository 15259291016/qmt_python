from enum import Enum

from utils.config import configs


class AnnotationMode(int, Enum):
    """标注模式"""

    NORMAL = 0  # 普通标注
    TALKING = 1  # 边聊边标
    STREAMING = 2  # 流式模式
    NORMAL_DISPATCH = 3  # 普通标注（测例分发）
    ABTEST = 4  # ABTest 模式
    ALL = -1  # 全部


class CaseStatus(int, Enum):
    """测例标注状态"""

    BEGIN = 0  # 待标注
    DOING = 1  # 进行中
    DONE = 2  # 已完成


class AnnotationState(int, Enum):
    """对话标注状态"""

    YES = 1  # 已标注
    NO = 0  # 未标注


class CaseSource(str, Enum):
    """测例来源标识"""

    FILE = "file"  # 测例文件
    TALKING = "talking"  # 边聊边标
    GLOW = "glow"  # glow 聊天界面
    STREAMING = "streaming"  # 流式模式
    DISPATCHING = "dispatching"  # 分发模式
    ABTEST = "abtest"  # abtest模式


class DialogueCategory(int, Enum):
    """对话角色类型"""

    BOT = 0  # 机器
    USER = 1  # 用户
    SYSTEM = 2  # 系统消息
    ALL = -1  # 全部


class ModelType(int, Enum):
    """机器模型类别"""

    NORMAL = 0  # 普通模型
    MEMORY = 1  # 带记忆模型
    TASK_DIALOGUE = 2  # 任务对话模型
    ALL = -1  # 全部


class ModelSpeaker(str, Enum):
    """模型回复的角色"""

    BOT = "Bot"  # 希望得到机器模型的回复
    USER = "User"  # 希望得到用户模型的回复
    SYSTEM = "System"  # 系统消息，用于 context


class NeedCompare(int, Enum):
    """是否需要版本对比"""

    YES = 1  # 需要
    NO = 0  # 不需要
    ALL = -1  # 全部


class NeedAIQuickShow(int, Enum):
    """是否需要在AI快速任务展示"""

    YES = 1  # 需要
    NO = 0  # 不需要
    ALL = -1  # 全部


class RoleStatus(int, Enum):
    """模型状态"""

    ONLINE = 1  # 上线
    OFFLINE = 0  # 下线
    ALL = -1  # 全部

    @classmethod
    def status2config_repr(cls, status, config_switch="showAnnotation"):
        if str(status).isdigit():
            status = int(status)
        if status == cls.ONLINE:
            return {
                config_switch: True,
                "showPlatformEnv": configs["ai_model_env"]
            }
        elif status == cls.OFFLINE:
            return {
                "$or": [
                    {config_switch: False},
                    {"showPlatformEnv": {"$nin": [configs["ai_model_env"]]}}
                ]
            }
        return {}


class RoleConfigFile(str, Enum):
    """角色预设配置文件名"""

    ROLE = "role"  # 普通模型（机器）
    USER_ROLE = "user_role"  # 普通模型（用户）
    MEMORY_ROLE = "memory_role"  # 记忆模型（机器）
    USER_MEMORY_ROLE = "user_memory_role"  # 记忆模型（用户）
    COMPARE_ROLE = "compare_role"  # 版本对比（普通模型）
    MEMORY_COMPARE_ROLE = "memory_compare_role"  # 版本对比（记忆模型）


class QualityCheckResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class EvalResultEnum(str, Enum):
    SERIOUS = "严重问题"
    SUBTLE = "轻微问题"
    DEBATABLE = "有争议"
    JUST = "可用"


class TDEditMode(str, Enum):
    """训练数据编辑模式"""

    LIMIT = "limit"
    FREE = "free"


class DictTypeEnum(str, Enum):
    json = "json"
    pattern = "pattern"
    kv = "kv"
    query_gen = "query_gen"
    trie = "trie"
    keyword_tree = "keyword_tree"

    @classmethod
    def json_type(cls):
        return [cls.json, cls.query_gen, cls.trie]

    @classmethod
    def text_type(cls):
        return [cls.pattern, cls.kv, cls.keyword_tree]


class UploadProgress(int, Enum):
    FAILED = -1
    EXECUTING = 0
    SUCCESS = 1


class TaskStatus(str, Enum):
    ready = "ready"
    scheduled = "scheduled"
    executing = "executing"
    finished = "finished"
    failed = "failed"


class PressureTaskType(int, Enum):
    BY_TIME_DURATION = 1
    BY_SAMPLE_USAGE = 2


class PressureTaskRunMode(int, Enum):
    PARALLEL = 1
    SERIAL = 2


class QuantEvalTaskStatus(str, Enum):
    failed = "failed"
    processing = "processing"
    success = "success"
