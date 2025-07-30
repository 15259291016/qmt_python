#!/usr/bin/env python
# -*- coding: utf-8 -*-

# coding=utf-8
"""
简单的比亚迪策略测试
"""

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("开始测试比亚迪策略...")

# 创建简单的模拟数据
def create_simple_data():
    """创建简单的模拟数据"""
    print("创建模拟数据...")
    
    # 生成日期
    dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')
    dates = dates[dates.weekday < 5]  # 只保留工作日
    
    # 生成价格
    np.random.seed(42)
    base_price = 200
    prices = [base_price]
    
    for i in range(1, len(dates)):
        # 简单的价格变化
        change = np.random.normal(0, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 100))
    
    # 创建DataFrame
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        high = price * 1.02
        low = price * 0.98
        open_price = prices[i-1] if i > 0 else price
        volume = np.random.randint(1000000, 10000000)
        
        data.append({
            'datetime': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    print(f"数据创建完成: {len(df)} 条记录")
    return df

# 简单的比亚迪策略
class SimpleBYDStrategy(bt.Strategy):
    """简单的比亚迪策略"""
    
    params = (
        ('rsi_period', 14),
        ('ma_short', 5),
        ('ma_long', 20),
    )
    
    def __init__(self):
        print("初始化策略...")
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.sma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_short)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_long)
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        print("策略初始化完成")
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: {order.executed.price:.2f}')
            else:
                self.log(f'卖出执行: {order.executed.price:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')
        
        self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        
        self.log(f'交易完成: 毛利润 {trade.pnl:.2f}, 净利润 {trade.pnlcomm:.2f}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # 买入条件：RSI < 30 且 短期均线上穿长期均线
            if self.rsi[0] < 30 and self.crossover > 0:
                self.log(f'买入信号: RSI={self.rsi[0]:.2f}, 价格={self.data.close[0]:.2f}')
                self.order = self.buy()
        else:
            # 卖出条件：RSI > 70 或 短期均线下穿长期均线
            if self.rsi[0] > 70 or self.crossover < 0:
                self.log(f'卖出信号: RSI={self.rsi[0]:.2f}, 价格={self.data.close[0]:.2f}')
                self.order = self.sell()

def run_simple_backtest():
    """运行简单回测"""
    print("开始运行简单回测...")
    
    # 创建数据
    df = create_simple_data()
    
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.001)
    
    # 添加数据
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    
    # 添加策略
    cerebro.addstrategy(SimpleBYDStrategy)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # 运行回测
    print("运行回测...")
    results = cerebro.run()
    result = results[0]
    
    # 分析结果
    initial_value = cerebro.broker.startingcash
    final_value = cerebro.broker.getvalue()
    total_return = (final_value - initial_value) / initial_value
    
    print("\n" + "="*50)
    print("回测结果")
    print("="*50)
    print(f"初始资金: {initial_value:,.2f}")
    print(f"最终资金: {final_value:,.2f}")
    print(f"总收益率: {total_return:.2%}")
    
    # 获取分析器结果
    sharpe = result.analyzers.sharpe.get_analysis()
    drawdown = result.analyzers.drawdown.get_analysis()
    trades = result.analyzers.trades.get_analysis()
    
    print(f"夏普比率: {sharpe.get('sharperatio', 0):.2f}")
    print(f"最大回撤: {drawdown.get('max', {}).get('drawdown', 0):.2%}")
    print(f"总交易次数: {trades.get('total', {}).get('total', 0)}")
    
    print("="*50)
    print("回测完成!")

if __name__ == "__main__":
    try:
        run_simple_backtest()
    except Exception as e:
        print(f"回测失败: {e}")
        import traceback
        traceback.print_exc() 