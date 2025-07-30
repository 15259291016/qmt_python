# coding=utf-8
"""
Backtrader 策略基类
提供统一的策略接口，兼容原有的策略结构
"""

import backtrader as bt
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BacktraderStrategyBase(bt.Strategy, ABC):
    """Backtrader 策略基类"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.name = kwargs.get('name', self.__class__.__name__)
        self.params = kwargs
        self.logger = logging.getLogger(f"BacktraderStrategy.{self.name}")
        
        # 策略状态
        self.position_size = 0
        self.last_signal = 0
        
        # 初始化策略
        self.initialize()
    
    def initialize(self):
        """策略初始化，子类可以重写"""
        self.logger.info(f"策略 {self.name} 初始化完成")
    
    def log(self, txt: str, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        self.logger.info(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: {order.executed.price:.2f}')
            else:
                self.log(f'卖出执行: {order.executed.price:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')
    
    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        
        self.log(f'交易利润: 毛利润 {trade.pnl:.2f}, 净利润 {trade.pnlcomm:.2f}')
    
    def next(self):
        """主要策略逻辑，子类必须实现"""
        # 获取当前数据
        data = self.datas[0]
        
        # 检查是否有持仓
        if not self.position:
            # 无持仓时的逻辑
            signal = self.generate_buy_signal(data)
            if signal:
                self.buy()
                self.log(f'买入信号: {signal}')
        else:
            # 有持仓时的逻辑
            signal = self.generate_sell_signal(data)
            if signal:
                self.sell()
                self.log(f'卖出信号: {signal}')
    
    @abstractmethod
    def generate_buy_signal(self, data) -> bool:
        """生成买入信号，子类必须实现"""
        pass
    
    @abstractmethod
    def generate_sell_signal(self, data) -> bool:
        """生成卖出信号，子类必须实现"""
        pass
    
    def get_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        return self.params
    
    def on_start(self):
        """策略启动时调用"""
        self.logger.info(f"策略 {self.name} 启动")
    
    def on_stop(self):
        """策略停止时调用"""
        self.logger.info(f"策略 {self.name} 停止")


class MAStrategy(BacktraderStrategyBase):
    """移动平均线策略"""
    
    params = (
        ('short_window', 5),
        ('long_window', 20),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 计算移动平均线
        self.sma_short = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_window
        )
        self.sma_long = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_window
        )
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
    
    def generate_buy_signal(self, data) -> bool:
        """生成买入信号"""
        return self.crossover > 0
    
    def generate_sell_signal(self, data) -> bool:
        """生成卖出信号"""
        return self.crossover < 0


class RSIStrategy(BacktraderStrategyBase):
    """RSI 策略"""
    
    params = (
        ('rsi_period', 14),
        ('oversold', 30),
        ('overbought', 70),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # RSI 指标
        self.rsi = bt.indicators.RSI(
            self.data.close, period=self.params.rsi_period
        )
    
    def generate_buy_signal(self, data) -> bool:
        """生成买入信号"""
        return self.rsi < self.params.oversold
    
    def generate_sell_signal(self, data) -> bool:
        """生成卖出信号"""
        return self.rsi > self.params.overbought


class MACDStrategy(BacktraderStrategyBase):
    """MACD 策略"""
    
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # MACD 指标
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )
    
    def generate_buy_signal(self, data) -> bool:
        """生成买入信号"""
        return self.macd.macd > self.macd.signal
    
    def generate_sell_signal(self, data) -> bool:
        """生成卖出信号"""
        return self.macd.macd < self.macd.signal


class BollingerBandsStrategy(BacktraderStrategyBase):
    """布林带策略"""
    
    params = (
        ('bb_period', 20),
        ('bb_dev', 2),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 布林带指标
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )
    
    def generate_buy_signal(self, data) -> bool:
        """生成买入信号"""
        return self.data.close < self.bb.lines.bot
    
    def generate_sell_signal(self, data) -> bool:
        """生成卖出信号"""
        return self.data.close > self.bb.lines.top 