from enum import Enum


class EvalTaskStatus(int, Enum):
    GENERATION_FAILED = -2
    GENERATING = -1
    EVALUATING = 0
    INSPECTING = 1
    FINISHED = 2

class EvalDetailStatus(int, Enum):
    EVALUATING = 0
    EVALUATED = 1


class EvalTaskType(int, Enum):
    SINGLE = 1     # 单独测评
    MULTI = 2     # （两个模型）对比测评


class TemplateType(int, Enum):
    EVALUATION = 1
    INSPECTION = 2


class DatasetsDivision(int, Enum):
    ALL = 1         # 全量测评
    MEAN = 2        # 均分测评
