import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import io
import base64

from ..model.position_model import PositionAnalysis, Position

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class PositionVisualizer:
    """持仓可视化工具"""
    
    def __init__(self):
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
    
    def create_position_summary_chart(self, analysis: PositionAnalysis) -> str:
        """创建持仓汇总图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 资产配置饼图
        labels = ['股票持仓', '现金']
        sizes = [analysis.summary.total_market_value, analysis.summary.cash]
        colors = ['#FF6B6B', '#4ECDC4']
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('资产配置分布')
        
        # 2. 持仓盈亏柱状图
        positions = analysis.top_positions[:5]  # 取前5个持仓
        symbols = [pos.symbol for pos in positions]
        pnl_pcts = [pos.unrealized_pnl_pct for pos in positions]
        colors = ['green' if pnl >= 0 else 'red' for pnl in pnl_pcts]
        
        bars = ax2.bar(symbols, pnl_pcts, color=colors, alpha=0.7)
        ax2.set_title('主要持仓盈亏率')
        ax2.set_ylabel('盈亏率 (%)')
        ax2.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, pnl in zip(bars, pnl_pcts):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{pnl:.1f}%', ha='center', va='bottom' if pnl >= 0 else 'top')
        
        # 3. 风险指标雷达图
        risk_metrics = {
            '集中度风险': analysis.risk.concentration_risk * 100,
            '行业集中度': analysis.risk.sector_concentration * 100,
            '波动率风险': analysis.risk.volatility_risk,
            'Beta风险': analysis.risk.beta_risk,
            'VaR(95%)': abs(analysis.risk.var_95)
        }
        
        categories = list(risk_metrics.keys())
        values = list(risk_metrics.values())
        
        # 雷达图
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # 闭合图形
        angles += angles[:1]
        
        ax3.plot(angles, values, 'o-', linewidth=2, color='#45B7D1')
        ax3.fill(angles, values, alpha=0.25, color='#45B7D1')
        ax3.set_xticks(angles[:-1])
        ax3.set_xticklabels(categories)
        ax3.set_title('风险指标雷达图')
        ax3.grid(True)
        
        # 4. 绩效指标表格
        performance_data = [
            ['总收益率', f"{analysis.summary.total_unrealized_pnl_pct:.2f}%"],
            ['持仓数量', str(analysis.summary.total_positions)],
            ['总市值', f"¥{analysis.summary.total_market_value:,.0f}"],
            ['风险等级', analysis.risk.risk_level.value.upper()]
        ]
        
        table = ax4.table(cellText=performance_data, 
                         colLabels=['指标', '数值'],
                         cellLoc='center',
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2)
        ax4.axis('off')
        ax4.set_title('关键绩效指标')
        
        plt.tight_layout()
        
        # 转换为base64字符串
        return self._fig_to_base64(fig)
    
    def create_position_detail_chart(self, analysis: PositionAnalysis) -> str:
        """创建持仓详细图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        positions = analysis.summary.positions
        
        # 1. 持仓市值分布
        symbols = [pos.symbol for pos in positions]
        market_values = [pos.market_value for pos in positions]
        
        bars = ax1.bar(symbols, market_values, color=self.colors[:len(symbols)])
        ax1.set_title('持仓市值分布')
        ax1.set_ylabel('市值 (元)')
        ax1.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, value in zip(bars, market_values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'¥{value:,.0f}', ha='center', va='bottom')
        
        # 2. 盈亏分布散点图
        market_values = [pos.market_value for pos in positions]
        pnl_pcts = [pos.unrealized_pnl_pct for pos in positions]
        colors = ['green' if pnl >= 0 else 'red' for pnl in pnl_pcts]
        
        ax2.scatter(market_values, pnl_pcts, c=colors, s=100, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_xlabel('市值 (元)')
        ax2.set_ylabel('盈亏率 (%)')
        ax2.set_title('持仓盈亏分布')
        
        # 添加股票代码标签
        for i, symbol in enumerate(symbols):
            ax2.annotate(symbol, (market_values[i], pnl_pcts[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 3. 持仓权重饼图
        total_mv = analysis.summary.total_market_value
        weights = [pos.market_value / total_mv * 100 for pos in positions]
        
        ax3.pie(weights, labels=symbols, autopct='%1.1f%%', startangle=90)
        ax3.set_title('持仓权重分布')
        
        # 4. 成本vs现价对比
        avg_prices = [pos.avg_price for pos in positions]
        current_prices = [pos.current_price for pos in positions]
        
        x = np.arange(len(symbols))
        width = 0.35
        
        bars1 = ax4.bar(x - width/2, avg_prices, width, label='平均成本', color='#FF6B6B', alpha=0.7)
        bars2 = ax4.bar(x + width/2, current_prices, width, label='当前价格', color='#4ECDC4', alpha=0.7)
        
        ax4.set_xlabel('股票')
        ax4.set_ylabel('价格 (元)')
        ax4.set_title('成本vs现价对比')
        ax4.set_xticks(x)
        ax4.set_xticklabels(symbols, rotation=45)
        ax4.legend()
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def create_risk_analysis_chart(self, analysis: PositionAnalysis) -> str:
        """创建风险分析图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 风险等级评估
        risk_levels = ['低风险', '中等风险', '高风险']
        risk_colors = ['#4ECDC4', '#FFEAA7', '#FF6B6B']
        
        # 根据风险等级确定颜色
        risk_level = analysis.risk.risk_level.value
        if risk_level == 'low':
            risk_color = risk_colors[0]
            risk_index = 0
        elif risk_level == 'medium':
            risk_color = risk_colors[1]
            risk_index = 1
        else:
            risk_color = risk_colors[2]
            risk_index = 2
        
        # 创建风险等级指示器
        risk_values = [0, 0, 0]
        risk_values[risk_index] = 1
        
        bars = ax1.bar(risk_levels, risk_values, color=risk_colors, alpha=0.7)
        ax1.set_title('风险等级评估')
        ax1.set_ylabel('风险等级')
        ax1.set_ylim(0, 1.2)
        
        # 添加风险等级标签
        ax1.text(risk_index, 1.1, f'当前: {risk_levels[risk_index]}', 
                ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 2. 风险指标对比
        risk_metrics = {
            '集中度风险': analysis.risk.concentration_risk * 100,
            '行业集中度': analysis.risk.sector_concentration * 100,
            '波动率风险': analysis.risk.volatility_risk,
            'VaR(95%)': abs(analysis.risk.var_95)
        }
        
        metrics = list(risk_metrics.keys())
        values = list(risk_metrics.values())
        
        bars = ax2.bar(metrics, values, color='#45B7D1', alpha=0.7)
        ax2.set_title('风险指标详情')
        ax2.set_ylabel('风险值')
        ax2.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.2f}', ha='center', va='bottom')
        
        # 3. 持仓集中度分析
        positions = analysis.summary.positions
        if positions:
            weights = [pos.market_value / analysis.summary.total_market_value * 100 for pos in positions]
            symbols = [pos.symbol for pos in positions]
            
            # 按权重排序
            sorted_data = sorted(zip(symbols, weights), key=lambda x: x[1], reverse=True)
            symbols, weights = zip(*sorted_data)
            
            bars = ax3.bar(symbols, weights, color=self.colors[:len(symbols)])
            ax3.set_title('持仓集中度分析')
            ax3.set_ylabel('权重 (%)')
            ax3.tick_params(axis='x', rotation=45)
            
            # 添加警戒线
            ax3.axhline(y=20, color='red', linestyle='--', alpha=0.7, label='20%警戒线')
            ax3.axhline(y=10, color='orange', linestyle='--', alpha=0.7, label='10%建议线')
            ax3.legend()
        
        # 4. 盈亏分布直方图
        if positions:
            pnl_pcts = [pos.unrealized_pnl_pct for pos in positions]
            
            ax4.hist(pnl_pcts, bins=min(10, len(pnl_pcts)), color='#96CEB4', alpha=0.7, edgecolor='black')
            ax4.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='盈亏平衡线')
            ax4.set_title('盈亏分布直方图')
            ax4.set_xlabel('盈亏率 (%)')
            ax4.set_ylabel('持仓数量')
            ax4.legend()
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def create_performance_chart(self, analysis: PositionAnalysis) -> str:
        """创建绩效分析图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        positions = analysis.summary.positions
        
        if positions:
            # 1. 收益率排名
            symbols = [pos.symbol for pos in positions]
            pnl_pcts = [pos.unrealized_pnl_pct for pos in positions]
            
            # 按收益率排序
            sorted_data = sorted(zip(symbols, pnl_pcts), key=lambda x: x[1], reverse=True)
            symbols, pnl_pcts = zip(*sorted_data)
            
            colors = ['green' if pnl >= 0 else 'red' for pnl in pnl_pcts]
            bars = ax1.bar(symbols, pnl_pcts, color=colors, alpha=0.7)
            ax1.set_title('持仓收益率排名')
            ax1.set_ylabel('收益率 (%)')
            ax1.tick_params(axis='x', rotation=45)
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            # 2. 市值vs收益率散点图
            market_values = [pos.market_value for pos in positions]
            pnl_pcts = [pos.unrealized_pnl_pct for pos in positions]
            
            ax2.scatter(market_values, pnl_pcts, s=100, alpha=0.7, c=colors)
            ax2.set_xlabel('市值 (元)')
            ax2.set_ylabel('收益率 (%)')
            ax2.set_title('市值vs收益率关系')
            ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            
            # 3. 盈利vs亏损持仓对比
            profit_positions = [pos for pos in positions if pos.unrealized_pnl > 0]
            loss_positions = [pos for pos in positions if pos.unrealized_pnl < 0]
            
            profit_count = len(profit_positions)
            loss_count = len(loss_positions)
            
            labels = ['盈利持仓', '亏损持仓']
            sizes = [profit_count, loss_count]
            colors_pie = ['#4ECDC4', '#FF6B6B']
            
            ax3.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
            ax3.set_title('盈利vs亏损持仓分布')
            
            # 4. 绩效指标仪表盘
            metrics = analysis.performance_metrics
            
            # 创建仪表盘样式的图表
            metric_names = ['总收益率', '平均收益率', '盈利持仓比例']
            metric_values = [
                metrics.get('总收益率', 0),
                metrics.get('平均收益率', 0),
                metrics.get('盈利持仓比例', 0)
            ]
            
            # 创建进度条样式的图表
            y_pos = np.arange(len(metric_names))
            bars = ax4.barh(y_pos, metric_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
            ax4.set_yticks(y_pos)
            ax4.set_yticklabels(metric_names)
            ax4.set_xlabel('数值')
            ax4.set_title('关键绩效指标')
            
            # 添加数值标签
            for i, (bar, value) in enumerate(zip(bars, metric_values)):
                width = bar.get_width()
                ax4.text(width, bar.get_y() + bar.get_height()/2,
                        f'{value:.2f}', ha='left', va='center')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """将matplotlib图表转换为base64字符串"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode()
        plt.close(fig)
        return img_str
    
    def generate_comprehensive_report(self, analysis: PositionAnalysis) -> Dict[str, str]:
        """生成综合报告，包含所有图表"""
        return {
            "summary_chart": self.create_position_summary_chart(analysis),
            "detail_chart": self.create_position_detail_chart(analysis),
            "risk_chart": self.create_risk_analysis_chart(analysis),
            "performance_chart": self.create_performance_chart(analysis)
        } 