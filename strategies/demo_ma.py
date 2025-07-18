# coding=utf-8
import pandas as pd
from typing import Dict, Any

from .base import BaseStrategy
from .registry import register_strategy


@register_strategy
class MAStrategy(BaseStrategy):
    """移动平均线策略"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.short_window = kwargs.get('short', 5)
        self.long_window = kwargs.get('long', 20)
        self.prices = {}  # symbol -> price_history
    
    def on_bar(self, bar: Dict[str, Any], account_id: str) -> int:
        """
        K线数据处理
        
        Args:
            bar: K线数据，包含 symbol, open, high, low, close, volume 等字段
            account_id: 账户ID
            
        Returns:
            int: 交易信号 (1: 买入, -1: 卖出, 0: 无信号)
        """
        symbol = bar['symbol']
        close_price = bar['close']
        
        # 初始化价格历史
        if symbol not in self.prices:
            self.prices[symbol] = []
        
        # 添加最新价格
        self.prices[symbol].append(close_price)
        
        # 保持历史数据长度
        max_length = max(self.short_window, self.long_window) + 10
        if len(self.prices[symbol]) > max_length:
            self.prices[symbol] = self.prices[symbol][-max_length:]
        
        # 检查是否有足够的数据
        if len(self.prices[symbol]) < self.long_window:
            return 0
        
        # 计算移动平均线
        short_ma = pd.Series(self.prices[symbol][-self.short_window:]).mean()
        long_ma = pd.Series(self.prices[symbol][-self.long_window:]).mean()
        
        # 生成交易信号
        if short_ma > long_ma:
            self.logger.debug(f"{symbol} 买入信号: 短期均线({short_ma:.2f}) > 长期均线({long_ma:.2f})")
            return 1  # 买入信号
        elif short_ma < long_ma:
            self.logger.debug(f"{symbol} 卖出信号: 短期均线({short_ma:.2f}) < 长期均线({long_ma:.2f})")
            return -1  # 卖出信号
        else:
            return 0  # 无信号
    
    def get_interval(self) -> int:
        """获取策略执行间隔（秒）"""
        return 60  # 每分钟执行一次
    
    def get_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'short': self.short_window,
            'long': self.long_window,
            'name': self.name
        } 