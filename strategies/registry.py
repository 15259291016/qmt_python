# coding=utf-8
import logging
from typing import Dict, Type, Optional

from .base import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """策略注册表"""
    def __init__(self):
        self._strategies: Dict[str, Type] = {}
        self._bt_strategies: Dict[str, Type] = {}
        self._custom_strategies: Dict[str, Type] = {}

    def register_strategy(self, name: str, strategy_class: Type):
        """注册策略"""
        self._strategies[name] = strategy_class
        # 判断是否为Backtrader策略
        import backtrader as bt
        if issubclass(strategy_class, bt.Strategy):
            self._bt_strategies[name] = strategy_class
        else:
            self._custom_strategies[name] = strategy_class
        logger.info(f"策略 {name} 已注册，类型: {'Backtrader' if name in self._bt_strategies else '自定义'}")

    def get_strategy(self, name: str) -> Optional[Type]:
        return self._strategies.get(name)

    def get_bt_strategy(self, name: str) -> Optional[Type]:
        return self._bt_strategies.get(name)

    def get_custom_strategy(self, name: str) -> Optional[Type]:
        return self._custom_strategies.get(name)

    def list_strategies(self) -> list:
        return list(self._strategies.keys())

    def list_bt_strategies(self) -> list:
        return list(self._bt_strategies.keys())

    def list_custom_strategies(self) -> list:
        return list(self._custom_strategies.keys())

    def unregister_strategy(self, name: str):
        if name in self._strategies:
            del self._strategies[name]
        if name in self._bt_strategies:
            del self._bt_strategies[name]
        if name in self._custom_strategies:
            del self._custom_strategies[name]
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