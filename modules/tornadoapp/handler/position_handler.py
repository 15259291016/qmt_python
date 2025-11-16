import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from tornado.web import RequestHandler
from modules.tornadoapp.define.base.handler import BaseHandler
from ..define.enum.response_model import Status, Message
from ..model.position_model import PositionAnalysis
from ..position.position_analyzer import PositionAnalyzer
import config.ConfigServer as Cs

class PositionAnalysisHandler(BaseHandler):
    """持仓分析处理器"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.tushare_token = Cs.getTushareToken()
        self.analyzer = PositionAnalyzer(self.tushare_token)
    
    async def get(self):
        """获取持仓分析"""
        try:
            # 获取请求参数
            account_id = self.get_argument("account_id", "")
            include_recommendations = self.get_argument("include_recommendations", "true").lower() == "true"
            
            if not account_id:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "缺少账户ID参数", "data": {}})
            
            # 模拟持仓数据 - 实际应该从数据库或交易系统获取
            positions_data = await self.get_positions_data(account_id)
            
            # 分析持仓
            analysis = await self.analyze_positions(positions_data)
            
            # 构建响应数据
            response_data = self.build_response_data(analysis, include_recommendations)
            
            return self.write({"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": response_data})
            
        except Exception as e:
            print(f"持仓分析失败: {e}")
            return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"持仓分析失败: {str(e)}", "data": {}})
    
    async def post(self):
        """提交持仓数据进行分析"""
        try:
            # 获取请求体数据
            request_data = json.loads(self.request.body)
            positions_data = request_data.get("positions", [])
            cash = request_data.get("cash", 0.0)
            
            if not positions_data:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "缺少持仓数据", "data": {}})
            
            # 分析持仓
            analysis = await self.analyze_positions(positions_data, cash)
            
            # 构建响应数据
            response_data = self.build_response_data(analysis, True)
            
            return self.write({"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": response_data})
            
        except Exception as e:
            print(f"持仓分析失败: {e}")
            return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"持仓分析失败: {str(e)}", "data": {}})
    
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
    """持仓明细处理器"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.tushare_token = Cs.getTushareToken()
        self.analyzer = PositionAnalyzer(self.tushare_token)
    
    async def get(self):
        """获取持仓明细"""
        try:
            account_id = self.get_argument("account_id", "")
            symbol = self.get_argument("symbol", "")
            
            if not account_id:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "缺少账户ID参数", "data": {}})
            
            # 获取持仓明细
            positions_data = await self.get_positions_data(account_id)
            
            if symbol:
                # 获取特定股票的持仓
                position_data = next((p for p in positions_data if p["symbol"] == symbol), None)
                if not position_data:
                    return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"未找到股票 {symbol} 的持仓", "data": {}})
                
                # 分析单个持仓
                analysis = await self.analyze_positions([position_data])
                position = analysis.summary.positions[0] if analysis.summary.positions else None
                
                if position:
                    response_data = {
                        "symbol": position.symbol,
                        "volume": position.volume,
                        "available_volume": position.available_volume,
                        "avg_price": round(position.avg_price, 2),
                        "current_price": round(position.current_price, 2),
                        "market_value": round(position.market_value, 2),
                        "cost_value": round(position.cost_value, 2),
                        "unrealized_pnl": round(position.unrealized_pnl, 2),
                        "unrealized_pnl_pct": round(position.unrealized_pnl_pct, 2),
                        "create_time": position.create_time.isoformat(),
                        "update_time": position.update_time.isoformat()
                    }
                else:
                    return self.write({"code": Status.UNKNOWN_ERROR, "msg": "持仓数据异常", "data": {}})
            else:
                # 获取所有持仓明细
                analysis = await self.analyze_positions(positions_data)
                response_data = {
                    "positions": [
                        {
                            "symbol": pos.symbol,
                            "volume": pos.volume,
                            "available_volume": pos.available_volume,
                            "avg_price": round(pos.avg_price, 2),
                            "current_price": round(pos.current_price, 2),
                            "market_value": round(pos.market_value, 2),
                            "cost_value": round(pos.cost_value, 2),
                            "unrealized_pnl": round(pos.unrealized_pnl, 2),
                            "unrealized_pnl_pct": round(pos.unrealized_pnl_pct, 2),
                            "create_time": pos.create_time.isoformat(),
                            "update_time": pos.update_time.isoformat()
                        }
                        for pos in analysis.summary.positions
                    ]
                }
            
            return self.write({"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": response_data})
            
        except Exception as e:
            print(f"获取持仓明细失败: {e}")
            return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"获取持仓明细失败: {str(e)}", "data": {}})
    
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
    """持仓报告处理器"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        config_data = Cs.returnConfigData()
        self.tushare_token = config_data.get("toshare_token", "")
        self.analyzer = PositionAnalyzer(self.tushare_token)
    
    async def get(self):
        """生成持仓报告"""
        try:
            account_id = self.get_argument("account_id", "")
            report_type = self.get_argument("type", "summary")  # summary, detailed, risk
            
            if not account_id:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "缺少账户ID参数", "data": {}})
            
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
            else:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "不支持的报告类型", "data": {}})
            
            return self.write({"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": report})
            
        except Exception as e:
            print(f"生成持仓报告失败: {e}")
            return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"生成持仓报告失败: {str(e)}", "data": {}})
    
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
            "report_type": "summary",
            "generated_time": datetime.now().isoformat(),
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
            "recommendations": analysis.recommendations[:3]  # 只显示前3条建议
        }
    
    def generate_detailed_report(self, analysis: PositionAnalysis) -> Dict[str, Any]:
        """生成详细报告"""
        return {
            "report_type": "detailed",
            "generated_time": datetime.now().isoformat(),
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
            "report_type": "risk",
            "generated_time": datetime.now().isoformat(),
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
            ]
        }
    
    def assess_risk_level(self, risk) -> str:
        """评估风险等级"""
        if risk.risk_level.value == "high":
            return "高风险 - 建议立即调整持仓结构"
        elif risk.risk_level.value == "medium":
            return "中等风险 - 建议适当优化持仓"
        else:
            return "低风险 - 持仓结构相对合理" 