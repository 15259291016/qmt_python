import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from tornado.web import RequestHandler
from modules.tornadoapp.define.base.handler import BaseHandler
from ..define.enum.response_model import Status, Message
from ..position.xtquant_position_manager import XtQuantPositionManager
import config.ConfigServer as Cs

class TechnicalAnalysisHandler(BaseHandler):
    """技术分析处理器"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.tushare_token = Cs.getTushareToken()
        self.position_manager = XtQuantPositionManager(self.tushare_token)
    
    async def get(self):
        """获取技术分析结果"""
        try:
            # 获取请求参数
            account_id = self.get_argument("account_id", "")
            symbol = self.get_argument("symbol", "")
            
            if not account_id:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "缺少账户ID参数", "data": {}})
            
            if symbol:
                # 分析特定股票
                result = await self.analyze_single_stock(account_id, symbol)
            else:
                # 分析所有持仓
                result = await self.analyze_all_positions(account_id)
            
            return self.write({"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": result})
            
        except Exception as e:
            print(f"技术分析失败: {e}")
            return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"技术分析失败: {str(e)}", "data": {}})
    
    async def post(self):
        """提交持仓数据进行技术分析"""
        try:
            # 获取请求体数据
            request_data = json.loads(self.request.body)
            positions_data = request_data.get("positions", [])
            account_id = request_data.get("account_id", "demo")
            
            if not positions_data:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "缺少持仓数据", "data": {}})
            
            # 分析持仓
            result = await self.analyze_custom_positions(positions_data, account_id)
            
            return self.write({"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": result})
            
        except Exception as e:
            print(f"技术分析失败: {e}")
            return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"技术分析失败: {str(e)}", "data": {}})
    
    async def analyze_single_stock(self, account_id: str, symbol: str) -> Dict[str, Any]:
        """分析单个股票"""
        # 获取持仓数据
        positions = await self.position_manager.get_xtquant_positions(account_id)
        
        # 找到指定股票的持仓
        target_position = None
        for pos in positions:
            if pos['symbol'] == symbol:
                target_position = pos
                break
        
        if not target_position:
            return {
                "symbol": symbol,
                "error": f"未找到股票 {symbol} 的持仓",
                "analysis_time": datetime.now().isoformat()
            }
        
        # 进行技术分析
        analysis = await self.position_manager.analyze_position_with_technical_analysis(target_position)
        
        return analysis
    
    async def analyze_all_positions(self, account_id: str) -> Dict[str, Any]:
        """分析所有持仓"""
        # 获取所有持仓的技术分析
        analysis_results = await self.position_manager.analyze_all_positions(account_id)
        
        # 生成交易建议
        recommendations = self.position_manager.generate_trading_recommendations(analysis_results)
        
        # 构建响应数据
        response_data = {
            "account_id": account_id,
            "summary": analysis_results['summary'],
            "positions": [],
            "recommendations": recommendations,
            "analysis_time": analysis_results['analysis_time']
        }
        
        # 格式化持仓数据
        for position in analysis_results['positions']:
            formatted_position = {
                "symbol": position['symbol'],
                "current_price": round(position['current_price'], 2),
                "avg_price": round(position['avg_price'], 2),
                "pnl_pct": round((position['current_price'] - position['avg_price']) / position['avg_price'] * 100, 2),
                "action": position['signals']['action'],
                "confidence": round(position['signals']['confidence'], 2),
                "target_price": round(position['signals']['target_price'], 2),
                "stop_loss": round(position['signals']['stop_loss'], 2),
                "reasons": position['signals']['reasons'],
                "key_indicators": {
                    "rsi": round(position['indicators'].get('rsi', 0), 2),
                    "macd": round(position['indicators'].get('macd', 0), 4),
                    "ma20": round(position['indicators'].get('ma20', 0), 2),
                    "bb_position": round(position['indicators'].get('price_position', 0.5), 2)
                }
            }
            response_data["positions"].append(formatted_position)
        
        return response_data
    
    async def analyze_custom_positions(self, positions_data: List[Dict], account_id: str) -> Dict[str, Any]:
        """分析自定义持仓数据"""
        # 分析每个持仓
        analysis_results = []
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        for position in positions_data:
            analysis = await self.position_manager.analyze_position_with_technical_analysis(position)
            analysis_results.append(analysis)
            
            # 统计信号
            action = analysis['signals']['action']
            if action == 'buy':
                buy_count += 1
            elif action == 'sell':
                sell_count += 1
            else:
                hold_count += 1
        
        # 生成交易建议
        mock_analysis = {
            'account_id': account_id,
            'positions': analysis_results,
            'summary': {
                'total_positions': len(positions_data),
                'buy_signals': buy_count,
                'sell_signals': sell_count,
                'hold_signals': hold_count
            },
            'analysis_time': datetime.now().isoformat()
        }
        
        recommendations = self.position_manager.generate_trading_recommendations(mock_analysis)
        
        # 构建响应数据
        response_data = {
            "account_id": account_id,
            "summary": mock_analysis['summary'],
            "positions": [],
            "recommendations": recommendations,
            "analysis_time": mock_analysis['analysis_time']
        }
        
        # 格式化持仓数据
        for position in analysis_results:
            formatted_position = {
                "symbol": position['symbol'],
                "current_price": round(position['current_price'], 2),
                "avg_price": round(position['avg_price'], 2),
                "pnl_pct": round((position['current_price'] - position['avg_price']) / position['avg_price'] * 100, 2),
                "action": position['signals']['action'],
                "confidence": round(position['signals']['confidence'], 2),
                "target_price": round(position['signals']['target_price'], 2),
                "stop_loss": round(position['signals']['stop_loss'], 2),
                "reasons": position['signals']['reasons'],
                "key_indicators": {
                    "rsi": round(position['indicators'].get('rsi', 0), 2),
                    "macd": round(position['indicators'].get('macd', 0), 4),
                    "ma20": round(position['indicators'].get('ma20', 0), 2),
                    "bb_position": round(position['indicators'].get('price_position', 0.5), 2)
                }
            }
            response_data["positions"].append(formatted_position)
        
        return response_data

class TradingSignalHandler(BaseHandler):
    """交易信号处理器"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        config_data = Cs.returnConfigData()
        self.tushare_token = config_data.get("toshare_token", "")
        self.position_manager = XtQuantPositionManager(self.tushare_token)
    
    async def get(self):
        """获取交易信号"""
        try:
            account_id = self.get_argument("account_id", "")
            min_confidence = float(self.get_argument("min_confidence", "0.6"))
            
            if not account_id:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "缺少账户ID参数", "data": {}})
            
            # 分析所有持仓
            analysis_results = await self.position_manager.analyze_all_positions(account_id)
            
            # 生成交易建议
            recommendations = self.position_manager.generate_trading_recommendations(analysis_results)
            
            # 过滤低置信度的建议
            filtered_recommendations = [
                rec for rec in recommendations 
                if rec['confidence'] >= min_confidence
            ]
            
            # 按置信度排序
            filtered_recommendations.sort(key=lambda x: x['confidence'], reverse=True)
            
            response_data = {
                "account_id": account_id,
                "min_confidence": min_confidence,
                "total_signals": len(recommendations),
                "filtered_signals": len(filtered_recommendations),
                "signals": filtered_recommendations,
                "analysis_time": analysis_results['analysis_time']
            }
            
            return self.write({"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": response_data})
            
        except Exception as e:
            print(f"获取交易信号失败: {e}")
            return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"获取交易信号失败: {str(e)}", "data": {}})

class IndicatorAnalysisHandler(BaseHandler):
    """技术指标分析处理器"""
    
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        config_data = Cs.returnConfigData()
        self.tushare_token = config_data.get("toshare_token", "")
        self.position_manager = XtQuantPositionManager(self.tushare_token)
    
    async def get(self):
        """获取技术指标分析"""
        try:
            symbol = self.get_argument("symbol", "")
            days = int(self.get_argument("days", "60"))
            
            if not symbol:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": "缺少股票代码参数", "data": {}})
            
            # 获取历史数据
            df = await self.position_manager.get_historical_data(symbol, days)
            
            if df.empty:
                return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"无法获取 {symbol} 的历史数据", "data": {}})
            
            # 计算技术指标
            indicators = self.position_manager.calculate_technical_indicators(df)
            
            # 获取当前价格
            current_price = float(df['close'].iloc[-1])
            
            # 生成交易信号（使用模拟成本价）
            avg_price = current_price * 0.95  # 假设成本价比当前价低5%
            signals = self.position_manager.generate_trading_signals(indicators, current_price, avg_price)
            
            response_data = {
                "symbol": symbol,
                "current_price": round(current_price, 2),
                "analysis_period": f"{days}天",
                "indicators": {
                    k: round(v, 4) if isinstance(v, float) else v
                    for k, v in indicators.items()
                },
                "signals": {
                    "action": signals['action'],
                    "confidence": round(signals['confidence'], 2),
                    "reasons": signals['reasons'],
                    "target_price": round(signals['target_price'], 2),
                    "stop_loss": round(signals['stop_loss'], 2)
                },
                "analysis_time": datetime.now().isoformat()
            }
            
            return self.write({"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": response_data})
            
        except Exception as e:
            print(f"技术指标分析失败: {e}")
            return self.write({"code": Status.UNKNOWN_ERROR, "msg": f"技术指标分析失败: {str(e)}", "data": {}}) 