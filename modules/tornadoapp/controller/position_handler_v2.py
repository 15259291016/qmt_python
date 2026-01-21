"""
持仓分析API处理器（Pydantic版本）
使用类型注解自动生成Swagger文档
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from modules.tornadoapp.define.base.handler import BaseHandler
from modules.tornadoapp.define.enum.response_model import Status, Message
from modules.tornadoapp.model.position_model import PositionAnalysis
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer
from modules.tornadoapp.schemas.position_schemas import (
    PositionAnalysisRequest,
    PositionAnalysisQueryParams,
    PositionAnalysisResponse,
    PositionDetailResponse,
    PositionReportQueryParams,
    PositionReportResponse,
    PositionDetailItem
)
import config.ConfigServer as Cs

logger = logging.getLogger(__name__)


class PositionAnalysisHandler(BaseHandler):
    """持仓分析处理器 - 使用Pydantic自动生成文档"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.tushare_token = Cs.getTushareToken()
        self.analyzer = PositionAnalyzer(self.tushare_token)
    
    async def get(
        self,
        account_id: str,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        获取持仓分析
        
        Args:
            account_id: 账户ID（查询参数）
            include_recommendations: 是否包含建议（查询参数，默认true）
        """
        try:
            # 模拟持仓数据 - 实际应该从数据库或交易系统获取
            positions_data = await self.get_positions_data(account_id)
            
            # 分析持仓
            analysis = await self.analyze_positions(positions_data)
            
            # 构建响应数据
            response_data = self.build_response_data(analysis, include_recommendations)
            
            return {
                "code": Status.SUCCESS,
                "msg": Message.SUCCESS,
                "data": response_data
            }
            
        except Exception as e:
            logger.error(f"持仓分析失败: {e}", exc_info=True)
            return {
                "code": Status.UNKNOWN_ERROR,
                "msg": f"持仓分析失败: {str(e)}",
                "data": {}
            }
    
    async def post(self) -> Dict[str, Any]:
        """
        提交持仓数据进行分析
        
        请求体自动解析为PositionAnalysisRequest
        """
        try:
            # 从请求体解析Pydantic模型
            request = self.parse_pydantic_model(PositionAnalysisRequest)
            
            if not request.positions:
                return {
                    "code": Status.UNKNOWN_ERROR,
                    "msg": "缺少持仓数据",
                    "data": {}
                }
            
            # 转换为字典格式
            positions_data = [pos.dict() for pos in request.positions]
            
            # 分析持仓
            analysis = await self.analyze_positions(positions_data, request.cash)
            
            # 构建响应数据
            response_data = self.build_response_data(analysis, True)
            
            return {
                "code": Status.SUCCESS,
                "msg": Message.SUCCESS,
                "data": response_data
            }
            
        except Exception as e:
            logger.error(f"持仓分析失败: {e}", exc_info=True)
            return {
                "code": Status.UNKNOWN_ERROR,
                "msg": f"持仓分析失败: {str(e)}",
                "data": {}
            }
    
    async def get_positions_data(self, account_id: str) -> List[Dict]:
        """获取持仓数据 - 模拟数据"""
        # 这里应该从实际的交易系统或数据库获取持仓数据
        # 目前使用模拟数据
        return [
            {
                "symbol": "000001.SZ",
                "volume": 1000,
                "available_volume": 1000,
                "avg_price": 15.50,
                "current_price": 16.20
            },
            {
                "symbol": "000002.SZ",
                "volume": 500,
                "available_volume": 500,
                "avg_price": 25.80,
                "current_price": 24.50
            },
            {
                "symbol": "600519.SH",
                "volume": 200,
                "available_volume": 200,
                "avg_price": 1800.00,
                "current_price": 1850.00
            }
        ]
    
    async def analyze_positions(self, positions_data: List[Dict], cash: float = 0.0) -> PositionAnalysis:
        """分析持仓"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyzer.analyze_positions, positions_data, cash)
    
    def build_response_data(self, analysis: PositionAnalysis, include_recommendations: bool = True) -> Dict[str, Any]:
        """构建响应数据"""
        response_data = {
            "summary": {
                "total_positions": analysis.summary.total_positions,
                "total_market_value": round(analysis.summary.total_market_value, 2),
                "total_cost_value": round(analysis.summary.total_cost_value, 2),
                "total_unrealized_pnl": round(analysis.summary.total_unrealized_pnl, 2),
                "total_unrealized_pnl_pct": round(analysis.summary.total_unrealized_pnl_pct, 2),
                "cash": round(analysis.summary.cash, 2),
                "total_asset": round(analysis.summary.total_asset, 2)
            },
            "risk": {
                "concentration_risk": round(analysis.risk.concentration_risk, 4),
                "sector_concentration": round(analysis.risk.sector_concentration, 4),
                "volatility_risk": round(analysis.risk.volatility_risk, 4),
                "beta_risk": round(analysis.risk.beta_risk, 4),
                "var_95": round(analysis.risk.var_95, 4),
                "max_drawdown": round(analysis.risk.max_drawdown, 4),
                "risk_level": analysis.risk.risk_level.value
            },
            "top_positions": [
                {
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "available_volume": pos.available_volume,
                    "avg_price": round(pos.avg_price, 2),
                    "current_price": round(pos.current_price, 2),
                    "market_value": round(pos.market_value, 2),
                    "cost_value": round(pos.cost_value, 2),
                    "unrealized_pnl": round(pos.unrealized_pnl, 2),
                    "unrealized_pnl_pct": round(pos.unrealized_pnl_pct, 2)
                }
                for pos in analysis.top_positions
            ],
            "sector_distribution": analysis.sector_distribution,
            "performance_metrics": {
                k: round(v, 4) if isinstance(v, float) else v
                for k, v in analysis.performance_metrics.items()
            }
        }
        
        if include_recommendations:
            response_data["recommendations"] = analysis.recommendations
        
        return response_data


class PositionDetailHandler(BaseHandler):
    """持仓明细处理器 - 使用Pydantic自动生成文档"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.tushare_token = Cs.getTushareToken()
        self.analyzer = PositionAnalyzer(self.tushare_token)
    
    async def get(
        self,
        account_id: str,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取持仓明细
        
        Args:
            account_id: 账户ID（查询参数）
            symbol: 股票代码（查询参数，可选，不传则返回所有持仓）
        """
        try:
            if not account_id:
                return {
                    "code": Status.UNKNOWN_ERROR,
                    "msg": "缺少账户ID参数",
                    "data": {}
                }
            
            # 获取持仓明细
            positions_data = await self.get_positions_data(account_id)
            
            if symbol:
                # 获取特定股票的持仓
                position_data = next((p for p in positions_data if p["symbol"] == symbol), None)
                if not position_data:
                    return {
                        "code": Status.UNKNOWN_ERROR,
                        "msg": f"未找到股票 {symbol} 的持仓",
                        "data": {}
                    }
                
                # 分析单个持仓
                analysis = await self.analyze_positions([position_data])
                position = analysis.summary.positions[0] if analysis.summary.positions else None
                
                if position:
                    response_data = PositionDetailResponse(
                        symbol=position.symbol,
                        volume=position.volume,
                        available_volume=position.available_volume,
                        avg_price=round(position.avg_price, 2),
                        current_price=round(position.current_price, 2),
                        market_value=round(position.market_value, 2),
                        cost_value=round(position.cost_value, 2),
                        unrealized_pnl=round(position.unrealized_pnl, 2),
                        unrealized_pnl_pct=round(position.unrealized_pnl_pct, 2),
                        create_time=position.create_time.isoformat(),
                        update_time=position.update_time.isoformat()
                    )
                else:
                    return {
                        "code": Status.UNKNOWN_ERROR,
                        "msg": "持仓数据异常",
                        "data": {}
                    }
            else:
                # 获取所有持仓明细
                analysis = await self.analyze_positions(positions_data)
                positions = [
                    PositionDetailItem(
                        symbol=pos.symbol,
                        volume=pos.volume,
                        available_volume=pos.available_volume,
                        avg_price=round(pos.avg_price, 2),
                        current_price=round(pos.current_price, 2),
                        market_value=round(pos.market_value, 2),
                        cost_value=round(pos.cost_value, 2),
                        unrealized_pnl=round(pos.unrealized_pnl, 2),
                        unrealized_pnl_pct=round(pos.unrealized_pnl_pct, 2),
                        create_time=pos.create_time.isoformat(),
                        update_time=pos.update_time.isoformat()
                    )
                    for pos in analysis.summary.positions
                ]
                response_data = PositionDetailResponse(positions=positions)
            
            return {
                "code": Status.SUCCESS,
                "msg": Message.SUCCESS,
                "data": response_data.dict(exclude_none=True)
            }
            
        except Exception as e:
            logger.error(f"获取持仓明细失败: {e}", exc_info=True)
            return {
                "code": Status.UNKNOWN_ERROR,
                "msg": f"获取持仓明细失败: {str(e)}",
                "data": {}
            }
    
    async def get_positions_data(self, account_id: str) -> List[Dict]:
        """获取持仓数据 - 模拟数据"""
        return [
            {
                "symbol": "000001.SZ",
                "volume": 1000,
                "available_volume": 1000,
                "avg_price": 15.50,
                "current_price": 16.20
            },
            {
                "symbol": "000002.SZ",
                "volume": 500,
                "available_volume": 500,
                "avg_price": 25.80,
                "current_price": 24.50
            },
            {
                "symbol": "600519.SH",
                "volume": 200,
                "available_volume": 200,
                "avg_price": 1800.00,
                "current_price": 1850.00
            }
        ]
    
    async def analyze_positions(self, positions_data: List[Dict], cash: float = 0.0) -> PositionAnalysis:
        """分析持仓"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyzer.analyze_positions, positions_data, cash)


class PositionReportHandler(BaseHandler):
    """持仓报告处理器 - 使用Pydantic自动生成文档"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        config_data = Cs.returnConfigData()
        self.tushare_token = config_data.get("toshare_token", "")
        self.analyzer = PositionAnalyzer(self.tushare_token)
    
    async def get(
        self,
        account_id: str,
        report_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        生成持仓报告
        
        Args:
            account_id: 账户ID（查询参数）
            report_type: 报告类型（查询参数，summary/detailed/risk，默认summary）
        """
        try:
            if not account_id:
                return {
                    "code": Status.UNKNOWN_ERROR,
                    "msg": "缺少账户ID参数",
                    "data": {}
                }
            
            if report_type not in ["summary", "detailed", "risk"]:
                return {
                    "code": Status.UNKNOWN_ERROR,
                    "msg": "不支持的报告类型",
                    "data": {}
                }
            
            # 获取持仓数据
            positions_data = await self.get_positions_data(account_id)
            analysis = await self.analyze_positions(positions_data)
            
            # 生成报告
            if report_type == "summary":
                report = self.generate_summary_report(analysis)
            elif report_type == "detailed":
                report = self.generate_detailed_report(analysis)
            elif report_type == "risk":
                report = self.generate_risk_report(analysis)
            
            response_data = PositionReportResponse(
                report_type=report_type,
                generated_time=datetime.now().isoformat(),
                data=report
            )
            
            return {
                "code": Status.SUCCESS,
                "msg": Message.SUCCESS,
                "data": response_data.dict()
            }
            
        except Exception as e:
            logger.error(f"生成持仓报告失败: {e}", exc_info=True)
            return {
                "code": Status.UNKNOWN_ERROR,
                "msg": f"生成持仓报告失败: {str(e)}",
                "data": {}
            }
    
    async def get_positions_data(self, account_id: str) -> List[Dict]:
        """获取持仓数据 - 模拟数据"""
        return [
            {
                "symbol": "000001.SZ",
                "volume": 1000,
                "available_volume": 1000,
                "avg_price": 15.50,
                "current_price": 16.20
            },
            {
                "symbol": "000002.SZ",
                "volume": 500,
                "available_volume": 500,
                "avg_price": 25.80,
                "current_price": 24.50
            },
            {
                "symbol": "600519.SH",
                "volume": 200,
                "available_volume": 200,
                "avg_price": 1800.00,
                "current_price": 1850.00
            }
        ]
    
    async def analyze_positions(self, positions_data: List[Dict], cash: float = 0.0) -> PositionAnalysis:
        """分析持仓"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyzer.analyze_positions, positions_data, cash)
    
    def generate_summary_report(self, analysis: PositionAnalysis) -> Dict[str, Any]:
        """生成汇总报告"""
        return {
            "summary": {
                "total_positions": analysis.summary.total_positions,
                "total_market_value": round(analysis.summary.total_market_value, 2),
                "total_unrealized_pnl": round(analysis.summary.total_unrealized_pnl, 2),
                "total_unrealized_pnl_pct": round(analysis.summary.total_unrealized_pnl_pct, 2),
                "total_asset": round(analysis.summary.total_asset, 2)
            },
            "risk_level": analysis.risk.risk_level.value,
            "top_positions": [
                {
                    "symbol": pos.symbol,
                    "market_value": round(pos.market_value, 2),
                    "unrealized_pnl_pct": round(pos.unrealized_pnl_pct, 2)
                }
                for pos in analysis.top_positions[:3]
            ],
            "recommendations": analysis.recommendations[:3] if analysis.recommendations else []
        }
    
    def generate_detailed_report(self, analysis: PositionAnalysis) -> Dict[str, Any]:
        """生成详细报告"""
        return {
            "summary": {
                "total_positions": analysis.summary.total_positions,
                "total_market_value": round(analysis.summary.total_market_value, 2),
                "total_cost_value": round(analysis.summary.total_cost_value, 2),
                "total_unrealized_pnl": round(analysis.summary.total_unrealized_pnl, 2),
                "total_unrealized_pnl_pct": round(analysis.summary.total_unrealized_pnl_pct, 2),
                "cash": round(analysis.summary.cash, 2),
                "total_asset": round(analysis.summary.total_asset, 2)
            },
            "all_positions": [
                {
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "avg_price": round(pos.avg_price, 2),
                    "current_price": round(pos.current_price, 2),
                    "market_value": round(pos.market_value, 2),
                    "unrealized_pnl": round(pos.unrealized_pnl, 2),
                    "unrealized_pnl_pct": round(pos.unrealized_pnl_pct, 2)
                }
                for pos in analysis.summary.positions
            ],
            "performance_metrics": {
                k: round(v, 4) if isinstance(v, float) else v
                for k, v in analysis.performance_metrics.items()
            },
            "recommendations": analysis.recommendations
        }
    
    def generate_risk_report(self, analysis: PositionAnalysis) -> Dict[str, Any]:
        """生成风险报告"""
        return {
            "risk_metrics": {
                "concentration_risk": round(analysis.risk.concentration_risk, 4),
                "sector_concentration": round(analysis.risk.sector_concentration, 4),
                "volatility_risk": round(analysis.risk.volatility_risk, 4),
                "beta_risk": round(analysis.risk.beta_risk, 4),
                "var_95": round(analysis.risk.var_95, 4),
                "max_drawdown": round(analysis.risk.max_drawdown, 4),
                "risk_level": analysis.risk.risk_level.value
            },
            "risk_assessment": self.assess_risk_level(analysis.risk),
            "risk_recommendations": [
                rec for rec in analysis.recommendations 
                if "风险" in rec or "集中" in rec or "分散" in rec
            ] if analysis.recommendations else []
        }
    
    def assess_risk_level(self, risk) -> str:
        """评估风险等级"""
        if risk.risk_level.value == "high":
            return "高风险 - 建议立即调整持仓结构"
        elif risk.risk_level.value == "medium":
            return "中等风险 - 建议适当优化持仓"
        else:
            return "低风险 - 持仓结构相对合理"

