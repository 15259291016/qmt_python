import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import tushare as ts
from scipy import stats

from ..model.position_model import (
    Position, PositionSummary, PositionRisk, PositionAnalysis, 
    PositionType, RiskLevel
)

class PositionAnalyzer:
    """持仓分析器"""
    
    def __init__(self, tushare_token: str):
        self.pro = ts.pro_api(tushare_token)
        self.tushare_token = tushare_token # 新增：存储tushare_token
        
    def calculate_position_metrics(self, position: Position) -> Position:
        """计算单个持仓的指标"""
        # 计算市值和成本
        position.market_value = float(position.volume * position.current_price)
        position.cost_value = float(position.volume * position.avg_price)
        
        # 计算未实现盈亏
        position.unrealized_pnl = position.market_value - position.cost_value
        position.unrealized_pnl_pct = float((position.unrealized_pnl / position.cost_value * 100) if position.cost_value > 0 else 0)
        
        return position
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """获取当前价格"""
        prices = {}
        try:
            # 获取实时价格数据
            for symbol in symbols:
                try:
                    # 获取最新日线数据
                    df = self.pro.daily(ts_code=symbol, limit=1)
                    if not df.empty:
                        prices[symbol] = df['close'].iloc[0]
                    else:
                        prices[symbol] = 0.0
                except Exception as e:
                    print(f"获取 {symbol} 价格失败: {e}")
                    prices[symbol] = 0.0
        except Exception as e:
            print(f"获取价格数据失败: {e}")
            
        return prices
    
    def analyze_positions(self, positions_data: List[Dict], cash: float = 0.0) -> PositionAnalysis:
        """分析持仓"""
        # 转换数据格式
        positions = []
        symbols = []
        
        for pos_data in positions_data:
            position = Position(
                symbol=pos_data.get('symbol', ''),
                volume=pos_data.get('volume', 0),
                available_volume=pos_data.get('available_volume', 0),
                avg_price=pos_data.get('avg_price', 0.0),
                current_price=pos_data.get('current_price', 0.0),
                position_type=PositionType.LONG
            )
            positions.append(position)
            symbols.append(position.symbol)
        
        # 获取当前价格
        current_prices = self.get_current_prices(symbols)
        
        # 更新价格并计算指标
        for position in positions:
            if position.symbol in current_prices:
                position.current_price = current_prices[position.symbol]
            position = self.calculate_position_metrics(position)
        
        # 计算汇总信息
        summary = self.calculate_summary(positions, cash)
        
        # 计算风险指标
        risk = self.calculate_risk_metrics(positions, summary)
        
        # 获取主要持仓
        top_positions = self.get_top_positions(positions)
        
        # 计算行业分布
        sector_distribution = self.calculate_sector_distribution(positions)
        
        # 计算绩效指标
        performance_metrics = self.calculate_performance_metrics(positions, summary)
        
        # 生成调整建议
        recommendations = self.generate_recommendations(positions, risk, summary)
        
        return PositionAnalysis(
            summary=summary,
            risk=risk,
            top_positions=top_positions,
            sector_distribution=sector_distribution,
            performance_metrics=performance_metrics,
            recommendations=recommendations
        )
    
    def calculate_fear_greed_index(self) -> float:
        """基于全市场数据估算恐贪指数，0-100"""
        try:
            import tushare as ts
            pro = ts.pro_api(self.tushare_token)
            from datetime import datetime
            today = datetime.now().strftime('%Y%m%d')
            # 1. 涨跌家数
            daily = pro.daily(trade_date=today)
            up_count = (daily['pct_chg'] > 0).sum()
            down_count = (daily['pct_chg'] < 0).sum()
            total_count = len(daily)
            up_ratio = up_count / total_count if total_count else 0.5
            # 2. 涨停/跌停家数
            limit_up_count = (daily['pct_chg'] > 9.5).sum()
            limit_down_count = (daily['pct_chg'] < -9.5).sum()
            limit_ratio = (limit_up_count - limit_down_count) / total_count if total_count else 0
            # 3. 成交额（与近20日均值对比）
            money = daily['amount'].sum() if 'amount' in daily.columns else 0
            hist = pro.daily(trade_date=(datetime.now() - pd.Timedelta(days=20)).strftime('%Y%m%d'))
            hist_money = hist['amount'].sum() if 'amount' in hist.columns else 1
            money_ratio = money / hist_money if hist_money else 1
            # 综合归一化（可根据实际调整权重）
            idx = 50 + 30 * (up_ratio - 0.5) + 10 * limit_ratio + 10 * (money_ratio - 1)
            idx = min(max(idx, 0), 100)
            return idx
        except Exception as e:
            print(f"[恐贪指数] 全市场数据获取失败，使用持仓估算法: {e}")
            return None

    def calculate_long_term_fear_greed_index(self, window: int = 20) -> float:
        """
        计算长期恐贪指数（近window日均值），批量获取历史数据，避免逐日API调用。
        """
        try:
            import tushare as ts
            pro = ts.pro_api(self.tushare_token)
            from datetime import datetime, timedelta
            import pandas as pd

            today = datetime.now()
            start_date = (today - timedelta(days=window*2)).strftime('%Y%m%d')  # 多取几天防止节假日
            end_date = today.strftime('%Y%m%d')
            # 批量获取近window*2天的所有A股daily数据
            daily_all = pro.daily(start_date=start_date, end_date=end_date)
            if daily_all is None or daily_all.empty:
                return None
            # 只保留最近window个交易日
            trade_dates = sorted(daily_all['trade_date'].unique(), reverse=True)[:window]
            idx_list = []
            # 近window日均成交额
            if 'amount' in daily_all.columns:
                hist_money = daily_all[daily_all['trade_date'].isin(trade_dates)]['amount'].sum() / window
            else:
                hist_money = 1
            for trade_date in trade_dates:
                daily = daily_all[daily_all['trade_date'] == trade_date]
                if daily is None or daily.empty:
                    continue
                up_count = (daily['pct_chg'] > 0).sum()
                down_count = (daily['pct_chg'] < 0).sum()
                total_count = len(daily)
                up_ratio = up_count / total_count if total_count else 0.5
                limit_up_count = (daily['pct_chg'] > 9.5).sum()
                limit_down_count = (daily['pct_chg'] < -9.5).sum()
                limit_ratio = (limit_up_count - limit_down_count) / total_count if total_count else 0
                money = daily['amount'].sum() if 'amount' in daily.columns else 0
                money_ratio = money / hist_money if hist_money else 1
                idx = 50 + 30 * (up_ratio - 0.5) + 10 * limit_ratio + 10 * (money_ratio - 1)
                idx = min(max(idx, 0), 100)
                idx_list.append(idx)
            if idx_list:
                return float(np.mean(idx_list))
            else:
                return None
        except Exception as e:
            print(f"[长期恐贪指数] 获取失败: {e}")
            return None

    def calculate_summary(self, positions: List[Position], cash: float) -> PositionSummary:
        """计算持仓汇总，增加恐贪指数"""
        total_positions = len(positions)
        total_market_value = sum(p.market_value for p in positions)
        total_cost_value = sum(p.cost_value for p in positions)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in positions)
        total_unrealized_pnl_pct = (total_unrealized_pnl / total_cost_value * 100) if total_cost_value > 0 else 0
        total_asset = total_market_value + cash

        # 优先用全市场恐贪指数
        fear_greed_index = self.calculate_fear_greed_index()
        # 长期恐贪指数
        long_term_fear_greed_index = self.calculate_long_term_fear_greed_index(window=20)
        if long_term_fear_greed_index is None:
            long_term_fear_greed_index = fear_greed_index
        # 若全市场不可用，回退到持仓估算
        if fear_greed_index is None:
            if positions:
                avg_pnl = np.mean([p.unrealized_pnl_pct for p in positions])
                pos_ratio = sum(1 for p in positions if p.unrealized_pnl_pct > 0) / len(positions)
                fear_greed_index = min(max((avg_pnl + 10 * (pos_ratio - 0.5)) * 2 + 50, 0), 100)
            else:
                fear_greed_index = 50
            long_term_fear_greed_index = fear_greed_index

        return PositionSummary(
            total_positions=total_positions,
            total_market_value=total_market_value,
            total_cost_value=total_cost_value,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_pct=total_unrealized_pnl_pct,
            cash=cash,
            total_asset=total_asset,
            positions=positions,
            fear_greed_index=fear_greed_index,
            long_term_fear_greed_index=long_term_fear_greed_index
        )
    
    def calculate_risk_metrics(self, positions: List[Position], summary: PositionSummary) -> PositionRisk:
        """计算风险指标"""
        if not positions:
            return PositionRisk(
                concentration_risk=0.0,
                sector_concentration=0.0,
                volatility_risk=0.0,
                beta_risk=0.0,
                var_95=0.0,
                max_drawdown=0.0,
                risk_level=RiskLevel.LOW
            )
        
        # 集中度风险 - 最大单只股票权重
        weights = [p.market_value / summary.total_market_value for p in positions if summary.total_market_value > 0]
        concentration_risk = max(weights) if weights else 0.0
        
        # 行业集中度 - 简化处理，假设所有股票在同一行业
        sector_concentration = 1.0  # 实际应该根据行业分类计算
        
        # 波动率风险 - 基于持仓盈亏率的波动
        pnl_rates = [p.unrealized_pnl_pct for p in positions]
        volatility_risk = float(np.std(pnl_rates) if len(pnl_rates) > 1 else 0.0)
        
        # Beta风险 - 简化处理
        beta_risk = 1.0  # 实际应该计算组合Beta
        
        # VaR计算 - 简化处理
        var_95 = float(np.percentile(pnl_rates, 5) if pnl_rates else 0.0)
        
        # 最大回撤 - 基于当前盈亏
        max_drawdown = min(pnl_rates) if pnl_rates else 0.0
        
        # 风险等级评估
        risk_score = (concentration_risk * 0.3 + 
                     sector_concentration * 0.2 + 
                     volatility_risk * 0.2 + 
                     abs(var_95) * 0.3)
        
        if risk_score < 0.3:
            risk_level = RiskLevel.LOW
        elif risk_score < 0.6:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        return PositionRisk(
            concentration_risk=concentration_risk,
            sector_concentration=sector_concentration,
            volatility_risk=volatility_risk,
            beta_risk=beta_risk,
            var_95=var_95,
            max_drawdown=max_drawdown,
            risk_level=risk_level
        )
    
    def get_top_positions(self, positions: List[Position], top_n: int = 5) -> List[Position]:
        """获取主要持仓"""
        # 按市值排序
        sorted_positions = sorted(positions, key=lambda x: x.market_value, reverse=True)
        return sorted_positions[:top_n]
    
    def calculate_sector_distribution(self, positions: List[Position]) -> Dict[str, float]:
        """计算行业分布"""
        # 简化处理，实际应该根据股票代码获取行业信息
        sector_distribution = {"其他": 100.0}
        return sector_distribution
    
    def calculate_performance_metrics(self, positions: List[Position], summary: PositionSummary) -> Dict[str, float]:
        """计算绩效指标"""
        if not positions:
            return {}
        
        # 计算各种绩效指标
        metrics = {
            "总收益率": summary.total_unrealized_pnl_pct,
            "平均收益率": np.mean([p.unrealized_pnl_pct for p in positions]),
            "收益率标准差": np.std([p.unrealized_pnl_pct for p in positions]),
            "最大单笔收益": max([p.unrealized_pnl_pct for p in positions]),
            "最大单笔亏损": min([p.unrealized_pnl_pct for p in positions]),
            "盈利持仓比例": len([p for p in positions if p.unrealized_pnl > 0]) / len(positions) * 100,
            "持仓集中度": max([p.market_value / summary.total_market_value for p in positions]) if summary.total_market_value > 0 else 0
        }
        
        return metrics
    
    def generate_recommendations(self, positions: List[Position], risk: PositionRisk, summary: PositionSummary) -> List[str]:
        """生成调整建议，加入恐贪指数分析"""
        recommendations = []
        
        # 恐贪指数分析（假设summary.fear_greed_index已赋值，范围0-100）
        if hasattr(summary, 'fear_greed_index'):
            idx = summary.fear_greed_index
            if idx <= 20:
                recommendations.append("当前市场极度恐慌，建议保持冷静，勿盲目割肉，可适当关注优质资产的低吸机会。")
            elif idx <= 40:
                recommendations.append("市场偏恐慌，操作宜谨慎，可逐步布局防御性板块。")
            elif idx <= 60:
                recommendations.append("市场情绪中性，建议按计划稳健操作，合理控制仓位。")
            elif idx <= 80:
                recommendations.append("市场偏贪婪，注意防范追高风险，适当锁定部分收益。")
            else:
                recommendations.append("市场极度贪婪，风险加大，建议逐步减仓，防止回撤。")
        
        # 基于集中度风险的建议
        if risk.concentration_risk > 0.2:
            recommendations.append("建议降低单只股票持仓集中度，分散投资风险")
        
        # 基于行业集中度的建议
        if risk.sector_concentration > 0.5:
            recommendations.append("建议增加行业分散度，避免行业集中风险")
        
        # 基于波动率风险的建议
        if risk.volatility_risk > 10:
            recommendations.append("持仓波动率较高，建议增加稳定性资产配置")
        
        # 基于整体盈亏的建议
        if summary.total_unrealized_pnl_pct < -10:
            recommendations.append("整体亏损较大，建议重新评估持仓策略")
        elif summary.total_unrealized_pnl_pct > 20:
            recommendations.append("盈利较好，建议适当止盈锁定收益")
        
        # 基于持仓数量的建议
        if summary.total_positions < 5:
            recommendations.append("持仓数量较少，建议适当增加持仓分散度")
        elif summary.total_positions > 20:
            recommendations.append("持仓数量较多，建议精简持仓提高管理效率")
        
        # 基于现金比例的建议
        cash_ratio = summary.cash / summary.total_asset if summary.total_asset > 0 else 0
        if cash_ratio < 0.1:
            recommendations.append("现金比例较低，建议保持适当流动性")
        elif cash_ratio > 0.5:
            recommendations.append("现金比例较高，建议适当增加投资配置")
        
        return recommendations 