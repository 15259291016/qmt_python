# coding=utf-8
import logging
from typing import Dict, Type, Optional

from .base import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """策略注册表"""
    
    def __init__(self):
        self._strategies: Dict[str, Type[BaseStrategy]] = {}
    
    def register_strategy(self, name: str, strategy_class: Type[BaseStrategy]):
        """注册策略"""
        self._strategies[name] = strategy_class
        logger.info(f"策略 {name} 已注册")
    
    def get_strategy(self, name: str) -> Optional[Type[BaseStrategy]]:
        """获取策略类"""
        return self._strategies.get(name)
    
    def list_strategies(self) -> list:
        """列出所有已注册的策略"""
        return list(self._strategies.keys())
    
    def unregister_strategy(self, name: str):
        """注销策略"""
        if name in self._strategies:
            del self._strategies[name]
            logger.info(f"策略 {name} 已注销")


# 全局策略注册表实例
_registry = StrategyRegistry()


def register_strategy(cls):
    """装饰器：注册策略类"""
    _registry.register_strategy(cls.__name__, cls)
    return cls


def get_strategy(name: str) -> Optional[Type[BaseStrategy]]:
    """获取策略类"""
    return _registry.get_strategy(name)


def get_registry() -> StrategyRegistry:
    """获取策略注册表实例"""
    return _registry


# 兼容旧版本的函数
STRATEGY_REGISTRY = _registry._strategies 