# coding=utf-8
"""
回测结果分析器
提供详细的绩效分析功能
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from .backtest_engine import BacktestResult

logger = logging.getLogger(__name__)


class BacktestResultsAnalyzer:
    """回测结果分析器"""
    
    def __init__(self, results: Dict[str, BacktestResult]):
        """
        初始化分析器
        
        Args:
            results: 回测结果字典
        """
        self.results = results
        self.analysis_data = self._prepare_analysis_data()
    
    def _prepare_analysis_data(self) -> pd.DataFrame:
        """准备分析数据"""
        data = []
        for strategy_name, result in self.results.items():
            data.append({
                'strategy_name': result.strategy_name,
                'symbol': result.symbol,
                'total_return': result.total_return,
                'annual_return': result.annual_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'profit_trades': result.profit_trades,
                'loss_trades': result.loss_trades,
                'avg_profit': result.avg_profit,
                'avg_loss': result.avg_loss,
                'profit_factor': result.profit_factor,
                'initial_cash': result.initial_cash,
                'final_value': result.final_value
            })
        
        return pd.DataFrame(data)
    
    def get_performance_summary(self) -> pd.DataFrame:
        """获取性能摘要"""
        return self.analysis_data.copy()
    
    def get_best_strategy(self, metric: str = 'total_return') -> str:
        """获取最佳策略"""
        if metric == 'total_return':
            best_idx = self.analysis_data['total_return'].idxmax()
        elif metric == 'sharpe_ratio':
            best_idx = self.analysis_data['sharpe_ratio'].idxmax()
        elif metric == 'win_rate':
            best_idx = self.analysis_data['win_rate'].idxmax()
        elif metric == 'profit_factor':
            best_idx = self.analysis_data['profit_factor'].idxmax()
        else:
            raise ValueError(f"不支持的指标: {metric}")
        
        return self.analysis_data.loc[best_idx, 'strategy_name']
    
    def get_risk_metrics(self) -> pd.DataFrame:
        """获取风险指标"""
        risk_metrics = self.analysis_data[['strategy_name', 'max_drawdown', 'sharpe_ratio']].copy()
        risk_metrics['volatility'] = self._calculate_volatility()
        risk_metrics['var_95'] = self._calculate_var(0.95)
        risk_metrics['var_99'] = self._calculate_var(0.99)
        
        return risk_metrics
    
    def _calculate_volatility(self) -> pd.Series:
        """计算波动率"""
        # 这里需要从权益曲线计算，暂时返回估计值
        return self.analysis_data['max_drawdown'] * 2  # 简单估计
    
    def _calculate_var(self, confidence_level: float) -> pd.Series:
        """计算 VaR"""
        # 这里需要从权益曲线计算，暂时返回估计值
        return self.analysis_data['max_drawdown'] * confidence_level
    
    def get_trading_metrics(self) -> pd.DataFrame:
        """获取交易指标"""
        trading_metrics = self.analysis_data[[
            'strategy_name', 'total_trades', 'profit_trades', 'loss_trades',
            'win_rate', 'avg_profit', 'avg_loss', 'profit_factor'
        ]].copy()
        
        # 计算额外指标
        trading_metrics['avg_trade_duration'] = self._estimate_trade_duration()
        trading_metrics['profit_loss_ratio'] = trading_metrics['avg_profit'] / abs(trading_metrics['avg_loss'])
        
        return trading_metrics
    
    def _estimate_trade_duration(self) -> pd.Series:
        """估计平均交易持续时间"""
        # 这里需要从交易历史计算，暂时返回估计值
        return pd.Series([5] * len(self.analysis_data))  # 假设平均5天
    
    def plot_performance_comparison(self, save_path: str = None):
        """绘制性能对比图"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 总收益率对比
        axes[0, 0].bar(self.analysis_data['strategy_name'], 
                       self.analysis_data['total_return'] * 100)
        axes[0, 0].set_title('总收益率对比')
        axes[0, 0].set_ylabel('收益率 (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 夏普比率对比
        axes[0, 1].bar(self.analysis_data['strategy_name'], 
                       self.analysis_data['sharpe_ratio'])
        axes[0, 1].set_title('夏普比率对比')
        axes[0, 1].set_ylabel('夏普比率')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 最大回撤对比
        axes[1, 0].bar(self.analysis_data['strategy_name'], 
                       self.analysis_data['max_drawdown'] * 100)
        axes[1, 0].set_title('最大回撤对比')
        axes[1, 0].set_ylabel('回撤 (%)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 胜率对比
        axes[1, 1].bar(self.analysis_data['strategy_name'], 
                       self.analysis_data['win_rate'] * 100)
        axes[1, 1].set_title('胜率对比')
        axes[1, 1].set_ylabel('胜率 (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"性能对比图已保存到: {save_path}")
        else:
            plt.show()
    
    def plot_risk_return_scatter(self, save_path: str = None):
        """绘制风险收益散点图"""
        plt.figure(figsize=(10, 8))
        
        scatter = plt.scatter(
            self.analysis_data['max_drawdown'] * 100,
            self.analysis_data['total_return'] * 100,
            s=self.analysis_data['sharpe_ratio'] * 100,  # 气泡大小基于夏普比率
            alpha=0.7,
            c=self.analysis_data['win_rate'] * 100,  # 颜色基于胜率
            cmap='viridis'
        )
        
        # 添加策略名称标签
        for i, strategy_name in enumerate(self.analysis_data['strategy_name']):
            plt.annotate(strategy_name, 
                        (self.analysis_data['max_drawdown'].iloc[i] * 100,
                         self.analysis_data['total_return'].iloc[i] * 100),
                        xytext=(5, 5), textcoords='offset points')
        
        plt.xlabel('最大回撤 (%)')
        plt.ylabel('总收益率 (%)')
        plt.title('风险收益散点图')
        
        # 添加颜色条
        cbar = plt.colorbar(scatter)
        cbar.set_label('胜率 (%)')
        
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"风险收益散点图已保存到: {save_path}")
        else:
            plt.show()
    
    def plot_trading_metrics(self, save_path: str = None):
        """绘制交易指标图"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 交易次数对比
        axes[0, 0].bar(self.analysis_data['strategy_name'], 
                       self.analysis_data['total_trades'])
        axes[0, 0].set_title('总交易次数')
        axes[0, 0].set_ylabel('交易次数')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 盈亏比对比
        axes[0, 1].bar(self.analysis_data['strategy_name'], 
                       self.analysis_data['profit_factor'])
        axes[0, 1].set_title('盈亏比')
        axes[0, 1].set_ylabel('盈亏比')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 平均盈亏对比
        x = np.arange(len(self.analysis_data))
        width = 0.35
        
        axes[1, 0].bar(x - width/2, self.analysis_data['avg_profit'], 
                       width, label='平均盈利', color='green', alpha=0.7)
        axes[1, 0].bar(x + width/2, -self.analysis_data['avg_loss'], 
                       width, label='平均亏损', color='red', alpha=0.7)
        axes[1, 0].set_title('平均盈亏对比')
        axes[1, 0].set_ylabel('金额')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(self.analysis_data['strategy_name'], rotation=45)
        axes[1, 0].legend()
        
        # 盈利亏损交易数量对比
        axes[1, 1].bar(x - width/2, self.analysis_data['profit_trades'], 
                       width, label='盈利交易', color='green', alpha=0.7)
        axes[1, 1].bar(x + width/2, self.analysis_data['loss_trades'], 
                       width, label='亏损交易', color='red', alpha=0.7)
        axes[1, 1].set_title('盈利亏损交易数量对比')
        axes[1, 1].set_ylabel('交易数量')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(self.analysis_data['strategy_name'], rotation=45)
        axes[1, 1].legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"交易指标图已保存到: {save_path}")
        else:
            plt.show()
    
    def generate_detailed_report(self) -> str:
        """生成详细分析报告"""
        report = []
        report.append("=" * 80)
        report.append("回测结果详细分析报告")
        report.append("=" * 80)
        report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"策略数量: {len(self.results)}")
        report.append("")
        
        # 性能排名
        report.append("1. 性能排名")
        report.append("-" * 40)
        
        # 按总收益率排名
        sorted_by_return = self.analysis_data.sort_values('total_return', ascending=False)
        report.append("按总收益率排名:")
        for i, (_, row) in enumerate(sorted_by_return.iterrows(), 1):
            report.append(f"  {i}. {row['strategy_name']}: {row['total_return']:.2%}")
        
        report.append("")
        
        # 按夏普比率排名
        sorted_by_sharpe = self.analysis_data.sort_values('sharpe_ratio', ascending=False)
        report.append("按夏普比率排名:")
        for i, (_, row) in enumerate(sorted_by_sharpe.iterrows(), 1):
            report.append(f"  {i}. {row['strategy_name']}: {row['sharpe_ratio']:.2f}")
        
        report.append("")
        
        # 风险分析
        report.append("2. 风险分析")
        report.append("-" * 40)
        risk_metrics = self.get_risk_metrics()
        for _, row in risk_metrics.iterrows():
            report.append(f"策略: {row['strategy_name']}")
            report.append(f"  最大回撤: {row['max_drawdown']:.2%}")
            report.append(f"  夏普比率: {row['sharpe_ratio']:.2f}")
            report.append(f"  波动率: {row['volatility']:.2%}")
            report.append(f"  VaR(95%): {row['var_95']:.2%}")
            report.append(f"  VaR(99%): {row['var_99']:.2%}")
            report.append("")
        
        # 交易分析
        report.append("3. 交易分析")
        report.append("-" * 40)
        trading_metrics = self.get_trading_metrics()
        for _, row in trading_metrics.iterrows():
            report.append(f"策略: {row['strategy_name']}")
            report.append(f"  总交易次数: {row['total_trades']}")
            report.append(f"  盈利交易: {row['profit_trades']}")
            report.append(f"  亏损交易: {row['loss_trades']}")
            report.append(f"  胜率: {row['win_rate']:.2%}")
            report.append(f"  平均盈利: {row['avg_profit']:.2f}")
            report.append(f"  平均亏损: {row['avg_loss']:.2f}")
            report.append(f"  盈亏比: {row['profit_factor']:.2f}")
            report.append("")
        
        # 最佳策略推荐
        report.append("4. 最佳策略推荐")
        report.append("-" * 40)
        best_return = self.get_best_strategy('total_return')
        best_sharpe = self.get_best_strategy('sharpe_ratio')
        best_win_rate = self.get_best_strategy('win_rate')
        
        report.append(f"最佳收益率策略: {best_return}")
        report.append(f"最佳风险调整收益策略: {best_sharpe}")
        report.append(f"最佳胜率策略: {best_win_rate}")
        report.append("")
        
        # 综合建议
        report.append("5. 综合建议")
        report.append("-" * 40)
        report.append("基于以上分析，建议:")
        
        # 根据夏普比率选择最佳策略
        best_overall = self.get_best_strategy('sharpe_ratio')
        report.append(f"• 推荐策略: {best_overall} (最佳风险调整收益)")
        
        # 检查风险
        best_strategy_data = self.analysis_data[self.analysis_data['strategy_name'] == best_overall].iloc[0]
        if best_strategy_data['max_drawdown'] > 0.2:
            report.append("• 风险提示: 最大回撤超过20%，建议谨慎使用")
        
        if best_strategy_data['win_rate'] < 0.5:
            report.append("• 风险提示: 胜率低于50%，建议优化策略")
        
        report.append("• 建议进行更长时间的回测验证")
        report.append("• 建议在实盘前进行充分的参数优化")
        
        return "\n".join(report)
    
    def export_to_excel(self, filename: str = None):
        """导出分析结果到Excel"""
        if filename is None:
            filename = f"backtest_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # 性能摘要
            self.analysis_data.to_excel(writer, sheet_name='性能摘要', index=False)
            
            # 风险指标
            risk_metrics = self.get_risk_metrics()
            risk_metrics.to_excel(writer, sheet_name='风险指标', index=False)
            
            # 交易指标
            trading_metrics = self.get_trading_metrics()
            trading_metrics.to_excel(writer, sheet_name='交易指标', index=False)
            
            # 详细报告
            report_df = pd.DataFrame({'详细报告': [self.generate_detailed_report()]})
            report_df.to_excel(writer, sheet_name='详细报告', index=False)
        
        logger.info(f"分析结果已导出到: {filename}") 