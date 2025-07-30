# coding=utf-8
"""
比亚迪股票策略回测
使用 Backtrader 框架进行回测分析
"""

import backtrader as bt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, Any

# 导入项目模块
from modules.backtrader_engine.backtest_engine import BacktraderEngine, BacktestResult
from modules.backtrader_engine.data_feed import TushareDataFeed
from strategies.byd_strategy import BYDStrategy, BYDEnhancedStrategy, BYDConservativeStrategy

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class BYDStrategyRunner:
    """比亚迪策略回测运行器"""
    
    def __init__(self, tushare_token: str, initial_cash: float = 1000000):
        """
        初始化回测运行器
        
        Args:
            tushare_token: Tushare API token
            initial_cash: 初始资金
        """
        self.tushare_token = tushare_token
        self.initial_cash = initial_cash
        self.results = {}
        
        logger.info("比亚迪策略回测运行器初始化完成")
    
    def run_basic_strategy(self, start_date: str = '20220101', end_date: str = '20241201') -> BacktestResult:
        """运行基础比亚迪策略"""
        logger.info("开始运行基础比亚迪策略回测...")
        
        # 创建回测引擎
        engine = BacktraderEngine(initial_cash=self.initial_cash, commission=0.001)
        
        # 添加数据源
        data_feed = TushareDataFeed(
            symbol='002594.SZ',  # 比亚迪股票代码
            start_date=start_date,
            end_date=end_date,
            tushare_token=self.tushare_token
        )
        engine.add_data(data_feed, name='BYD')
        
        # 添加策略
        engine.add_strategy(BYDStrategy, strategy_name='BYD_Basic')
        
        # 运行回测
        result = engine.run_backtest()
        
        # 保存结果
        self.results['basic'] = result
        
        logger.info(f"基础策略回测完成，总收益率: {result.total_return:.2%}")
        return result
    
    def run_enhanced_strategy(self, start_date: str = '20220101', end_date: str = '20241201') -> BacktestResult:
        """运行增强比亚迪策略"""
        logger.info("开始运行增强比亚迪策略回测...")
        
        # 创建回测引擎
        engine = BacktraderEngine(initial_cash=self.initial_cash, commission=0.001)
        
        # 添加数据源
        data_feed = TushareDataFeed(
            symbol='002594.SZ',
            start_date=start_date,
            end_date=end_date,
            tushare_token=self.tushare_token
        )
        engine.add_data(data_feed, name='BYD')
        
        # 添加策略
        engine.add_strategy(BYDEnhancedStrategy, strategy_name='BYD_Enhanced')
        
        # 运行回测
        result = engine.run_backtest()
        
        # 保存结果
        self.results['enhanced'] = result
        
        logger.info(f"增强策略回测完成，总收益率: {result.total_return:.2%}")
        return result
    
    def run_conservative_strategy(self, start_date: str = '20220101', end_date: str = '20241201') -> BacktestResult:
        """运行保守比亚迪策略"""
        logger.info("开始运行保守比亚迪策略回测...")
        
        # 创建回测引擎
        engine = BacktraderEngine(initial_cash=self.initial_cash, commission=0.001)
        
        # 添加数据源
        data_feed = TushareDataFeed(
            symbol='002594.SZ',
            start_date=start_date,
            end_date=end_date,
            tushare_token=self.tushare_token
        )
        engine.add_data(data_feed, name='BYD')
        
        # 添加策略
        engine.add_strategy(BYDConservativeStrategy, strategy_name='BYD_Conservative')
        
        # 运行回测
        result = engine.run_backtest()
        
        # 保存结果
        self.results['conservative'] = result
        
        logger.info(f"保守策略回测完成，总收益率: {result.total_return:.2%}")
        return result
    
    def run_all_strategies(self, start_date: str = '20220101', end_date: str = '20241201') -> Dict[str, BacktestResult]:
        """运行所有策略"""
        logger.info("开始运行所有比亚迪策略回测...")
        
        results = {}
        
        # 运行基础策略
        try:
            results['basic'] = self.run_basic_strategy(start_date, end_date)
        except Exception as e:
            logger.error(f"基础策略回测失败: {e}")
        
        # 运行增强策略
        try:
            results['enhanced'] = self.run_enhanced_strategy(start_date, end_date)
        except Exception as e:
            logger.error(f"增强策略回测失败: {e}")
        
        # 运行保守策略
        try:
            results['conservative'] = self.run_conservative_strategy(start_date, end_date)
        except Exception as e:
            logger.error(f"保守策略回测失败: {e}")
        
        self.results = results
        return results
    
    def generate_comparison_report(self) -> str:
        """生成策略对比报告"""
        if not self.results:
            return "没有可用的回测结果"
        
        report = []
        report.append("=" * 80)
        report.append("比亚迪股票策略回测对比报告")
        report.append("=" * 80)
        report.append("")
        
        # 策略对比表格
        report.append("策略性能对比:")
        report.append("-" * 80)
        report.append(f"{'策略名称':<15} {'总收益率':<12} {'年化收益率':<12} {'夏普比率':<10} {'最大回撤':<10} {'胜率':<8}")
        report.append("-" * 80)
        
        for strategy_name, result in self.results.items():
            report.append(
                f"{strategy_name:<15} "
                f"{result.total_return:>10.2%} "
                f"{result.annual_return:>10.2%} "
                f"{result.sharpe_ratio:>8.2f} "
                f"{result.max_drawdown:>8.2%} "
                f"{result.win_rate:>6.1%}"
            )
        
        report.append("-" * 80)
        report.append("")
        
        # 详细分析
        for strategy_name, result in self.results.items():
            report.append(f"【{strategy_name.upper()} 策略详细分析】")
            report.append(f"策略名称: {result.strategy_name}")
            report.append(f"股票代码: {result.symbol}")
            report.append(f"回测期间: {result.start_date.strftime('%Y-%m-%d')} 至 {result.end_date.strftime('%Y-%m-%d')}")
            report.append(f"初始资金: {result.initial_cash:,.0f} 元")
            report.append(f"最终价值: {result.final_value:,.0f} 元")
            report.append(f"总收益率: {result.total_return:.2%}")
            report.append(f"年化收益率: {result.annual_return:.2%}")
            report.append(f"夏普比率: {result.sharpe_ratio:.2f}")
            report.append(f"最大回撤: {result.max_drawdown:.2%}")
            report.append(f"总交易次数: {result.total_trades}")
            report.append(f"盈利交易: {result.profit_trades}")
            report.append(f"亏损交易: {result.loss_trades}")
            report.append(f"胜率: {result.win_rate:.1%}")
            report.append(f"平均盈利: {result.avg_profit:.2%}")
            report.append(f"平均亏损: {result.avg_loss:.2%}")
            report.append(f"盈亏比: {result.profit_factor:.2f}")
            report.append("")
        
        # 投资建议
        report.append("【投资建议】")
        if self.results:
            best_strategy = max(self.results.values(), key=lambda x: x.sharpe_ratio)
            report.append(f"推荐策略: {best_strategy.strategy_name}")
            report.append(f"推荐理由: 夏普比率最高 ({best_strategy.sharpe_ratio:.2f})")
            report.append("")
        
        report.append("【风险提示】")
        report.append("- 历史回测结果不代表未来表现")
        report.append("- 投资有风险，入市需谨慎")
        report.append("- 建议结合基本面分析进行投资决策")
        report.append("- 请根据自身风险承受能力选择合适的策略")
        
        return "\n".join(report)
    
    def save_results(self, filename: str = None):
        """保存回测结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"byd_backtest_results_{timestamp}.json"
        
        # 转换结果为可序列化格式
        serializable_results = {}
        for strategy_name, result in self.results.items():
            serializable_results[strategy_name] = {
                'strategy_name': result.strategy_name,
                'symbol': result.symbol,
                'start_date': result.start_date.isoformat(),
                'end_date': result.end_date.isoformat(),
                'initial_cash': result.initial_cash,
                'final_value': result.final_value,
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
                'profit_factor': result.profit_factor
            }
        
        # 保存到文件
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"回测结果已保存到: {filename}")
    
    def plot_results(self, output_dir: str = "byd_backtest_plots"):
        """绘制回测结果图表"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 创建对比图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('比亚迪股票策略回测结果对比', fontsize=16)
        
        # 1. 收益率对比
        ax1 = axes[0, 0]
        strategies = list(self.results.keys())
        returns = [self.results[s].total_return for s in strategies]
        ax1.bar(strategies, returns, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_title('总收益率对比')
        ax1.set_ylabel('收益率')
        for i, v in enumerate(returns):
            ax1.text(i, v + 0.01, f'{v:.1%}', ha='center', va='bottom')
        
        # 2. 夏普比率对比
        ax2 = axes[0, 1]
        sharpe_ratios = [self.results[s].sharpe_ratio for s in strategies]
        ax2.bar(strategies, sharpe_ratios, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax2.set_title('夏普比率对比')
        ax2.set_ylabel('夏普比率')
        for i, v in enumerate(sharpe_ratios):
            ax2.text(i, v + 0.1, f'{v:.2f}', ha='center', va='bottom')
        
        # 3. 最大回撤对比
        ax3 = axes[1, 0]
        max_drawdowns = [self.results[s].max_drawdown for s in strategies]
        ax3.bar(strategies, max_drawdowns, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax3.set_title('最大回撤对比')
        ax3.set_ylabel('最大回撤')
        for i, v in enumerate(max_drawdowns):
            ax3.text(i, v - 0.02, f'{v:.1%}', ha='center', va='top')
        
        # 4. 胜率对比
        ax4 = axes[1, 1]
        win_rates = [self.results[s].win_rate for s in strategies]
        ax4.bar(strategies, win_rates, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax4.set_title('胜率对比')
        ax4.set_ylabel('胜率')
        for i, v in enumerate(win_rates):
            ax4.text(i, v + 0.01, f'{v:.1%}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 保存图表
        plot_filename = os.path.join(output_dir, 'byd_strategy_comparison.png')
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        logger.info(f"对比图表已保存到: {plot_filename}")


def main():
    """主函数"""
    # 配置参数
    TUSHARE_TOKEN = "your_tushare_token_here"  # 请替换为你的 Tushare token
    INITIAL_CASH = 1000000  # 初始资金 100万
    START_DATE = "20220101"  # 回测开始日期
    END_DATE = "20241201"    # 回测结束日期
    
    # 检查 Tushare token
    if TUSHARE_TOKEN == "your_tushare_token_here":
        logger.error("请先配置 Tushare token!")
        logger.info("获取 Tushare token 的方法:")
        logger.info("1. 访问 https://tushare.pro/")
        logger.info("2. 注册账号并获取 token")
        logger.info("3. 将 token 替换到脚本中的 TUSHARE_TOKEN 变量")
        return
    
    try:
        # 创建回测运行器
        runner = BYDStrategyRunner(TUSHARE_TOKEN, INITIAL_CASH)
        
        # 运行所有策略
        results = runner.run_all_strategies(START_DATE, END_DATE)
        
        # 生成报告
        report = runner.generate_comparison_report()
        print(report)
        
        # 保存结果
        runner.save_results()
        
        # 绘制图表
        runner.plot_results()
        
        logger.info("比亚迪策略回测完成!")
        
    except Exception as e:
        logger.error(f"回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 