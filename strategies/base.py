# coding=utf-8
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BaseStrategy:
    """策略基类"""
    
    def __init__(self, **kwargs):
        """初始化策略"""
        self.name = kwargs.get('name', self.__class__.__name__)
        self.params = kwargs
        self.logger = logging.getLogger(f"Strategy.{self.name}")
    
    def on_bar(self, bar: Dict[str, Any], account_id: str) -> int:
        """
        K线数据处理
        
        Args:
            bar: K线数据，包含 symbol, open, high, low, close, volume 等字段
            account_id: 账户ID
            
        Returns:
            int: 交易信号 (1: 买入, -1: 卖出, 0: 无信号)
        """
        raise NotImplementedError("子类必须实现 on_bar 方法")
    
    def on_tick(self, tick: Dict[str, Any], account_id: str):
        """
        Tick数据处理
        
        Args:
            tick: Tick数据
            account_id: 账户ID
        """
        pass
    
    def on_order(self, order: Dict[str, Any], account_id: str):
        """
        订单状态更新
        
        Args:
            order: 订单信息
            account_id: 账户ID
        """
        pass
    
    def get_interval(self) -> int:
        """
        获取策略执行间隔（秒）
        
        Returns:
            int: 执行间隔，默认60秒
        """
        return 60
    
    def get_params(self) -> Dict[str, Any]:
        """
        获取策略参数
        
        Returns:
            Dict: 策略参数字典
        """
        return self.params
    
    def initialize(self):
        """策略初始化"""
        self.logger.info(f"策略 {self.name} 初始化完成")
    
    def on_start(self):
        """策略启动时调用"""
        self.logger.info(f"策略 {self.name} 启动")
    
    def on_stop(self):
        """策略停止时调用"""
        self.logger.info(f"策略 {self.name} 停止")
    
    def on_error(self, error: Exception):
        """策略错误处理"""
        self.logger.error(f"策略 {self.name} 发生错误: {error}") 