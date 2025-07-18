# coding=utf-8
"""
策略包初始化文件
"""

# 导入所有策略模块，确保装饰器生效
from . import demo_ma

# 导出策略注册表
from .registry import StrategyRegistry, get_registry, register_strategy, get_strategy

__all__ = [
    'StrategyRegistry',
    'get_registry', 
    'register_strategy',
    'get_strategy'
] 