"""
持仓分析API的Pydantic模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PositionItem(BaseModel):
    """持仓项"""
    symbol: str = Field(..., description="股票代码", example="000001.SZ")
    volume: int = Field(..., description="持仓数量", ge=0, example=1000)
    available_volume: int = Field(..., description="可用数量", ge=0, example=1000)
    avg_price: float = Field(..., description="平均成本价", ge=0, example=15.50)
    current_price: float = Field(..., description="当前价格", ge=0, example=16.20)


class PositionAnalysisRequest(BaseModel):
    """持仓分析请求"""
    positions: List[PositionItem] = Field(..., description="持仓列表", min_items=0)
    cash: float = Field(0.0, description="现金余额", ge=0, example=10000.0)


class PositionAnalysisQueryParams(BaseModel):
    """持仓分析查询参数（GET）"""
    account_id: str = Field(..., description="账户ID", example="account_001")
    include_recommendations: bool = Field(True, description="是否包含建议", example=True)


class SectorDistribution(BaseModel):
    """行业分布"""
    sector: str = Field(..., description="行业名称", example="银行")
    percentage: float = Field(..., description="占比百分比", ge=0, le=100, example=35.5)
    market_value: float = Field(..., description="市值", ge=0, example=155000.0)


class RiskMetrics(BaseModel):
    """风险指标"""
    total_market_value: float = Field(..., description="总市值", ge=0)
    total_cost: float = Field(..., description="总成本", ge=0)
    total_profit: float = Field(..., description="总盈亏", example=5000.0)
    total_profit_rate: float = Field(..., description="总盈亏率", example=3.2)
    sector_concentration: float = Field(..., description="行业集中度", ge=0, le=100)
    max_single_position_ratio: float = Field(..., description="单只股票最大占比", ge=0, le=100)


class PositionDetailItem(BaseModel):
    """持仓明细项"""
    symbol: str = Field(..., description="股票代码")
    volume: int = Field(..., description="持仓数量")
    available_volume: int = Field(..., description="可用数量")
    avg_price: float = Field(..., description="平均成本价")
    current_price: float = Field(..., description="当前价格")
    market_value: float = Field(..., description="市值")
    cost_value: float = Field(..., description="成本价值")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    unrealized_pnl_pct: float = Field(..., description="未实现盈亏率")
    create_time: Optional[str] = Field(None, description="创建时间")
    update_time: Optional[str] = Field(None, description="更新时间")


class PositionAnalysisResponse(BaseModel):
    """持仓分析响应"""
    summary: Dict[str, Any] = Field(..., description="持仓汇总")
    risk: Dict[str, Any] = Field(..., description="风险指标")
    top_positions: List[Dict[str, Any]] = Field(..., description="主要持仓")
    sector_distribution: Dict[str, float] = Field(..., description="行业分布")
    performance_metrics: Dict[str, Any] = Field(..., description="绩效指标")
    recommendations: Optional[List[str]] = Field(None, description="操作建议")


class PositionDetailResponse(BaseModel):
    """持仓明细响应"""
    symbol: Optional[str] = Field(None, description="股票代码（单个持仓时）")
    volume: Optional[int] = Field(None, description="持仓数量")
    available_volume: Optional[int] = Field(None, description="可用数量")
    avg_price: Optional[float] = Field(None, description="平均成本价")
    current_price: Optional[float] = Field(None, description="当前价格")
    market_value: Optional[float] = Field(None, description="市值")
    cost_value: Optional[float] = Field(None, description="成本价值")
    unrealized_pnl: Optional[float] = Field(None, description="未实现盈亏")
    unrealized_pnl_pct: Optional[float] = Field(None, description="未实现盈亏率")
    create_time: Optional[str] = Field(None, description="创建时间")
    update_time: Optional[str] = Field(None, description="更新时间")
    positions: Optional[List[PositionDetailItem]] = Field(None, description="持仓列表（多个持仓时）")


class PositionReportQueryParams(BaseModel):
    """持仓报告查询参数"""
    account_id: str = Field(..., description="账户ID", example="account_001")
    report_type: str = Field("summary", description="报告类型: summary/detailed/risk", example="summary")


class PositionReportResponse(BaseModel):
    """持仓报告响应"""
    report_type: str = Field(..., description="报告类型")
    generated_time: str = Field(..., description="生成时间")
    data: Dict[str, Any] = Field(..., description="报告数据")

