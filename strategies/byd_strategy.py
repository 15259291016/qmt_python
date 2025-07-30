# coding=utf-8
"""
比亚迪（002594.SZ）专用策略
结合技术指标和基本面分析
"""

import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BYDStrategy(bt.Strategy):
    """比亚迪专用策略"""
    
    params = (
        ('rsi_period', 14),        # RSI 周期
        ('rsi_oversold', 30),      # RSI 超卖阈值
        ('rsi_overbought', 70),    # RSI 超买阈值
        ('ma_short', 5),           # 短期均线
        ('ma_long', 20),           # 长期均线
        ('bb_period', 20),         # 布林带周期
        ('bb_dev', 2),             # 布林带标准差倍数
        ('volume_ma_period', 10),  # 成交量均线周期
        ('stop_loss', 0.05),       # 止损比例
        ('take_profit', 0.15),     # 止盈比例
    )
    
    def __init__(self):
        """初始化策略"""
        super().__init__()
        
        # 技术指标
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.sma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_short)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_long)
        self.bb = bt.indicators.BollingerBands(self.data.close, period=self.params.bb_period, devfactor=self.params.bb_dev)
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.volume_ma_period)
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        
        # 策略状态
        self.entry_price = None
        self.stop_loss_price = None
        self.take_profit_price = None
        
        # 统计信息
        self.trade_count = 0
        self.win_count = 0
        self.total_profit = 0
        
        logger.info("比亚迪策略初始化完成")
    
    def log(self, txt: str, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: {order.executed.price:.2f}, 数量: {order.executed.size}')
                self.entry_price = order.executed.price
                self.stop_loss_price = self.entry_price * (1 - self.params.stop_loss)
                self.take_profit_price = self.entry_price * (1 + self.params.take_profit)
            else:
                self.log(f'卖出执行: {order.executed.price:.2f}, 数量: {order.executed.size}')
                if self.entry_price:
                    profit = (order.executed.price - self.entry_price) / self.entry_price
                    self.total_profit += profit
                    if profit > 0:
                        self.win_count += 1
                    self.trade_count += 1
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')
    
    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        
        self.log(f'交易完成: 毛利润 {trade.pnl:.2f}, 净利润 {trade.pnlcomm:.2f}')
    
    def generate_buy_signal(self) -> bool:
        """生成买入信号"""
        # 1. RSI 超卖信号
        rsi_oversold = self.rsi[0] < self.params.rsi_oversold
        
        # 2. 均线金叉信号
        ma_crossover = self.crossover > 0
        
        # 3. 布林带下轨支撑
        bb_support = self.data.close[0] < self.bb.lines.bot[0]
        
        # 4. 成交量放大
        volume_surge = self.data.volume[0] > self.volume_ma[0] * 1.5
        
        # 综合信号：至少满足2个条件
        signals = [rsi_oversold, ma_crossover, bb_support, volume_surge]
        signal_count = sum(signals)
        
        return signal_count >= 2
    
    def generate_sell_signal(self) -> bool:
        """生成卖出信号"""
        # 1. RSI 超买信号
        rsi_overbought = self.rsi[0] > self.params.rsi_overbought
        
        # 2. 均线死叉信号
        ma_crossunder = self.crossover < 0
        
        # 3. 布林带上轨压力
        bb_resistance = self.data.close[0] > self.bb.lines.top[0]
        
        # 4. 止损信号
        stop_loss = self.data.close[0] < self.stop_loss_price if self.stop_loss_price else False
        
        # 5. 止盈信号
        take_profit = self.data.close[0] > self.take_profit_price if self.take_profit_price else False
        
        # 综合信号：满足任一条件
        signals = [rsi_overbought, ma_crossunder, bb_resistance, stop_loss, take_profit]
        
        return any(signals)
    
    def next(self):
        """主要策略逻辑"""
        # 检查是否有持仓
        if not self.position:
            # 无持仓时的买入逻辑
            if self.generate_buy_signal():
                self.buy()
                self.log(f'买入信号: RSI={self.rsi[0]:.2f}, 价格={self.data.close[0]:.2f}')
        else:
            # 有持仓时的卖出逻辑
            if self.generate_sell_signal():
                self.sell()
                self.log(f'卖出信号: RSI={self.rsi[0]:.2f}, 价格={self.data.close[0]:.2f}')
    
    def on_stop(self):
        """策略停止时调用"""
        if self.trade_count > 0:
            win_rate = self.win_count / self.trade_count
            avg_profit = self.total_profit / self.trade_count
            self.log(f'策略统计: 总交易{self.trade_count}次, 胜率{win_rate:.2%}, 平均收益{avg_profit:.2%}')


class BYDEnhancedStrategy(bt.Strategy):
    """比亚迪增强策略 - 结合更多指标"""
    
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('bb_period', 20),
        ('bb_dev', 2),
        ('atr_period', 14),
        ('stop_loss_atr', 2),
        ('take_profit_atr', 4),
    )
    
    def __init__(self):
        """初始化增强策略"""
        super().__init__()
        
        # 技术指标
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        # 策略状态
        self.entry_price = None
        self.stop_loss_price = None
        self.take_profit_price = None
        
        logger.info("比亚迪增强策略初始化完成")
    
    def log(self, txt: str, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: {order.executed.price:.2f}')
                self.entry_price = order.executed.price
                # 基于ATR的动态止损止盈
                atr_value = self.atr[0]
                self.stop_loss_price = self.entry_price - (atr_value * self.params.stop_loss_atr)
                self.take_profit_price = self.entry_price + (atr_value * self.params.take_profit_atr)
            else:
                self.log(f'卖出执行: {order.executed.price:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')
    
    def generate_buy_signal(self) -> bool:
        """生成买入信号"""
        # 1. RSI 超卖
        rsi_oversold = self.rsi[0] < self.params.rsi_oversold
        
        # 2. MACD 金叉
        macd_crossover = self.macd.macd[0] > self.macd.signal[0] and self.macd.macd[-1] <= self.macd.signal[-1]
        
        # 3. 布林带下轨支撑
        bb_support = self.data.close[0] < self.bb.lines.bot[0]
        
        # 4. 价格在布林带中轨以下
        below_middle = self.data.close[0] < self.bb.lines.mid[0]
        
        # 综合信号
        signals = [rsi_oversold, macd_crossover, bb_support, below_middle]
        signal_count = sum(signals)
        
        return signal_count >= 3
    
    def generate_sell_signal(self) -> bool:
        """生成卖出信号"""
        # 1. RSI 超买
        rsi_overbought = self.rsi[0] > self.params.rsi_overbought
        
        # 2. MACD 死叉
        macd_crossunder = self.macd.macd[0] < self.macd.signal[0] and self.macd.macd[-1] >= self.macd.signal[-1]
        
        # 3. 布林带上轨压力
        bb_resistance = self.data.close[0] > self.bb.lines.top[0]
        
        # 4. 止损信号
        stop_loss = self.data.close[0] < self.stop_loss_price if self.stop_loss_price else False
        
        # 5. 止盈信号
        take_profit = self.data.close[0] > self.take_profit_price if self.take_profit_price else False
        
        # 综合信号
        signals = [rsi_overbought, macd_crossunder, bb_resistance, stop_loss, take_profit]
        
        return any(signals)
    
    def next(self):
        """主要策略逻辑"""
        if not self.position:
            if self.generate_buy_signal():
                self.buy()
                self.log(f'买入信号: RSI={self.rsi[0]:.2f}, MACD={self.macd.macd[0]:.4f}')
        else:
            if self.generate_sell_signal():
                self.sell()
                self.log(f'卖出信号: RSI={self.rsi[0]:.2f}, MACD={self.macd.macd[0]:.4f}')


class BYDConservativeStrategy(bt.Strategy):
    """比亚迪保守策略 - 适合稳健投资"""
    
    params = (
        ('ma_short', 10),
        ('ma_long', 50),
        ('rsi_period', 21),
        ('rsi_oversold', 25),
        ('rsi_overbought', 75),
        ('volume_ma_period', 20),
        ('stop_loss', 0.08),
        ('take_profit', 0.20),
    )
    
    def __init__(self):
        """初始化保守策略"""
        super().__init__()
        
        # 技术指标
        self.sma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_short)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_long)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.volume_ma_period)
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        
        # 策略状态
        self.entry_price = None
        self.stop_loss_price = None
        self.take_profit_price = None
        
        logger.info("比亚迪保守策略初始化完成")
    
    def log(self, txt: str, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: {order.executed.price:.2f}')
                self.entry_price = order.executed.price
                self.stop_loss_price = self.entry_price * (1 - self.params.stop_loss)
                self.take_profit_price = self.entry_price * (1 + self.params.take_profit)
            else:
                self.log(f'卖出执行: {order.executed.price:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')
    
    def generate_buy_signal(self) -> bool:
        """生成买入信号"""
        # 1. 均线金叉
        ma_crossover = self.crossover > 0
        
        # 2. RSI 超卖
        rsi_oversold = self.rsi[0] < self.params.rsi_oversold
        
        # 3. 价格在长期均线之上
        above_long_ma = self.data.close[0] > self.sma_long[0]
        
        # 4. 成交量确认
        volume_confirm = self.data.volume[0] > self.volume_ma[0]
        
        # 保守策略：需要满足大部分条件
        signals = [ma_crossover, rsi_oversold, above_long_ma, volume_confirm]
        signal_count = sum(signals)
        
        return signal_count >= 3
    
    def generate_sell_signal(self) -> bool:
        """生成卖出信号"""
        # 1. 均线死叉
        ma_crossunder = self.crossover < 0
        
        # 2. RSI 超买
        rsi_overbought = self.rsi[0] > self.params.rsi_overbought
        
        # 3. 止损信号
        stop_loss = self.data.close[0] < self.stop_loss_price if self.stop_loss_price else False
        
        # 4. 止盈信号
        take_profit = self.data.close[0] > self.take_profit_price if self.take_profit_price else False
        
        # 保守策略：满足任一条件即可卖出
        signals = [ma_crossunder, rsi_overbought, stop_loss, take_profit]
        
        return any(signals)
    
    def next(self):
        """主要策略逻辑"""
        if not self.position:
            if self.generate_buy_signal():
                self.buy()
                self.log(f'买入信号: RSI={self.rsi[0]:.2f}, 价格={self.data.close[0]:.2f}')
        else:
            if self.generate_sell_signal():
                self.sell()
                self.log(f'卖出信号: RSI={self.rsi[0]:.2f}, 价格={self.data.close[0]:.2f}') 