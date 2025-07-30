# coding=utf-8
"""
Backtrader 回测引擎
提供基于 Backtrader 框架的回测功能
"""

import backtrader as bt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, asdict
import json
import logging
import os

from .strategy_base import BacktraderStrategyBase
from .data_feed import TushareDataFeed, XtQuantDataFeed, CSVDataFeed

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_cash: float
    final_value: float
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_trades: int
    loss_trades: int
    avg_profit: float
    avg_loss: float
    profit_factor: float
    equity_curve: List[float]
    trade_history: List[Dict]


class BacktraderEngine:
    """Backtrader 回测引擎"""
    
    def __init__(self, 
                 initial_cash: float = 1000000,
                 commission: float = 0.001,
                 margin: float = 0.0,
                 mult: float = 1.0,
                 **kwargs):
        """
        初始化回测引擎
        
        Args:
            initial_cash: 初始资金
            commission: 手续费率
            margin: 保证金
            mult: 杠杆倍数
        """
        self.initial_cash = initial_cash
        self.commission = commission
        self.margin = margin
        self.mult = mult
        
        # 回测结果
        self.results: Dict[str, BacktestResult] = {}
        
        # 创建 Cerebro 引擎
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        self.cerebro.broker.setmargin(margin)
        self.cerebro.broker.setmult(mult)
        
        # 添加分析器
        self._add_analyzers()
        
        logger.info("Backtrader 回测引擎初始化完成")
    
    def _add_analyzers(self):
        """添加分析器"""
        # 夏普比率分析器
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        
        # 回撤分析器
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        
        # 交易分析器
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 收益率分析器
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
        # 权益曲线分析器
        self.cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
    
    def add_data(self, data_feed: bt.feeds.PandasData, name: str = None):
        """添加数据源"""
        self.cerebro.adddata(data_feed, name=name)
        logger.info(f"添加数据源: {name or 'default'}")
    
    def add_strategy(self, strategy_class: Type[BacktraderStrategyBase], 
                    strategy_name: str = None, **kwargs):
        """添加策略"""
        strategy_name = strategy_name or strategy_class.__name__
        self.cerebro.addstrategy(strategy_class, **kwargs)
        logger.info(f"添加策略: {strategy_name}")
    
    def run_backtest(self, strategy_name: str = None) -> Dict[str, Any]:
        """运行回测"""
        try:
            logger.info("开始运行回测...")
            
            # 运行回测
            results = self.cerebro.run()
            
            if not results:
                logger.warning("回测未产生结果")
                return {}
            
            # 处理结果
            result = results[0]
            analysis = self._analyze_results(result, strategy_name)
            
            # 保存结果
            if strategy_name:
                self.results[strategy_name] = analysis
            
            logger.info("回测完成")
            return analysis
            
        except Exception as e:
            logger.error(f"回测运行失败: {e}")
            raise
    
    def _analyze_results(self, result, strategy_name: str = None) -> BacktestResult:
        """分析回测结果"""
        try:
            # 获取分析器结果
            sharpe_ratio = result.analyzers.sharpe.get_analysis()
            drawdown = result.analyzers.drawdown.get_analysis()
            trades = result.analyzers.trades.get_analysis()
            returns = result.analyzers.returns.get_analysis()
            
            # 计算基本指标
            final_value = self.cerebro.broker.getvalue()
            total_return = (final_value - self.initial_cash) / self.initial_cash
            
            # 年化收益率
            days = (result.datas[0].datetime.date(-1) - result.datas[0].datetime.date(0)).days
            annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
            
            # 夏普比率
            sharpe = sharpe_ratio.get('sharperatio', 0)
            
            # 最大回撤
            max_dd = drawdown.get('max', {}).get('drawdown', 0)
            
            # 交易统计
            total_trades = trades.get('total', {}).get('total', 0)
            profit_trades = trades.get('won', {}).get('total', 0)
            loss_trades = trades.get('lost', {}).get('total', 0)
            
            win_rate = profit_trades / total_trades if total_trades > 0 else 0
            
            # 平均盈亏
            avg_profit = trades.get('won', {}).get('pnl', {}).get('average', 0)
            avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
            
            # 盈亏比
            total_profit = trades.get('won', {}).get('pnl', {}).get('total', 0)
            total_loss = abs(trades.get('lost', {}).get('pnl', {}).get('total', 0))
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # 权益曲线
            equity_curve = self._get_equity_curve()
            
            # 交易历史
            trade_history = self._get_trade_history()
            
            return BacktestResult(
                strategy_name=strategy_name or "Unknown",
                symbol="",  # 可以从数据源获取
                start_date=result.datas[0].datetime.date(0),
                end_date=result.datas[0].datetime.date(-1),
                initial_cash=self.initial_cash,
                final_value=final_value,
                total_return=total_return,
                annual_return=annual_return,
                sharpe_ratio=sharpe,
                max_drawdown=max_dd,
                win_rate=win_rate,
                total_trades=total_trades,
                profit_trades=profit_trades,
                loss_trades=loss_trades,
                avg_profit=avg_profit,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                equity_curve=equity_curve,
                trade_history=trade_history
            )
            
        except Exception as e:
            logger.error(f"分析回测结果失败: {e}")
            raise
    
    def _get_equity_curve(self) -> List[float]:
        """获取权益曲线"""
        # 这里需要从 Backtrader 获取权益曲线数据
        # 由于 Backtrader 的限制，这里返回空列表
        # 实际使用时可以通过其他方式获取
        return []
    
    def _get_trade_history(self) -> List[Dict]:
        """获取交易历史"""
        # 这里需要从 Backtrader 获取交易历史
        # 由于 Backtrader 的限制，这里返回空列表
        # 实际使用时可以通过其他方式获取
        return []
    
    def plot_results(self, filename: str = None, style: str = 'candle'):
        """绘制回测结果"""
        try:
            if filename:
                self.cerebro.plot(style=style, filename=filename)
            else:
                self.cerebro.plot(style=style)
            
            logger.info("回测结果图表已生成")
            
        except Exception as e:
            logger.error(f"绘制回测结果失败: {e}")
    
    def save_results(self, filename: str = None):
        """保存回测结果"""
        try:
            if filename is None:
                filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            results_data = {}
            for name, result in self.results.items():
                results_data[name] = asdict(result)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, default=str, indent=2)
            
            logger.info(f"回测结果已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"保存回测结果失败: {e}")
    
    def generate_report(self) -> str:
        """生成回测报告"""
        try:
            report = []
            report.append("=" * 60)
            report.append("Backtrader 回测报告")
            report.append("=" * 60)
            report.append(f"回测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"策略数量: {len(self.results)}")
            report.append("")
            
            for strategy_name, result in self.results.items():
                report.append(f"策略: {result.strategy_name}")
                report.append("-" * 40)
                report.append(f"股票: {result.symbol}")
                report.append(f"初始资金: {result.initial_cash:,.2f}")
                report.append(f"最终资金: {result.final_value:,.2f}")
                report.append(f"总收益率: {result.total_return:.2%}")
                report.append(f"年化收益率: {result.annual_return:.2%}")
                report.append(f"夏普比率: {result.sharpe_ratio:.2f}")
                report.append(f"最大回撤: {result.max_drawdown:.2%}")
                report.append(f"胜率: {result.win_rate:.2%}")
                report.append(f"总交易次数: {result.total_trades}")
                report.append(f"盈利交易: {result.profit_trades}")
                report.append(f"亏损交易: {result.loss_trades}")
                report.append(f"平均盈利: {result.avg_profit:.2f}")
                report.append(f"平均亏损: {result.avg_loss:.2f}")
                report.append(f"盈亏比: {result.profit_factor:.2f}")
                report.append("")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"生成回测报告失败: {e}")
            return f"生成回测报告失败: {e}"


class MultiStrategyBacktestEngine:
    """多策略回测引擎"""
    
    def __init__(self, initial_cash: float = 1000000, **kwargs):
        """初始化多策略回测引擎"""
        self.initial_cash = initial_cash
        self.kwargs = kwargs
        self.engines = {}
        self.results = {}
    
    def add_strategy_backtest(self, strategy_name: str, 
                            strategy_class: Type[BacktraderStrategyBase],
                            data_feed: bt.feeds.PandasData,
                            **strategy_kwargs):
        """添加策略回测"""
        # 创建独立的回测引擎
        engine = BacktraderEngine(initial_cash=self.initial_cash, **self.kwargs)
        engine.add_data(data_feed, name=strategy_name)
        engine.add_strategy(strategy_class, strategy_name=strategy_name, **strategy_kwargs)
        
        self.engines[strategy_name] = engine
    
    def run_all_backtests(self) -> Dict[str, BacktestResult]:
        """运行所有策略回测"""
        for strategy_name, engine in self.engines.items():
            try:
                logger.info(f"开始回测策略: {strategy_name}")
                result = engine.run_backtest(strategy_name)
                self.results[strategy_name] = result
                logger.info(f"策略 {strategy_name} 回测完成")
            except Exception as e:
                logger.error(f"策略 {strategy_name} 回测失败: {e}")
        
        return self.results
    
    def plot_all_results(self, output_dir: str = "backtest_plots"):
        """绘制所有策略的回测结果"""
        os.makedirs(output_dir, exist_ok=True)
        
        for strategy_name, engine in self.engines.items():
            try:
                filename = os.path.join(output_dir, f"{strategy_name}_results.png")
                engine.plot_results(filename=filename)
                logger.info(f"策略 {strategy_name} 图表已保存到: {filename}")
            except Exception as e:
                logger.error(f"绘制策略 {strategy_name} 结果失败: {e}")
    
    def save_all_results(self, filename: str = None):
        """保存所有回测结果"""
        if filename is None:
            filename = f"multi_strategy_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results_data = {}
        for name, result in self.results.items():
            results_data[name] = asdict(result)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, default=str, indent=2)
        
        logger.info(f"所有回测结果已保存到: {filename}")
    
    def generate_comprehensive_report(self) -> str:
        """生成综合回测报告"""
        report = []
        report.append("=" * 80)
        report.append("多策略回测综合报告")
        report.append("=" * 80)
        report.append(f"回测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"策略数量: {len(self.results)}")
        report.append(f"初始资金: {self.initial_cash:,.2f}")
        report.append("")
        
        # 策略对比表格
        report.append("策略性能对比:")
        report.append("-" * 80)
        report.append(f"{'策略名称':<15} {'总收益率':<10} {'年化收益率':<12} {'夏普比率':<10} {'最大回撤':<10} {'胜率':<8}")
        report.append("-" * 80)
        
        for strategy_name, result in self.results.items():
            report.append(f"{strategy_name:<15} {result.total_return:>8.2%} {result.annual_return:>10.2%} "
                        f"{result.sharpe_ratio:>8.2f} {result.max_drawdown:>8.2%} {result.win_rate:>6.2%}")
        
        report.append("-" * 80)
        report.append("")
        
        # 详细结果
        for strategy_name, result in self.results.items():
            report.append(f"详细结果 - {strategy_name}:")
            report.append("-" * 40)
            report.append(f"总交易次数: {result.total_trades}")
            report.append(f"盈利交易: {result.profit_trades}")
            report.append(f"亏损交易: {result.loss_trades}")
            report.append(f"平均盈利: {result.avg_profit:.2f}")
            report.append(f"平均亏损: {result.avg_loss:.2f}")
            report.append(f"盈亏比: {result.profit_factor:.2f}")
            report.append("")
        
        return "\n".join(report) 