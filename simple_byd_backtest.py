# coding=utf-8
"""
比亚迪股票策略回测 - 简化版本
使用模拟数据进行回测演示
"""

import backtrader as bt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, Any

# 导入策略
from strategies.byd_strategy import BYDStrategy, BYDEnhancedStrategy, BYDConservativeStrategy

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


def create_byd_mock_data():
    """创建比亚迪模拟数据"""
    logger.info("创建比亚迪模拟数据...")
    
    # 生成日期范围（2022年1月1日到2024年12月1日）
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 1)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    # 过滤掉周末
    dates = dates[dates.weekday < 5]
    
    # 模拟比亚迪价格走势
    np.random.seed(42)  # 固定随机种子，确保结果可重现
    
    # 基础价格参数
    base_price = 200  # 起始价格
    daily_return_mean = 0.0005  # 日均收益率
    daily_return_std = 0.025  # 日收益率标准差
    
    # 生成价格序列
    prices = [base_price]
    for i in range(1, len(dates)):
        # 添加趋势和周期性波动
        trend = 0.0001 * i  # 缓慢上升趋势
        cycle = 0.01 * np.sin(2 * np.pi * i / 252)  # 年度周期
        random_return = np.random.normal(daily_return_mean, daily_return_std)
        
        # 计算新价格
        total_return = random_return + trend + cycle
        new_price = prices[-1] * (1 + total_return)
        prices.append(max(new_price, 50))  # 最低价格限制
    
    # 创建OHLCV数据
    data = []
    for i, (date, close_price) in enumerate(zip(dates, prices)):
        # 模拟OHLC数据
        high = close_price * (1 + abs(np.random.normal(0, 0.015)))
        low = close_price * (1 - abs(np.random.normal(0, 0.015)))
        open_price = prices[i-1] if i > 0 else close_price
        
        # 确保OHLC逻辑正确
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        # 模拟成交量（与价格波动相关）
        price_change = abs(close_price - open_price) / open_price
        base_volume = 10000000  # 基础成交量
        volume = base_volume * (1 + price_change * 10 + np.random.normal(0, 0.3))
        volume = max(volume, 1000000)  # 最小成交量
        
        data.append({
            'datetime': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    logger.info(f"比亚迪模拟数据创建完成: {len(df)} 条记录")
    logger.info(f"价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    logger.info(f"数据时间范围: {df.index.min()} 至 {df.index.max()}")
    
    return df


class MockDataFeed(bt.feeds.PandasData):
    """模拟数据源"""
    
    def __init__(self, df: pd.DataFrame, **kwargs):
        super().__init__(dataname=df, **kwargs)


class SimpleBYDBacktest:
    """简化比亚迪回测类"""
    
    def __init__(self, initial_cash: float = 1000000):
        """
        初始化回测
        
        Args:
            initial_cash: 初始资金
        """
        self.initial_cash = initial_cash
        self.results = {}
        
        logger.info("简化比亚迪回测初始化完成")
    
    def run_strategy(self, strategy_class, strategy_name: str, **strategy_params) -> Dict[str, Any]:
        """运行单个策略回测"""
        logger.info(f"开始运行 {strategy_name} 策略回测...")
        
        # 创建模拟数据
        df = create_byd_mock_data()
        
        # 创建 Cerebro 引擎
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=0.001)
        
        # 添加数据源
        data_feed = MockDataFeed(df)
        cerebro.adddata(data_feed, name='BYD')
        
        # 添加策略
        cerebro.addstrategy(strategy_class, **strategy_params)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
        # 运行回测
        results = cerebro.run()
        result = results[0]
        
        # 提取分析结果
        sharpe_ratio = result.analyzers.sharpe.get_analysis()
        drawdown = result.analyzers.drawdown.get_analysis()
        trades = result.analyzers.trades.get_analysis()
        returns = result.analyzers.returns.get_analysis()
        
        # 计算关键指标
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - self.initial_cash) / self.initial_cash
        
        # 计算年化收益率
        days = (df.index[-1] - df.index[0]).days
        annual_return = (1 + total_return) ** (365 / days) - 1
        
        # 提取交易统计
        total_trades = trades.get('total', {}).get('total', 0)
        won_trades = trades.get('won', {}).get('total', 0)
        lost_trades = trades.get('lost', {}).get('total', 0)
        win_rate = won_trades / total_trades if total_trades > 0 else 0
        
        # 计算平均盈亏
        avg_won = trades.get('won', {}).get('pnl', {}).get('average', 0)
        avg_lost = trades.get('lost', {}).get('pnl', {}).get('average', 0)
        
        # 盈亏比
        profit_factor = abs(avg_won / avg_lost) if avg_lost != 0 else float('inf')
        
        # 构建结果
        result_dict = {
            'strategy_name': strategy_name,
            'symbol': '002594.SZ',
            'start_date': df.index[0],
            'end_date': df.index[-1],
            'initial_cash': self.initial_cash,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio.get('sharperatio', 0),
            'max_drawdown': drawdown.get('max', {}).get('drawdown', 0),
            'win_rate': win_rate,
            'total_trades': total_trades,
            'profit_trades': won_trades,
            'loss_trades': lost_trades,
            'avg_profit': avg_won,
            'avg_loss': avg_lost,
            'profit_factor': profit_factor
        }
        
        self.results[strategy_name] = result_dict
        
        logger.info(f"{strategy_name} 策略回测完成:")
        logger.info(f"  总收益率: {total_return:.2%}")
        logger.info(f"  年化收益率: {annual_return:.2%}")
        logger.info(f"  夏普比率: {result_dict['sharpe_ratio']:.2f}")
        logger.info(f"  最大回撤: {result_dict['max_drawdown']:.2%}")
        logger.info(f"  胜率: {win_rate:.1%}")
        logger.info(f"  总交易次数: {total_trades}")
        
        return result_dict
    
    def run_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """运行所有策略"""
        logger.info("开始运行所有比亚迪策略回测...")
        
        # 运行基础策略
        self.run_strategy(BYDStrategy, 'BYD_Basic')
        
        # 运行增强策略
        self.run_strategy(BYDEnhancedStrategy, 'BYD_Enhanced')
        
        # 运行保守策略
        self.run_strategy(BYDConservativeStrategy, 'BYD_Conservative')
        
        return self.results
    
    def generate_report(self) -> str:
        """生成回测报告"""
        if not self.results:
            return "没有可用的回测结果"
        
        report = []
        report.append("=" * 80)
        report.append("比亚迪股票策略回测报告")
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
                f"{result['total_return']:>10.2%} "
                f"{result['annual_return']:>10.2%} "
                f"{result['sharpe_ratio']:>8.2f} "
                f"{result['max_drawdown']:>8.2%} "
                f"{result['win_rate']:>6.1%}"
            )
        
        report.append("-" * 80)
        report.append("")
        
        # 详细分析
        for strategy_name, result in self.results.items():
            report.append(f"【{strategy_name.upper()} 策略详细分析】")
            report.append(f"策略名称: {result['strategy_name']}")
            report.append(f"股票代码: {result['symbol']}")
            report.append(f"回测期间: {result['start_date'].strftime('%Y-%m-%d')} 至 {result['end_date'].strftime('%Y-%m-%d')}")
            report.append(f"初始资金: {result['initial_cash']:,.0f} 元")
            report.append(f"最终价值: {result['final_value']:,.0f} 元")
            report.append(f"总收益率: {result['total_return']:.2%}")
            report.append(f"年化收益率: {result['annual_return']:.2%}")
            report.append(f"夏普比率: {result['sharpe_ratio']:.2f}")
            report.append(f"最大回撤: {result['max_drawdown']:.2%}")
            report.append(f"总交易次数: {result['total_trades']}")
            report.append(f"盈利交易: {result['profit_trades']}")
            report.append(f"亏损交易: {result['loss_trades']}")
            report.append(f"胜率: {result['win_rate']:.1%}")
            report.append(f"平均盈利: {result['avg_profit']:.2f}")
            report.append(f"平均亏损: {result['avg_loss']:.2f}")
            report.append(f"盈亏比: {result['profit_factor']:.2f}")
            report.append("")
        
        # 投资建议
        report.append("【投资建议】")
        if self.results:
            best_strategy = max(self.results.values(), key=lambda x: x['sharpe_ratio'])
            report.append(f"推荐策略: {best_strategy['strategy_name']}")
            report.append(f"推荐理由: 夏普比率最高 ({best_strategy['sharpe_ratio']:.2f})")
            report.append("")
        
        report.append("【风险提示】")
        report.append("- 本回测使用模拟数据，仅供参考")
        report.append("- 历史回测结果不代表未来表现")
        report.append("- 投资有风险，入市需谨慎")
        report.append("- 建议结合基本面分析进行投资决策")
        
        return "\n".join(report)
    
    def plot_results(self, output_dir: str = "byd_backtest_plots"):
        """绘制回测结果图表"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 创建对比图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('比亚迪股票策略回测结果对比', fontsize=16)
        
        strategies = list(self.results.keys())
        
        # 1. 收益率对比
        ax1 = axes[0, 0]
        returns = [self.results[s]['total_return'] for s in strategies]
        ax1.bar(strategies, returns, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_title('总收益率对比')
        ax1.set_ylabel('收益率')
        for i, v in enumerate(returns):
            ax1.text(i, v + 0.01, f'{v:.1%}', ha='center', va='bottom')
        
        # 2. 夏普比率对比
        ax2 = axes[0, 1]
        sharpe_ratios = [self.results[s]['sharpe_ratio'] for s in strategies]
        ax2.bar(strategies, sharpe_ratios, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax2.set_title('夏普比率对比')
        ax2.set_ylabel('夏普比率')
        for i, v in enumerate(sharpe_ratios):
            ax2.text(i, v + 0.1, f'{v:.2f}', ha='center', va='bottom')
        
        # 3. 最大回撤对比
        ax3 = axes[1, 0]
        max_drawdowns = [self.results[s]['max_drawdown'] for s in strategies]
        ax3.bar(strategies, max_drawdowns, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax3.set_title('最大回撤对比')
        ax3.set_ylabel('最大回撤')
        for i, v in enumerate(max_drawdowns):
            ax3.text(i, v - 0.02, f'{v:.1%}', ha='center', va='top')
        
        # 4. 胜率对比
        ax4 = axes[1, 1]
        win_rates = [self.results[s]['win_rate'] for s in strategies]
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
    logger.info("开始比亚迪策略回测演示")
    
    try:
        # 创建回测实例
        backtest = SimpleBYDBacktest(initial_cash=1000000)
        
        # 运行所有策略
        results = backtest.run_all_strategies()
        
        # 生成报告
        report = backtest.generate_report()
        print(report)
        
        # 绘制图表
        backtest.plot_results()
        
        logger.info("比亚迪策略回测演示完成!")
        
    except Exception as e:
        logger.error(f"回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 