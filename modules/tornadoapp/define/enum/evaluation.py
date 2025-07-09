#!/usr/bin python
# -*- encoding: utf-8 -*-
'''
@File    :   evaluation.py
@Time    :   2024/03/05 16:41:14
@Author  :   v_baojzhang
@Version :   1.0
@Contact :   v_baojzhang@tencent.com
@Desc    :   新测评流程相关枚举类
'''

# here put the import lib
from enum import Enum


class EvaluationType(Enum):
    """测评类型：单独测评、对比测评"""
    SOLO = 1
    COMP = 2


class EvaluationTaskStatus(Enum):
    """任务生成状态"""
    GENNing = 0     # 数据生成中
    EVALING = 1     # 测评中
    FINISHED = 2    # 已完成
    ERROR = -1      # 错误

class EvaluationStatus(Enum):
    """测评状态"""
    EVALING = 0     # 待测评
    INSPECTING = 1  # 待质检
    FINISHED = 2    # 已完成


class DataCollectionStatus(Enum):
    """数据集case"""
    GOODCASE = 1
    BADCASE = 2