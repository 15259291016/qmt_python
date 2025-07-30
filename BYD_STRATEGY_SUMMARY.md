# 比亚迪股票策略回测指南

## 项目概述

本项目提供了完整的比亚迪（002594.SZ）股票策略回测功能，使用Backtrader框架进行回测分析。

## 策略说明

### 1. 基础比亚迪策略 (BYDStrategy)
- **买入条件**: RSI < 30 且短期均线上穿长期均线
- **卖出条件**: RSI > 70 或短期均线下穿长期均线
- **止损**: 5%
- **止盈**: 15%
- **特点**: 适合中等风险偏好的投资者

### 2. 增强比亚迪策略 (BYDEnhancedStrategy)
- **买入条件**: 结合RSI、均线、布林带、成交量等多重指标
- **卖出条件**: 多重技术指标确认
- **止损**: 3%
- **止盈**: 20%
- **特点**: 更精确的信号，适合积极投资者

### 3. 保守比亚迪策略 (BYDConservativeStrategy)
- **买入条件**: 更严格的RSI和均线条件
- **卖出条件**: 保守的止盈止损
- **止损**: 2%
- **止盈**: 10%
- **特点**: 低风险，适合稳健投资者

## 文件说明

### 主要文件
- `byd_backtest.py` - 完整的比亚迪回测脚本（需要Tushare token）
- `simple_byd_backtest.py` - 简化版回测脚本（使用模拟数据）
- `test_byd_simple.py` - 简单测试脚本
- `strategies/byd_strategy.py` - 比亚迪策略实现

### 使用方法

#### 方法1: 使用真实数据（推荐）
```bash
# 1. 获取Tushare token
# 访问 https://tushare.pro/ 注册并获取token

# 2. 修改脚本中的token
# 编辑 byd_backtest.py 中的 TUSHARE_TOKEN 变量

# 3. 运行回测
python byd_backtest.py
```

#### 方法2: 使用模拟数据（快速测试）
```bash
# 直接运行简化版本
python simple_byd_backtest.py
```

#### 方法3: 简单测试
```bash
# 运行基础测试
python test_byd_simple.py
```

## 回测结果分析

### 关键指标说明
- **总收益率**: 整个回测期间的累计收益率
- **年化收益率**: 按年计算的收益率
- **夏普比率**: 风险调整后的收益率指标
- **最大回撤**: 最大亏损幅度
- **胜率**: 盈利交易占总交易的比例
- **盈亏比**: 平均盈利与平均亏损的比值

### 策略对比
| 策略类型 | 风险等级 | 预期收益 | 最大回撤 | 适用投资者 |
|---------|---------|---------|---------|-----------|
| 基础策略 | 中等 | 中等 | 中等 | 一般投资者 |
| 增强策略 | 较高 | 较高 | 较高 | 积极投资者 |
| 保守策略 | 较低 | 较低 | 较低 | 稳健投资者 |

## 技术指标说明

### RSI (相对强弱指标)
- **超买**: RSI > 70，可能卖出
- **超卖**: RSI < 30，可能买入
- **中性**: 30 ≤ RSI ≤ 70

### 移动平均线
- **短期均线**: 5日、10日均线
- **长期均线**: 20日、50日均线
- **金叉**: 短期均线上穿长期均线，买入信号
- **死叉**: 短期均线下穿长期均线，卖出信号

### 布林带
- **上轨**: 价格上限，超买区域
- **中轨**: 移动平均线
- **下轨**: 价格下限，超卖区域

## 风险提示

⚠️ **重要提醒**:
1. **历史回测结果不代表未来表现**
2. **投资有风险，入市需谨慎**
3. **建议结合基本面分析进行投资决策**
4. **请根据自身风险承受能力选择合适的策略**
5. **实盘交易前请充分测试和验证**

## 环境要求

### Python版本
- Python 3.8+

### 主要依赖
```bash
pip install backtrader
pip install pandas
pip install numpy
pip install matplotlib
pip install tushare  # 如需使用真实数据
```

### 安装依赖
```bash
pip install -r requirements.txt
```

## 自定义策略

### 修改策略参数
```python
# 在策略类中修改参数
params = (
    ('rsi_period', 14),        # RSI周期
    ('rsi_oversold', 30),      # RSI超卖阈值
    ('rsi_overbought', 70),    # RSI超买阈值
    ('ma_short', 5),           # 短期均线
    ('ma_long', 20),           # 长期均线
    ('stop_loss', 0.05),       # 止损比例
    ('take_profit', 0.15),     # 止盈比例
)
```

### 添加新的技术指标
```python
def __init__(self):
    # 添加MACD指标
    self.macd = bt.indicators.MACD(self.data.close)
    
    # 添加KDJ指标
    self.stoch = bt.indicators.Stochastic(self.data)
```

### 自定义买卖信号
```python
def generate_buy_signal(self) -> bool:
    # 自定义买入条件
    condition1 = self.rsi[0] < 30
    condition2 = self.macd.macd[0] > self.macd.signal[0]
    return condition1 and condition2

def generate_sell_signal(self) -> bool:
    # 自定义卖出条件
    condition1 = self.rsi[0] > 70
    condition2 = self.macd.macd[0] < self.macd.signal[0]
    return condition1 or condition2
```

## 输出文件说明

### 回测结果文件
- `byd_backtest_results_YYYYMMDD_HHMMSS.json` - 回测结果数据
- `byd_backtest_plots/byd_strategy_comparison.png` - 策略对比图表

### 图表说明
1. **总收益率对比**: 各策略的累计收益率
2. **夏普比率对比**: 风险调整后的收益率
3. **最大回撤对比**: 各策略的最大亏损幅度
4. **胜率对比**: 各策略的盈利交易比例

## 常见问题

### Q1: 如何获取Tushare token？
A1: 访问 https://tushare.pro/ 注册账号，在个人中心获取token。

### Q2: 回测结果不理想怎么办？
A2: 可以尝试调整策略参数，或者使用不同的技术指标组合。

### Q3: 如何添加更多股票？
A3: 修改脚本中的股票代码，或者创建多股票回测脚本。

### Q4: 如何优化策略参数？
A4: 可以使用网格搜索或遗传算法进行参数优化。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件
- 项目讨论区

---

**免责声明**: 本策略仅供学习和研究使用，不构成投资建议。投资有风险，请谨慎决策。 