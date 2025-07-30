# coding=utf-8
"""
比亚迪策略演示脚本
展示如何使用不同的比亚迪策略进行回测
"""

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


def create_demo_data():
    """创建演示数据"""
    logger.info("创建比亚迪演示数据...")
    
    # 生成日期范围
    dates = pd.date_range('2022-01-01', '2024-01-01', freq='D')
    dates = dates[dates.weekday < 5]  # 只保留工作日
    
    # 模拟比亚迪价格走势（包含趋势和波动）
    np.random.seed(42)
    base_price = 200
    
    # 添加趋势和周期性波动
    trend = np.linspace(0, 0.5, len(dates))  # 上升趋势
    cycle = 0.1 * np.sin(2 * np.pi * np.arange(len(dates)) / 252)  # 年度周期
    
    prices = [base_price]
    for i in range(1, len(dates)):
        # 随机波动 + 趋势 + 周期
        random_change = np.random.normal(0, 0.02)
        trend_change = trend[i] - trend[i-1]
        cycle_change = cycle[i] - cycle[i-1]
        
        total_change = random_change + trend_change + cycle_change
        new_price = prices[-1] * (1 + total_change)
        prices.append(max(new_price, 100))
    
    # 创建OHLCV数据
    data = []
    for i, (date, close_price) in enumerate(zip(dates, prices)):
        # 模拟OHLC数据
        high = close_price * (1 + abs(np.random.normal(0, 0.015)))
        low = close_price * (1 - abs(np.random.normal(0, 0.015)))
        open_price = prices[i-1] if i > 0 else close_price
        
        # 确保OHLC逻辑正确
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        # 模拟成交量
        price_change = abs(close_price - open_price) / open_price
        base_volume = 15000000  # 比亚迪基础成交量
        volume = base_volume * (1 + price_change * 5 + np.random.normal(0, 0.2))
        volume = max(volume, 5000000)
        
        data.append({
            'datetime': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    logger.info(f"演示数据创建完成: {len(df)} 条记录")
    logger.info(f"价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    return df


class DemoBYDStrategy(bt.Strategy):
    """演示用比亚迪策略"""
    
    params = (
        ('rsi_period', 14),
        ('ma_short', 5),
        ('ma_long', 20),
        ('stop_loss', 0.05),
        ('take_profit', 0.15),
    )
    
    def __init__(self):
        # 技术指标
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.sma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_short)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_long)
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        
        # 策略状态
        self.entry_price = None
        self.stop_loss_price = None
        self.take_profit_price = None
        
        logger.info("演示策略初始化完成")
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
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
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易完成: 毛利润 {trade.pnl:.2f}, 净利润 {trade.pnlcomm:.2f}')
    
    def next(self):
        if not self.position:
            # 买入条件：RSI超卖 + 均线金叉
            if self.rsi[0] < 30 and self.crossover > 0:
                self.log(f'买入信号: RSI={self.rsi[0]:.2f}, 价格={self.data.close[0]:.2f}')
                self.buy()
        else:
            # 卖出条件：RSI超买 + 均线死叉 + 止损止盈
            rsi_overbought = self.rsi[0] > 70
            ma_crossunder = self.crossover < 0
            stop_loss = self.data.close[0] < self.stop_loss_price if self.stop_loss_price else False
            take_profit = self.data.close[0] > self.take_profit_price if self.take_profit_price else False
            
            if rsi_overbought or ma_crossunder or stop_loss or take_profit:
                self.log(f'卖出信号: RSI={self.rsi[0]:.2f}, 价格={self.data.close[0]:.2f}')
                self.sell()


def run_demo_backtest():
    """运行演示回测"""
    logger.info("开始比亚迪策略演示回测...")
    
    # 创建数据
    df = create_demo_data()
    
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(commission=0.001)
    
    # 添加数据
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data, name='BYD')
    
    # 添加策略
    cerebro.addstrategy(DemoBYDStrategy)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # 运行回测
    logger.info("运行回测...")
    results = cerebro.run()
    result = results[0]
    
    # 分析结果
    initial_value = cerebro.broker.startingcash
    final_value = cerebro.broker.getvalue()
    total_return = (final_value - initial_value) / initial_value
    
    # 计算年化收益率
    days = (df.index[-1] - df.index[0]).days
    annual_return = (1 + total_return) ** (365 / days) - 1
    
    # 获取分析器结果
    sharpe = result.analyzers.sharpe.get_analysis()
    drawdown = result.analyzers.drawdown.get_analysis()
    trades = result.analyzers.trades.get_analysis()
    
    # 交易统计
    total_trades = trades.get('total', {}).get('total', 0)
    won_trades = trades.get('won', {}).get('total', 0)
    lost_trades = trades.get('lost', {}).get('total', 0)
    win_rate = won_trades / total_trades if total_trades > 0 else 0
    
    # 打印结果
    print("\n" + "="*60)
    print("比亚迪策略演示回测结果")
    print("="*60)
    print(f"股票代码: 002594.SZ (比亚迪)")
    print(f"回测期间: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"初始资金: {initial_value:,.0f} 元")
    print(f"最终资金: {final_value:,.0f} 元")
    print(f"总收益率: {total_return:.2%}")
    print(f"年化收益率: {annual_return:.2%}")
    print(f"夏普比率: {sharpe.get('sharperatio', 0):.2f}")
    print(f"最大回撤: {drawdown.get('max', {}).get('drawdown', 0):.2%}")
    print(f"总交易次数: {total_trades}")
    print(f"盈利交易: {won_trades}")
    print(f"亏损交易: {lost_trades}")
    print(f"胜率: {win_rate:.1%}")
    print("="*60)
    
    # 绘制结果
    try:
        cerebro.plot(style='candle', filename='byd_demo_results.png')
        logger.info("图表已保存到: byd_demo_results.png")
    except Exception as e:
        logger.warning(f"绘制图表失败: {e}")
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe.get('sharperatio', 0),
        'max_drawdown': drawdown.get('max', {}).get('drawdown', 0),
        'total_trades': total_trades,
        'win_rate': win_rate
    }


def show_strategy_info():
    """显示策略信息"""
    print("\n" + "="*60)
    print("比亚迪策略说明")
    print("="*60)
    print("策略特点:")
    print("- 结合RSI和移动平均线指标")
    print("- 设置止损止盈机制")
    print("- 适合比亚迪股票的高波动特征")
    print()
    print("买入条件:")
    print("- RSI < 30 (超卖)")
    print("- 短期均线上穿长期均线 (金叉)")
    print()
    print("卖出条件:")
    print("- RSI > 70 (超买)")
    print("- 短期均线下穿长期均线 (死叉)")
    print("- 止损: -5%")
    print("- 止盈: +15%")
    print()
    print("风险提示:")
    print("- 本演示使用模拟数据")
    print("- 历史回测结果不代表未来表现")
    print("- 投资有风险，入市需谨慎")
    print("="*60)


def main():
    """主函数"""
    logger.info("开始比亚迪策略演示")
    
    try:
        # 显示策略信息
        show_strategy_info()
        
        # 运行演示回测
        result = run_demo_backtest()
        
        # 策略建议
        print("\n策略建议:")
        if result['sharpe_ratio'] > 1.0:
            print("✓ 策略表现良好，夏普比率较高")
        else:
            print("⚠ 策略表现一般，建议优化参数")
        
        if result['win_rate'] > 0.5:
            print("✓ 胜率较高，策略较为稳定")
        else:
            print("⚠ 胜率较低，建议调整买卖条件")
        
        if result['max_drawdown'] < 0.1:
            print("✓ 最大回撤较小，风险控制良好")
        else:
            print("⚠ 最大回撤较大，建议加强风险控制")
        
        logger.info("比亚迪策略演示完成!")
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 