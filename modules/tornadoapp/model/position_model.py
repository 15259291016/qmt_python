from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

class PositionType(Enum):
    """持仓类型"""
    LONG = "long"      # 多头持仓
    SHORT = "short"    # 空头持仓

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Position:
    """持仓信息"""
    symbol: str                    # 股票代码
    volume: int                    # 持仓数量
    available_volume: int          # 可用数量
    avg_price: float               # 平均成本
    current_price: float           # 当前价格
    market_value: float = 0.0      # 市值
    cost_value: float = 0.0        # 成本价值
    unrealized_pnl: float = 0.0    # 未实现盈亏
    unrealized_pnl_pct: float = 0.0 # 未实现盈亏率
    position_type: PositionType = PositionType.LONG    # 持仓类型
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)

@dataclass
class PositionSummary:
    """持仓汇总"""
    total_positions: int           # 总持仓数量
    total_market_value: float      # 总市值
    total_cost_value: float        # 总成本
    total_unrealized_pnl: float    # 总未实现盈亏
    total_unrealized_pnl_pct: float # 总未实现盈亏率
    cash: float                    # 现金
    total_asset: float             # 总资产
    positions: List[Position]      # 持仓列表

@dataclass
class PositionRisk:
    """持仓风险指标"""
    concentration_risk: float      # 集中度风险
    sector_concentration: float    # 行业集中度
    volatility_risk: float         # 波动率风险
    beta_risk: float               # Beta风险
    var_95: float                  # 95% VaR
    max_drawdown: float            # 最大回撤
    risk_level: RiskLevel          # 风险等级

@dataclass
class PositionAnalysis:
    """持仓分析结果"""
    summary: PositionSummary       # 持仓汇总
    risk: PositionRisk             # 风险指标
    top_positions: List[Position]  # 主要持仓
    sector_distribution: Dict[str, float]  # 行业分布
    performance_metrics: Dict[str, float]  # 绩效指标
    recommendations: List[str]     # 调整建议 