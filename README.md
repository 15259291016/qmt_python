# 量化交易系统 - 持仓分析模块

## 项目概述

这是一个基于Python的量化交易系统，集成了完整的持仓分析功能，包括：
- 持仓数据管理
- 技术分析
- 风险控制
- 可视化报告
- XtQuant集成

## 主要功能

### 1. 持仓分析模块
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

### 2. 技术分析

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

## 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件
- 项目讨论区