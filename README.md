# 量化交易系统 - 持仓分析模块

## 项目概述

这是一个基于Python的量化交易系统，集成了完整的持仓分析功能，包括：
- 持仓数据管理
- 技术分析
- 风险控制
- 可视化报告
- XtQuant集成

## 主要功能

### 1. 回测框架
- **Backtrader 集成**: 使用成熟的 Backtrader 回测框架
- **多策略支持**: 支持同时回测多个策略
- **参数优化**: 自动参数优化和策略选择
- **详细分析**: 完整的绩效分析和风险指标

### 2. 持仓分析模块
- **持仓查询**: 支持从XtQuant获取实时持仓数据
- **风险分析**: 计算集中度风险、波动率风险、VaR等指标
- **绩效评估**: 分析收益率、最大回撤、夏普比率等
- **可视化报告**: 生成图表和PDF报告

### 2. 技术分析模块
- **技术指标**: 支持MA、MACD、RSI、KDJ、布林带等指标
- **交易信号**: 基于多指标综合评分生成买卖信号
- **趋势分析**: 识别多头/空头趋势
- **信号过滤**: 支持置信度过滤和风险控制

### 3. XtQuant集成
- **实时数据**: 从XtQuant获取持仓和行情数据
- **自动分析**: 定期分析持仓并提供交易建议
- **风险监控**: 实时监控持仓风险

## Python环境

建议使用 Python 3.11.9

```bash
conda create -n py311 python=3.11.9
conda activate py311
```

## 安装依赖

```bash
pip install -r requirements.txt
```

**重要依赖说明**:
- `backtrader`: 回测框架
- `tushare`: 金融数据接口
- `talib-binary`: 技术分析库
- `xtquant`: 迅投量化交易接口
- `matplotlib`: 图表生成
- `pandas`: 数据处理
- `numpy`: 数值计算

## 环境配置

首次使用项目时，需要配置环境变量：

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，配置你的服务信息
# 请根据.env.example中的示例，填入你的实际配置
```

**重要配置项**:
- `toshare_token`: Tushare API token
- `xtquant_config`: XtQuant配置信息

**注意**: `.env` 文件包含敏感信息，不会被提交到Git仓库。请确保在 `.env` 文件中配置正确的服务参数。

## 快速开始

### 1. 启动Web服务器

```bash
python main.py
```

### 2. 运行演示脚本

```bash
# 持仓分析演示
python demo_position_analysis.py

# XtQuant技术分析演示
python demo_xtquant_analysis.py

# Backtrader 回测演示
python demo_backtrader_example.py

# Backtrader 框架测试
python test_backtrader_framework.py

# 比亚迪策略回测演示
python simple_byd_backtest.py

# 比亚迪策略演示
python demo_byd_strategy.py

# 比亚迪策略简单测试
python test_byd_simple.py
```

### 3. 访问API接口

启动服务器后，可以访问以下API端点：

#### 持仓分析API
- `GET /api/position/analysis?account_id=demo` - 获取持仓分析
- `GET /api/position/detail?account_id=demo` - 获取持仓明细
- `GET /api/position/report?account_id=demo&type=summary` - 生成持仓报告

#### 技术分析API
- `GET /api/technical/analysis?account_id=demo` - 获取技术分析
- `GET /api/technical/signals?account_id=demo&min_confidence=0.7` - 获取交易信号
- `GET /api/technical/indicators?symbol=000001.SZ&days=60` - 获取技术指标

## 使用示例

### 1. 持仓分析

```python
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer

# 创建分析器
analyzer = PositionAnalyzer(tushare_token)

# 分析持仓
positions_data = [
    {
        "symbol": "000001.SZ",
        "volume": 1000,
        "avg_price": 15.50,
        "current_price": 16.20
    }
]

analysis = analyzer.analyze_positions(positions_data, cash=50000)
print(f"总收益率: {analysis.summary.total_unrealized_pnl_pct:.2f}%")
```

### 2. 回测分析

```python
from modules.backtrader_engine import BacktraderEngine, TushareDataFeed, MAStrategy

# 创建回测引擎
engine = BacktraderEngine(initial_cash=1000000, commission=0.001)

# 添加数据源和策略
data_feed = TushareDataFeed(symbol='000001.SZ', start_date='20230101', 
                           end_date='20231231', tushare_token='your_token')
engine.add_data(data_feed)
engine.add_strategy(MAStrategy)

# 运行回测
result = engine.run_backtest()
print(f"总收益率: {result.total_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
```

### 3. 比亚迪策略回测

```python
from strategies.byd_strategy import BYDStrategy, BYDEnhancedStrategy, BYDConservativeStrategy

# 运行比亚迪策略回测
python simple_byd_backtest.py

# 查看详细说明
# 参考 BYD_STRATEGY_SUMMARY.md 文件
```

### 3. 技术分析

```python
from modules.tornadoapp.position.xtquant_position_manager import XtQuantPositionManager

# 创建XtQuant管理器
manager = XtQuantPositionManager(tushare_token)

# 分析持仓
results = await manager.analyze_all_positions("demo_account")

# 获取交易建议
recommendations = manager.generate_trading_recommendations(results)
for rec in recommendations:
    print(f"{rec['symbol']}: {rec['action']} (置信度: {rec['confidence']:.2f})")
```

### 3. 可视化报告

```python
from modules.tornadoapp.position.position_visualizer import PositionVisualizer

# 创建可视化工具
visualizer = PositionVisualizer()

# 生成图表
charts = visualizer.generate_comprehensive_report(analysis)
```

## 项目结构

```
modules/tornadoapp/position/
├── __init__.py                    # 模块初始化
├── position_analyzer.py           # 持仓分析器
├── position_visualizer.py         # 可视化工具
├── xtquant_position_manager.py    # XtQuant集成
└── position_api.py               # API路由

modules/tornadoapp/handler/
├── position_handler.py            # 持仓分析API处理器
└── technical_analysis_handler.py  # 技术分析API处理器

modules/tornadoapp/model/
└── position_model.py              # 持仓数据模型
```

## 技术指标说明

### 支持的指标
- **移动平均线**: MA5, MA10, MA20, MA60
- **MACD**: 趋势指标
- **RSI**: 相对强弱指标
- **KDJ**: 随机指标
- **布林带**: 波动率指标
- **成交量**: 量价关系分析

### 交易信号生成
系统基于多指标综合评分生成交易信号：
- **买入信号**: 评分 >= 3.0
- **卖出信号**: 评分 <= -3.0
- **持有信号**: -3.0 < 评分 < 3.0

## 风险提示

⚠️ **重要提醒**:
- 本系统提供的分析结果仅供参考，不构成投资建议
- 技术分析存在滞后性，请结合基本面分析
- 投资有风险，入市需谨慎
- 建议在实盘交易前进行充分的回测验证

## 开发说明

### 添加新的技术指标

```python
def calculate_custom_indicator(self, df: pd.DataFrame) -> float:
    """计算自定义指标"""
    close_prices = df['close'].values.astype(np.float64)
    # 实现指标计算逻辑
    return indicator_value
```

### 扩展交易信号逻辑

```python
def generate_custom_signals(self, indicators: Dict, current_price: float) -> Dict:
    """生成自定义交易信号"""
    # 实现信号生成逻辑
    return signals
```

## 市场数据存储

### 数据库设计

本项目采用MySQL数据库，专门为记录市场数据而设计，为未来的量化AI模型准备数据。

#### 数据库特性

- **专注数据存储**: 简化设计，专注于市场数据存储和查询
- **支持迅投数据**: 完整支持迅投的3秒级别tick数据、分钟级、日线数据
- **AI友好**: 为机器学习模型提供便捷的数据访问接口
- **高性能**: 优化的索引策略和查询性能
- **易于维护**: 简单的表结构，清晰的数据管理

#### 核心表结构

##### 1. 股票基础信息
- `stock_basic`: 股票基础信息表

##### 2. 市场数据表
- `tick_data`: 3秒级别tick数据
- `minute_data`: 分钟级行情数据
- `daily_data`: 日线行情数据
- `adj_factor`: 复权因子表

##### 3. 技术指标
- `technical_indicators`: 技术指标表

##### 4. 数据管理
- `data_sync_status`: 数据同步状态表
- `system_config`: 系统配置表

#### 快速开始

##### 1. 初始化数据库
```bash
# 一键初始化数据库
python database/init_market_data.py --host localhost --user root --password your_password

# 测试连接
python database/init_market_data.py --test-only --host localhost --user root --password your_password
```

##### 2. 基本使用
```python
from database.market_data_manager import MarketDataManager

# 创建数据管理器
manager = MarketDataManager(
    host='localhost',
    port=3306,
    user='market_data_app',
    password='app_password',
    database='market_data'
)

# 测试连接
if manager.test_connection():
    print("✅ 数据库连接成功！")
```

##### 3. 存储市场数据
```python
import pandas as pd

# 存储股票基础信息
stocks_data = pd.DataFrame({
    'ts_code': ['000001.SZ', '000002.SZ', '600519.SH'],
    'symbol': ['000001', '000002', '600519'],
    'name': ['平安银行', '万科A', '贵州茅台'],
    'industry': ['银行', '房地产', '食品饮料'],
    'market': ['主板', '主板', '主板']
})
manager.insert_stock_basic(stocks_data)

# 存储日线数据
daily_data = pd.DataFrame({
    'symbol': ['000001.SZ'],
    'trade_date': ['2025-01-15'],
    'open': [15.50], 'high': [15.80], 'low': [15.40], 'close': [15.70],
    'volume': [1000000], 'amount': [15700000], 'pct_chg': [1.29]
})
manager.insert_daily_data(daily_data)

# 存储tick数据
tick_data = pd.DataFrame({
    'symbol': ['000001.SZ'] * 100,
    'tick_time': pd.date_range('2025-01-15 09:30:00', periods=100, freq='3S'),
    'last_price': [15.50 + i * 0.01 for i in range(100)],
    'volume': [1000] * 100,
    'amount': [15500 + i * 10 for i in range(100)]
})
manager.insert_tick_data(tick_data)
```

##### 4. 查询市场数据
```python
# 获取股票列表
stocks = manager.get_stock_list()
print(f"股票总数: {len(stocks)}")

# 获取日线数据
daily_data = manager.get_daily_data('000001.SZ', '2025-01-01', '2025-01-15')
print(f"日线数据条数: {len(daily_data)}")

# 获取tick数据
tick_data = manager.get_tick_data('000001.SZ', '2025-01-15 09:30:00', '2025-01-15 10:00:00')
print(f"tick数据条数: {len(tick_data)}")

# 获取最新价格
latest_price = manager.get_latest_price('000001.SZ')
print(f"平安银行最新价格: {latest_price}")
```

##### 5. 为AI模型准备数据
```python
# 获取训练数据
def get_training_data(symbol, start_date, end_date):
    """获取用于AI模型训练的数据"""
    # 获取日线数据
    daily_data = manager.get_daily_data(symbol, start_date, end_date)
    
    # 获取技术指标
    indicators = manager.get_technical_indicators(symbol, start_date, end_date)
    
    # 合并数据
    training_data = daily_data.merge(indicators, on=['symbol', 'trade_date'], how='left')
    
    # 计算特征
    training_data['price_change'] = training_data['close'].pct_change()
    training_data['volume_change'] = training_data['volume'].pct_change()
    training_data['ma5_ma20_diff'] = training_data['ma5'] - training_data['ma20']
    
    return training_data

# 获取训练数据
training_data = get_training_data('000001.SZ', '2024-01-01', '2024-12-31')
print(f"训练数据形状: {training_data.shape}")
```

#### 数据导出

```python
# 导出数据到CSV
csv_file = manager.export_data_to_csv(
    symbol='000001.SZ',
    data_type='daily',
    start_date='2025-01-01',
    end_date='2025-01-15',
    output_dir='data/export'
)
print(f"数据导出到: {csv_file}")
```

#### 详细使用指南

更多详细的使用方法和示例，请参考：
- `database/MARKET_DATA_GUIDE.md` - 完整使用指南
- `database/market_data_manager.py` - 数据管理器源码
- `database/market_data_schema.sql` - 数据库表结构

## 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件
- 项目讨论区