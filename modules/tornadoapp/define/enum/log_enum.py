from enum import Enum


class LogLevel(str, Enum):
    INFO = "INFO"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    WARNING = "WARNING"
    EXCEPTION = "EXCEPTION"
