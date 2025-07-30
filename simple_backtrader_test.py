# coding=utf-8
"""
简单的 Backtrader 测试脚本
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_backtrader_import():
    """测试 Backtrader 导入"""
    try:
        import backtrader as bt
        print("✓ Backtrader 导入成功")
        return True
    except ImportError as e:
        print(f"✗ Backtrader 导入失败: {e}")
        return False


def create_test_data():
    """创建测试数据"""
    # 生成模拟股票数据
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    
    # 模拟价格数据
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = [base_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    # 创建OHLCV数据
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
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
    
    # 保存为CSV
    df.to_csv('test_data.csv')
    print(f"✓ 测试数据创建完成: {len(df)} 条记录")
    return df


def test_simple_backtest():
    """测试简单回测"""
    try:
        import backtrader as bt
        
        # 创建测试数据
        df = create_test_data()
        
        # 创建 Cerebro 引擎
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(1000000)
        cerebro.broker.setcommission(commission=0.001)
        
        # 添加数据
        data = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data)
        
        # 添加简单策略
        class SimpleStrategy(bt.Strategy):
            def __init__(self):
                self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=20)
            
            def next(self):
                if not self.position:
                    if self.data.close[0] > self.sma[0]:
                        self.buy()
                else:
                    if self.data.close[0] < self.sma[0]:
                        self.sell()
        
        cerebro.addstrategy(SimpleStrategy)
        
        # 运行回测
        print("开始运行回测...")
        initial_value = cerebro.broker.getvalue()
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        print(f"✓ 回测完成")
        print(f"  初始资金: {initial_value:,.2f}")
        print(f"  最终资金: {final_value:,.2f}")
        print(f"  收益率: {((final_value - initial_value) / initial_value):.2%}")
        
        return True
        
    except Exception as e:
        print(f"✗ 简单回测失败: {e}")
        return False


def main():
    """主函数"""
    print("开始 Backtrader 简单测试")
    print("=" * 50)
    
    # 测试导入
    if not test_backtrader_import():
        print("Backtrader 导入失败，请检查安装")
        return
    
    # 测试简单回测
    if test_simple_backtest():
        print("\n🎉 Backtrader 框架工作正常！")
    else:
        print("\n⚠ Backtrader 框架测试失败")


if __name__ == "__main__":
    main() 