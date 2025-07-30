# Backtrader 回测框架迁移指南

## 概述

本项目已成功从自研回测框架迁移到 **Backtrader** 框架。Backtrader 是一个功能强大的 Python 回测框架，具有以下优势：

- ✅ **成熟稳定** - 经过大量用户验证
- ✅ **功能丰富** - 内置多种技术指标和分析器
- ✅ **易于使用** - 简洁的 API 设计
- ✅ **高度可扩展** - 支持自定义指标和策略
- ✅ **可视化支持** - 内置图表绘制功能

## 新框架架构

### 1. 核心模块

```
modules/backtrader_engine/
├── __init__.py              # 模块初始化
├── strategy_base.py         # 策略基类
├── data_feed.py            # 数据源适配器
├── backtest_engine.py      # 回测引擎
└── results_analyzer.py     # 结果分析器
```

### 2. 主要组件

#### 策略基类 (`strategy_base.py`)
```python
from modules.backtrader_engine.strategy_base import BacktraderStrategyBase

class MyStrategy(BacktraderStrategyBase):
    def generate_buy_signal(self, data) -> bool:
        # 实现买入信号逻辑
        pass
    
    def generate_sell_signal(self, data) -> bool:
        # 实现卖出信号逻辑
        pass
```

#### 数据源适配器 (`data_feed.py`)
```python
from modules.backtrader_engine.data_feed import TushareDataFeed, CSVDataFeed

# Tushare 数据源
data_feed = TushareDataFeed(
    symbol='000001.SZ',
    start_date='20230101',
    end_date='20231231',
    tushare_token='your_token'
)

# CSV 数据源
csv_feed = CSVDataFeed('data/stock_data.csv')
```

#### 回测引擎 (`backtest_engine.py`)
```python
from modules.backtrader_engine.backtest_engine import BacktraderEngine

engine = BacktraderEngine(
    initial_cash=1000000,
    commission=0.001
)

engine.add_data(data_feed)
engine.add_strategy(MyStrategy)
result = engine.run_backtest()
```

## 使用方法

### 1. 单策略回测

```python
from modules.backtrader_engine import (
    BacktraderEngine, TushareDataFeed, MAStrategy
)

# 创建数据源
data_feed = TushareDataFeed(
    symbol='000001.SZ',
    start_date='20230101',
    end_date='20231231',
    tushare_token='your_token'
)

# 创建回测引擎
engine = BacktraderEngine(
    initial_cash=1000000,
    commission=0.001
)

# 添加数据和策略
engine.add_data(data_feed, name='000001.SZ')
engine.add_strategy(MAStrategy, strategy_name='MA_Strategy')

# 运行回测
result = engine.run_backtest('MA_Strategy')

# 生成报告
report = engine.generate_report()
print(report)

# 绘制结果
engine.plot_results(filename='results.png')

# 保存结果
engine.save_results('results.json')
```

### 2. 多策略回测

```python
from modules.backtrader_engine import MultiStrategyBacktestEngine

# 创建多策略回测引擎
multi_engine = MultiStrategyBacktestEngine(
    initial_cash=1000000,
    commission=0.001
)

# 添加多个策略
strategy_configs = [
    {
        'symbol': '000001.SZ',
        'strategy_class': MAStrategy,
        'strategy_name': 'MA_Strategy_000001',
        'strategy_params': {'short_window': 5, 'long_window': 20}
    },
    {
        'symbol': '000002.SZ',
        'strategy_class': RSIStrategy,
        'strategy_name': 'RSI_Strategy_000002',
        'strategy_params': {'rsi_period': 14, 'oversold': 30, 'overbought': 70}
    }
]

# 添加策略回测
for config in strategy_configs:
    data_feed = TushareDataFeed(
        symbol=config['symbol'],
        start_date='20230101',
        end_date='20231231',
        tushare_token='your_token'
    )
    
    multi_engine.add_strategy_backtest(
        strategy_name=config['strategy_name'],
        strategy_class=config['strategy_class'],
        data_feed=data_feed,
        **config['strategy_params']
    )

# 运行所有回测
results = multi_engine.run_all_backtests()

# 生成综合报告
report = multi_engine.generate_comprehensive_report()
print(report)

# 绘制所有结果
multi_engine.plot_all_results('multi_strategy_plots')

# 保存所有结果
multi_engine.save_all_results('multi_strategy_results.json')
```

### 3. 参数优化

```python
# 参数组合
param_combinations = [
    {'short_window': 5, 'long_window': 10},
    {'short_window': 5, 'long_window': 20},
    {'short_window': 10, 'long_window': 20},
    {'short_window': 10, 'long_window': 30},
    {'short_window': 20, 'long_window': 30},
]

results = {}

for i, params in enumerate(param_combinations):
    # 创建回测引擎
    engine = BacktraderEngine(initial_cash=1000000, commission=0.001)
    
    # 添加数据源和策略
    data_feed = TushareDataFeed(symbol='000001.SZ', ...)
    engine.add_data(data_feed)
    engine.add_strategy(MAStrategy, strategy_name=f'MA_Strategy_{i}', **params)
    
    # 运行回测
    result = engine.run_backtest(f'MA_Strategy_{i}')
    if result:
        results[f'MA_Strategy_{i}'] = result

# 分析优化结果
analyzer = BacktestResultsAnalyzer(results)
best_strategy = analyzer.get_best_strategy('total_return')
print(f"最佳策略: {best_strategy}")
```

### 4. 详细分析

```python
from modules.backtrader_engine import BacktestResultsAnalyzer

# 创建分析器
analyzer = BacktestResultsAnalyzer(results)

# 获取性能摘要
performance_summary = analyzer.get_performance_summary()

# 获取风险指标
risk_metrics = analyzer.get_risk_metrics()

# 获取交易指标
trading_metrics = analyzer.get_trading_metrics()

# 生成详细报告
detailed_report = analyzer.generate_detailed_report()
print(detailed_report)

# 绘制分析图表
analyzer.plot_performance_comparison('performance_comparison.png')
analyzer.plot_risk_return_scatter('risk_return_scatter.png')
analyzer.plot_trading_metrics('trading_metrics.png')

# 导出到Excel
analyzer.export_to_excel('detailed_analysis.xlsx')
```

## 内置策略

### 1. 移动平均线策略 (MAStrategy)
```python
# 参数
short_window = 5    # 短期均线周期
long_window = 20    # 长期均线周期

# 信号逻辑
# 买入: 短期均线 > 长期均线
# 卖出: 短期均线 < 长期均线
```

### 2. RSI 策略 (RSIStrategy)
```python
# 参数
rsi_period = 14     # RSI 计算周期
oversold = 30       # 超卖阈值
overbought = 70     # 超买阈值

# 信号逻辑
# 买入: RSI < oversold
# 卖出: RSI > overbought
```

### 3. MACD 策略 (MACDStrategy)
```python
# 参数
fast_period = 12    # 快线周期
slow_period = 26    # 慢线周期
signal_period = 9   # 信号线周期

# 信号逻辑
# 买入: MACD > Signal
# 卖出: MACD < Signal
```

### 4. 布林带策略 (BollingerBandsStrategy)
```python
# 参数
bb_period = 20      # 布林带周期
bb_dev = 2          # 标准差倍数

# 信号逻辑
# 买入: 价格 < 下轨
# 卖出: 价格 > 上轨
```

## 数据源支持

### 1. Tushare 数据源
```python
data_feed = TushareDataFeed(
    symbol='000001.SZ',
    start_date='20230101',
    end_date='20231231',
    tushare_token='your_token'
)
```

### 2. XtQuant 数据源
```python
data_feed = XtQuantDataFeed(
    symbol='000001.SZ',
    start_date='20230101',
    end_date='20231231',
    qmt_path='your_qmt_path',
    account='your_account'
)
```

### 3. CSV 数据源
```python
data_feed = CSVDataFeed('data/stock_data.csv')
```

## 性能指标

新框架提供完整的性能分析：

### 收益指标
- 总收益率
- 年化收益率
- 夏普比率
- 索提诺比率

### 风险指标
- 最大回撤
- 波动率
- VaR (95%, 99%)
- 下行风险

### 交易指标
- 总交易次数
- 胜率
- 盈亏比
- 平均盈亏
- 最大连续亏损

## 可视化功能

### 1. 回测结果图表
```python
engine.plot_results(filename='results.png')
```

### 2. 性能对比图
```python
analyzer.plot_performance_comparison('performance.png')
```

### 3. 风险收益散点图
```python
analyzer.plot_risk_return_scatter('risk_return.png')
```

### 4. 交易指标图
```python
analyzer.plot_trading_metrics('trading_metrics.png')
```

## 迁移优势

### 相比自研框架的优势

1. **成熟稳定**
   - Backtrader 经过大量用户验证
   - 社区活跃，问题解决及时
   - 文档完善，学习资源丰富

2. **功能丰富**
   - 内置 100+ 技术指标
   - 多种分析器支持
   - 灵活的数据源适配

3. **易于使用**
   - 简洁的 API 设计
   - 丰富的示例代码
   - 详细的文档说明

4. **高度可扩展**
   - 支持自定义指标
   - 支持自定义策略
   - 支持自定义分析器

5. **可视化支持**
   - 内置图表绘制
   - 多种图表类型
   - 可自定义样式

## 安装依赖

```bash
pip install backtrader
```

## 测试验证

运行测试脚本验证框架功能：

```bash
python test_backtrader_framework.py
```

## 示例代码

完整的使用示例请参考：
- `demo_backtrader_example.py` - 完整示例
- `test_backtrader_framework.py` - 测试脚本

## 注意事项

1. **数据格式要求**
   - CSV 数据需要包含 datetime, open, high, low, close, volume 列
   - datetime 列需要设置为索引

2. **策略开发**
   - 继承 `BacktraderStrategyBase` 类
   - 实现 `generate_buy_signal` 和 `generate_sell_signal` 方法
   - 使用 Backtrader 内置指标

3. **性能优化**
   - 大量数据回测时注意内存使用
   - 多策略回测时考虑并行处理
   - 参数优化时合理设置搜索范围

## 技术支持

如有问题，请参考：
- [Backtrader 官方文档](https://www.backtrader.com/)
- [Backtrader GitHub](https://github.com/mementum/backtrader)
- 项目中的示例代码和测试脚本 