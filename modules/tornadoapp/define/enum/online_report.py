from enum import Enum


class TimeGroupingUnit(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class BeforeVote(str, Enum):
    UP = "1"
    NONE = "2"
    DOWN = "3"
