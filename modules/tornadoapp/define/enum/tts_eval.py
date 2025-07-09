from enum import Enum


class MOSEvalTaskType(int, Enum):
    AUDIO = 1


class EvalTaskStatus(int, Enum):
    DOING = 0
    DONE = 1


