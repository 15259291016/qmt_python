# coding=utf-8
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

from strategies.base import BaseStrategy
from .manager import StrategyManager, StrategyPerformance

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    account_id: str
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
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
    daily_returns: List[float]


class BacktestEngine:
    """多策略回测引擎"""
    
    def __init__(self, 
                 strategy_manager: StrategyManager,
                 data: pd.DataFrame,
                 initial_capital: float = 1000000,
                 commission_rate: float = 0.0003,
                 slippage: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            strategy_manager: 策略管理器
            data: 历史数据，包含 datetime, symbol, open, high, low, close, volume 字段
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
        """
        self.strategy_manager = strategy_manager
        self.data = data
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # 回测结果
        self.results: Dict[str, BacktestResult] = {}
        
        # 数据预处理
        self._prepare_data()
        
        logger.info("回测引擎初始化完成")
    
    def _prepare_data(self):
        """数据预处理"""
        try:
            # 确保数据包含必要字段
            required_columns = ['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in self.data.columns]
            if missing_columns:
                raise ValueError(f"数据缺少必要字段: {missing_columns}")
            
            # 按时间排序
            self.data = self.data.sort_values('datetime').reset_index(drop=True)
            
            # 按symbol分组
            self.data_by_symbol = {}
            for symbol in self.data['symbol'].unique():
                symbol_data = self.data[self.data['symbol'] == symbol].copy()
                symbol_data = symbol_data.sort_values('datetime').reset_index(drop=True)
                self.data_by_symbol[symbol] = symbol_data
            
            logger.info(f"数据预处理完成，共 {len(self.data_by_symbol)} 个品种")
            
        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            raise
    
    def run_backtest(self, 
                    start_date: datetime = None, 
                    end_date: datetime = None,
                    strategies: List[str] = None) -> Dict[str, BacktestResult]:
        """
        运行回测
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            strategies: 要回测的策略列表，None表示回测所有策略
            
        Returns:
            回测结果字典
        """
        try:
            if strategies is None:
                strategies = list(self.strategy_manager.strategies.keys())
            
            logger.info(f"开始回测 {len(strategies)} 个策略")
            
            # 过滤数据时间范围
            if start_date:
                self.data = self.data[self.data['datetime'] >= start_date]
            if end_date:
                self.data = self.data[self.data['datetime'] <= end_date]
            
            # 重新准备数据
            self._prepare_data()
            
            # 为每个策略运行回测
            for strategy_name in strategies:
                try:
                    logger.info(f"开始回测策略: {strategy_name}")
                    result = self._run_single_strategy_backtest(strategy_name)
                    if result:
                        self.results[strategy_name] = result
                        logger.info(f"策略 {strategy_name} 回测完成")
                except Exception as e:
                    logger.error(f"策略 {strategy_name} 回测失败: {e}")
            
            logger.info(f"回测完成，共 {len(self.results)} 个策略")
            return self.results
            
        except Exception as e:
            logger.error(f"回测运行失败: {e}")
            raise
    
    def _run_single_strategy_backtest(self, strategy_name: str) -> Optional[BacktestResult]:
        """运行单个策略回测"""
        try:
            strategy = self.strategy_manager.strategies[strategy_name]
            state = self.strategy_manager.strategy_states[strategy_name]
            
            account_id = state.get('account_id')
            symbols = state.get('symbols', [])
            
            if not account_id or not symbols:
                logger.warning(f"策略 {strategy_name} 缺少账户或品种配置")
                return None
            
            # 初始化回测状态
            capital = self.initial_capital
            positions = {}  # symbol -> quantity
            equity_curve = [capital]
            trade_history = []
            daily_returns = []
            
            # 获取所有交易日
            all_dates = sorted(self.data['datetime'].unique())
            
            for date in all_dates:
                daily_capital = capital
                
                # 获取当日数据
                daily_data = self.data[self.data['datetime'] == date]
                
                for _, row in daily_data.iterrows():
                    symbol = row['symbol']
                    if symbol not in symbols:
                        continue
                    
                    # 构建K线数据
                    bar_data = {
                        'symbol': symbol,
                        'datetime': row['datetime'],
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['volume']
                    }
                    
                    # 执行策略
                    signal = strategy.on_bar(bar_data, account_id)
                    
                    # 执行交易
                    if signal != 0:
                        trade_result = self._execute_trade(
                            symbol, signal, row['close'], 
                            capital, positions, trade_history
                        )
                        if trade_result:
                            capital = trade_result['new_capital']
                            positions = trade_result['new_positions']
                
                # 更新持仓市值
                for symbol, quantity in positions.items():
                    if symbol in self.data_by_symbol:
                        symbol_data = self.data_by_symbol[symbol]
                        today_data = symbol_data[symbol_data['datetime'] == date]
                        if not today_data.empty:
                            price = today_data.iloc[0]['close']
                            daily_capital += quantity * price
                
                equity_curve.append(daily_capital)
                
                # 计算日收益率
                if len(equity_curve) > 1:
                    daily_return = (daily_capital - equity_curve[-2]) / equity_curve[-2]
                    daily_returns.append(daily_return)
            
            # 计算绩效指标
            performance = self._calculate_backtest_performance(
                strategy_name, account_id, symbols,
                all_dates[0], all_dates[-1],
                equity_curve, trade_history, daily_returns
            )
            
            return performance
            
        except Exception as e:
            logger.error(f"策略 {strategy_name} 回测失败: {e}")
            return None
    
    def _execute_trade(self, symbol: str, signal: int, price: float, 
                      capital: float, positions: Dict, trade_history: List) -> Optional[Dict]:
        """执行交易"""
        try:
            current_position = positions.get(symbol, 0)
            
            if signal > 0 and current_position == 0:  # 买入信号
                # 计算可买数量（简化，固定资金比例）
                available_capital = capital * 0.1  # 使用10%资金
                quantity = int(available_capital / price / 100) * 100  # 整手交易
                
                if quantity > 0:
                    # 计算交易成本
                    commission = quantity * price * self.commission_rate
                    slippage_cost = quantity * price * self.slippage
                    total_cost = quantity * price + commission + slippage_cost
                    
                    if total_cost <= capital:
                        # 执行买入
                        positions[symbol] = quantity
                        capital -= total_cost
                        
                        trade_record = {
                            'datetime': datetime.now(),
                            'symbol': symbol,
                            'action': 'buy',
                            'quantity': quantity,
                            'price': price,
                            'commission': commission,
                            'slippage': slippage_cost,
                            'total_cost': total_cost
                        }
                        trade_history.append(trade_record)
                        
                        return {
                            'new_capital': capital,
                            'new_positions': positions
                        }
            
            elif signal < 0 and current_position > 0:  # 卖出信号
                # 执行卖出
                commission = current_position * price * self.commission_rate
                slippage_cost = current_position * price * self.slippage
                total_revenue = current_position * price - commission - slippage_cost
                
                capital += total_revenue
                positions[symbol] = 0
                
                trade_record = {
                    'datetime': datetime.now(),
                    'symbol': symbol,
                    'action': 'sell',
                    'quantity': current_position,
                    'price': price,
                    'commission': commission,
                    'slippage': slippage_cost,
                    'total_revenue': total_revenue
                }
                trade_history.append(trade_record)
                
                return {
                    'new_capital': capital,
                    'new_positions': positions
                }
            
            return None
            
        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            return None
    
    def _calculate_backtest_performance(self, strategy_name: str, account_id: str, 
                                      symbols: List[str], start_date: datetime, 
                                      end_date: datetime, equity_curve: List[float],
                                      trade_history: List[Dict], daily_returns: List[float]) -> BacktestResult:
        """计算回测绩效"""
        try:
            initial_capital = equity_curve[0]
            final_capital = equity_curve[-1]
            total_return = (final_capital - initial_capital) / initial_capital
            
            # 计算年化收益率
            days = (end_date - start_date).days
            annual_return = total_return * 365 / days if days > 0 else 0
            
            # 计算夏普比率
            if daily_returns:
                returns_array = np.array(daily_returns)
                sharpe_ratio = np.mean(returns_array) / np.std(returns_array) * np.sqrt(252) if np.std(returns_array) > 0 else 0
            else:
                sharpe_ratio = 0
            
            # 计算最大回撤
            max_drawdown = 0
            peak = equity_curve[0]
            for value in equity_curve:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # 计算交易统计
            total_trades = len(trade_history)
            profit_trades = 0
            loss_trades = 0
            total_profit = 0
            total_loss = 0
            
            for trade in trade_history:
                if trade['action'] == 'sell':
                    # 找到对应的买入交易
                    buy_trade = None
                    for prev_trade in trade_history[:trade_history.index(trade)]:
                        if prev_trade['symbol'] == trade['symbol'] and prev_trade['action'] == 'buy':
                            buy_trade = prev_trade
                            break
                    
                    if buy_trade:
                        profit = trade['total_revenue'] - buy_trade['total_cost']
                        if profit > 0:
                            profit_trades += 1
                            total_profit += profit
                        else:
                            loss_trades += 1
                            total_loss += abs(profit)
            
            win_rate = profit_trades / total_trades if total_trades > 0 else 0
            avg_profit = total_profit / profit_trades if profit_trades > 0 else 0
            avg_loss = total_loss / loss_trades if loss_trades > 0 else 0
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            return BacktestResult(
                strategy_name=strategy_name,
                account_id=account_id,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_capital=final_capital,
                total_return=total_return,
                annual_return=annual_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                total_trades=total_trades,
                profit_trades=profit_trades,
                loss_trades=loss_trades,
                avg_profit=avg_profit,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                equity_curve=equity_curve,
                trade_history=trade_history,
                daily_returns=daily_returns
            )
            
        except Exception as e:
            logger.error(f"计算回测绩效失败: {e}")
            raise
    
    def save_results(self, file_path: str = None):
        """保存回测结果"""
        try:
            if file_path is None:
                file_path = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            results_data = {}
            for name, result in self.results.items():
                results_data[name] = asdict(result)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, default=str, indent=2)
            
            logger.info(f"回测结果已保存到: {file_path}")
            
        except Exception as e:
            logger.error(f"保存回测结果失败: {e}")
    
    def generate_report(self) -> str:
        """生成回测报告"""
        try:
            report = []
            report.append("=" * 60)
            report.append("多策略回测报告")
            report.append("=" * 60)
            report.append(f"回测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"策略数量: {len(self.results)}")
            report.append("")
            
            for strategy_name, result in self.results.items():
                report.append(f"策略: {strategy_name}")
                report.append("-" * 40)
                report.append(f"账户: {result.account_id}")
                report.append(f"品种: {', '.join(result.symbols)}")
                report.append(f"初始资金: {result.initial_capital:,.2f}")
                report.append(f"最终资金: {result.final_capital:,.2f}")
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