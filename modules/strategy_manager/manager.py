# coding=utf-8
import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
from pathlib import Path

from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount

from .config import STRATEGY_CONFIG
from strategies.base import BaseStrategy
from strategies.registry import StrategyRegistry
# 确保策略被导入和注册
import strategies
from modules.tornadoapp.oms.order_manager import OrderManager
from modules.tornadoapp.risk.risk_manager import RiskManager
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
from modules.tornadoapp.audit.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


@dataclass
class StrategyPerformance:
    """策略绩效数据"""
    strategy_name: str
    account_id: str
    symbol: str
    start_time: datetime
    end_time: datetime
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


@dataclass
class StrategyLog:
    """策略运行日志"""
    timestamp: datetime
    strategy_name: str
    account_id: str
    symbol: str
    log_level: str
    message: str
    data: Optional[Dict] = None


class StrategyManager:
    """多策略管理器"""
    
    def __init__(self, 
                 xt_trader: XtQuantTrader,
                 order_manager: OrderManager,
                 data_service_manager=None,
                 base_path: str = "strategy_data"):
        self.xt_trader = xt_trader
        self.order_manager = order_manager
        self.data_service_manager = data_service_manager
        
        # 策略相关
        self.strategies: Dict[str, BaseStrategy] = {}
        self.strategy_threads: Dict[str, threading.Thread] = {}
        self.strategy_states: Dict[str, Dict] = {}
        self.performance_data: Dict[str, StrategyPerformance] = {}
        
        # 账户和品种管理
        self.accounts: Dict[str, StockAccount] = {}
        self.symbols: List[str] = []
        self.account_strategies: Dict[str, List[str]] = {}  # 账户 -> 策略列表
        
        # 文件路径
        self.base_path = Path(base_path)
        self.log_path = self.base_path / "logs"
        self.performance_path = self.base_path / "performance"
        self.config_path = self.base_path / "configs"
        
        # 创建目录
        for path in [self.log_path, self.performance_path, self.config_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # 热插拔支持
        self.hot_reload_enabled = True
        self.config_watcher = None
        
        # 使用全局策略注册表
        from strategies.registry import get_registry
        self.registry = get_registry()
        # 确保策略被导入和注册
        import strategies
        
        logger.info("策略管理器初始化完成")
    
    def add_account(self, account_id: str, account: StockAccount):
        """添加交易账户"""
        self.accounts[account_id] = account
        self.account_strategies[account_id] = []
        logger.info(f"添加账户: {account_id}")
    
    def add_symbol(self, symbol: str):
        """添加交易品种"""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            logger.info(f"添加交易品种: {symbol}")
    
    def load_strategies_from_config(self, config: List[Dict] = None):
        """从配置加载策略"""
        if config is None:
            config = STRATEGY_CONFIG
        
        for strategy_config in config:
            try:
                strategy_name = strategy_config['name']
                strategy_class = strategy_config['class']
                strategy_params = strategy_config.get('params', {})
                
                # 从注册表获取策略类
                strategy_cls = self.registry.get_strategy(strategy_class)
                if strategy_cls is None:
                    logger.error(f"策略类 {strategy_class} 未找到")
                    continue
                
                # 创建策略实例
                strategy = strategy_cls(**strategy_params)
                self.strategies[strategy_name] = strategy
                
                # 初始化策略状态
                self.strategy_states[strategy_name] = {
                    'status': 'stopped',
                    'start_time': None,
                    'last_update': None,
                    'error_count': 0,
                    'performance': None
                }
                
                logger.info(f"加载策略: {strategy_name} ({strategy_class})")
                
            except Exception as e:
                logger.error(f"加载策略 {strategy_config.get('name', 'unknown')} 失败: {e}")
    
    def assign_strategy_to_account(self, strategy_name: str, account_id: str, symbols: List[str] = None):
        """将策略分配给账户"""
        if strategy_name not in self.strategies:
            logger.error(f"策略 {strategy_name} 不存在")
            return False
        
        if account_id not in self.accounts:
            logger.error(f"账户 {account_id} 不存在")
            return False
        
        if symbols is None:
            symbols = self.symbols
        
        # 添加到账户策略映射
        if strategy_name not in self.account_strategies[account_id]:
            self.account_strategies[account_id].append(strategy_name)
        
        # 更新策略状态
        self.strategy_states[strategy_name]['account_id'] = account_id
        self.strategy_states[strategy_name]['symbols'] = symbols
        
        logger.info(f"策略 {strategy_name} 分配给账户 {account_id}, 品种: {symbols}")
        return True
    
    def start_strategy(self, strategy_name: str):
        """启动单个策略"""
        if strategy_name not in self.strategies:
            logger.error(f"策略 {strategy_name} 不存在")
            return False
        
        if self.strategy_states[strategy_name]['status'] == 'running':
            logger.warning(f"策略 {strategy_name} 已在运行")
            return True
        
        try:
            strategy = self.strategies[strategy_name]
            state = self.strategy_states[strategy_name]
            
            # 创建策略运行线程
            thread = threading.Thread(
                target=self._run_strategy_loop,
                args=(strategy_name,),
                name=f"Strategy-{strategy_name}",
                daemon=True
            )
            
            self.strategy_threads[strategy_name] = thread
            thread.start()
            
            # 更新状态
            state['status'] = 'running'
            state['start_time'] = datetime.now()
            state['last_update'] = datetime.now()
            
            self._log_strategy_event(strategy_name, "INFO", f"策略启动成功")
            logger.info(f"策略 {strategy_name} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动策略 {strategy_name} 失败: {e}")
            self._log_strategy_event(strategy_name, "ERROR", f"策略启动失败: {e}")
            return False
    
    def stop_strategy(self, strategy_name: str):
        """停止单个策略"""
        if strategy_name not in self.strategies:
            logger.error(f"策略 {strategy_name} 不存在")
            return False
        
        state = self.strategy_states[strategy_name]
        if state['status'] != 'running':
            logger.warning(f"策略 {strategy_name} 未在运行")
            return True
        
        try:
            # 标记停止
            state['status'] = 'stopping'
            
            # 等待线程结束
            if strategy_name in self.strategy_threads:
                thread = self.strategy_threads[strategy_name]
                thread.join(10)  # 最多等待10秒
            
            # 更新状态
            state['status'] = 'stopped'
            state['last_update'] = datetime.now()
            
            self._log_strategy_event(strategy_name, "INFO", f"策略停止成功")
            logger.info(f"策略 {strategy_name} 停止成功")
            return True
            
        except Exception as e:
            logger.error(f"停止策略 {strategy_name} 失败: {e}")
            return False
    
    def start_all_strategies(self):
        """启动所有策略"""
        logger.info("启动所有策略...")
        for strategy_name in self.strategies:
            self.start_strategy(strategy_name)
    
    def stop_all_strategies(self):
        """停止所有策略"""
        logger.info("停止所有策略...")
        for strategy_name in self.strategies:
            self.stop_strategy(strategy_name)
    
    def _run_strategy_loop(self, strategy_name: str):
        """策略运行循环"""
        strategy = self.strategies[strategy_name]
        state = self.strategy_states[strategy_name]
        account_id = state.get('account_id')
        symbols = state.get('symbols', [])
        
        if not account_id or not symbols:
            logger.error(f"策略 {strategy_name} 缺少账户或品种配置")
            return
        
        account = self.accounts[account_id]
        
        logger.info(f"策略 {strategy_name} 开始运行 - 账户: {account_id}, 品种: {symbols}")
        
        try:
            while state['status'] == 'running':
                try:
                    # 获取最新数据
                    data = self._get_latest_data(symbols)
                    if data is None:
                        time.sleep(1)
                        continue
                    
                    # 执行策略逻辑
                    for symbol in symbols:
                        if symbol in data:
                            signal = strategy.on_bar(data[symbol], account_id)
                            
                            # 记录信号
                            self._log_strategy_event(
                                strategy_name, "DEBUG", 
                                f"信号生成: {symbol} = {signal}",
                                {'symbol': symbol, 'signal': signal, 'data': data[symbol]}
                            )
                            
                            # 执行交易
                            if signal != 0:
                                self._execute_signal(strategy_name, account, symbol, signal, data[symbol])
                    
                    # 更新状态
                    state['last_update'] = datetime.now()
                    state['error_count'] = 0
                    
                    # 策略执行间隔
                    time.sleep(strategy.get_interval())
                    
                except Exception as e:
                    state['error_count'] += 1
                    logger.error(f"策略 {strategy_name} 执行错误: {e}")
                    self._log_strategy_event(strategy_name, "ERROR", f"策略执行错误: {e}")
                    
                    if state['error_count'] > 10:
                        logger.error(f"策略 {strategy_name} 错误次数过多，停止运行")
                        break
                    
                    time.sleep(5)  # 错误后等待5秒
                    
        except Exception as e:
            logger.error(f"策略 {strategy_name} 运行循环异常: {e}")
        finally:
            state['status'] = 'stopped'
            logger.info(f"策略 {strategy_name} 运行结束")
    
    def _get_latest_data(self, symbols: list) -> dict:
        """获取最新K线数据（多品种）"""
        try:
            if self.data_service_manager:
                data = {}
                for symbol in symbols:
                    # 获取最新一条1分钟K线
                    bars = self.data_service_manager.get_bar_data(symbol, '20240101', '20991231', '1min')
                    if bars:
                        latest_bar = bars[-1]
                        data[symbol] = latest_bar.dict() if hasattr(latest_bar, 'dict') else latest_bar
                return data if data else None
            else:
                return self._get_mock_data(symbols)
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return None
    
    def _get_mock_data(self, symbols: List[str]) -> Dict:
        """获取模拟数据"""
        import random
        data = {}
        for symbol in symbols:
            price = 10 + random.random() * 10
            data[symbol] = {
                'symbol': symbol,
                'open': price,
                'high': price * 1.02,
                'low': price * 0.98,
                'close': price + random.uniform(-0.1, 0.1),
                'volume': random.randint(1000, 10000),
                'timestamp': datetime.now()
            }
        return data
    
    def _execute_signal(self, strategy_name: str, account: StockAccount, symbol: str, signal: int, data: Dict):
        """执行交易信号"""
        try:
            if signal > 0:  # 买入信号
                # 检查持仓
                positions = self.xt_trader.query_stock_positions(account)
                current_position = 0
                for pos in positions:
                    if pos.stock_code == symbol:
                        current_position = pos.volume
                        break
                
                if current_position == 0:  # 没有持仓才买入
                    price = data['close']
                    quantity = 100  # 固定数量，实际应该根据资金计算
                    
                    order = self.order_manager.create_order(symbol, "买", price, quantity, account)
                    
                    self._log_strategy_event(
                        strategy_name, "INFO",
                        f"买入信号执行: {symbol}, 价格: {price}, 数量: {quantity}",
                        {'symbol': symbol, 'action': 'buy', 'price': price, 'quantity': quantity, 'order': order}
                    )
            
            elif signal < 0:  # 卖出信号
                # 检查持仓
                positions = self.xt_trader.query_stock_positions(account)
                current_position = 0
                for pos in positions:
                    if pos.stock_code == symbol:
                        current_position = pos.volume
                        break
                
                if current_position > 0:  # 有持仓才卖出
                    price = data['close']
                    quantity = current_position
                    
                    order = self.order_manager.create_order(symbol, "卖", price, quantity, account)
                    
                    self._log_strategy_event(
                        strategy_name, "INFO",
                        f"卖出信号执行: {symbol}, 价格: {price}, 数量: {quantity}",
                        {'symbol': symbol, 'action': 'sell', 'price': price, 'quantity': quantity, 'order': order}
                    )
                    
        except Exception as e:
            logger.error(f"执行信号失败: {e}")
            self._log_strategy_event(strategy_name, "ERROR", f"执行信号失败: {e}")
    
    def _log_strategy_event(self, strategy_name: str, level: str, message: str, data: Dict = None):
        """记录策略事件"""
        try:
            log_entry = StrategyLog(
                timestamp=datetime.now(),
                strategy_name=strategy_name,
                account_id=self.strategy_states[strategy_name].get('account_id', ''),
                symbol=data.get('symbol', '') if data else '',
                log_level=level,
                message=message,
                data=data
            )
            
            # 保存到文件
            log_file = self.log_path / f"{strategy_name}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(log_entry), ensure_ascii=False, default=str) + '\n')
                
        except Exception as e:
            logger.error(f"记录策略日志失败: {e}")
    
    def calculate_performance(self, strategy_name: str, start_date: datetime = None, end_date: datetime = None):
        """计算策略绩效"""
        try:
            if strategy_name not in self.strategies:
                logger.error(f"策略 {strategy_name} 不存在")
                return None
            
            # 读取策略日志
            log_files = list(self.log_path.glob(f"{strategy_name}_*.json"))
            if not log_files:
                logger.warning(f"策略 {strategy_name} 没有日志数据")
                return None
            
            # 解析日志数据
            trades = []
            equity_curve = [1000000]  # 初始资金100万
            
            for log_file in log_files:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log_data = json.loads(line.strip())
                            if log_data.get('data') and log_data['data'].get('action') in ['buy', 'sell']:
                                trades.append(log_data)
                        except:
                            continue
            
            if not trades:
                logger.warning(f"策略 {strategy_name} 没有交易记录")
                return None
            
            # 计算绩效指标
            performance = self._calculate_performance_metrics(strategy_name, trades, equity_curve)
            
            # 保存绩效数据
            self.performance_data[strategy_name] = performance
            self._save_performance_data(strategy_name, performance)
            
            return performance
            
        except Exception as e:
            logger.error(f"计算策略绩效失败: {e}")
            return None
    
    def _calculate_performance_metrics(self, strategy_name: str, trades: List[Dict], equity_curve: List[float]) -> StrategyPerformance:
        """计算绩效指标"""
        # 简化的绩效计算
        total_trades = len(trades)
        profit_trades = len([t for t in trades if t.get('profit', 0) > 0])
        loss_trades = total_trades - profit_trades
        
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0] if equity_curve else 0
        annual_return = total_return * 252 / len(equity_curve) if len(equity_curve) > 1 else 0
        
        # 计算夏普比率（简化）
        returns = np.diff(equity_curve) / equity_curve[:-1] if len(equity_curve) > 1 else [0]
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # 计算最大回撤
        max_drawdown = 0
        peak = equity_curve[0]
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        win_rate = profit_trades / total_trades if total_trades > 0 else 0
        
        return StrategyPerformance(
            strategy_name=strategy_name,
            account_id=self.strategy_states[strategy_name].get('account_id', ''),
            symbol='',  # 多品种策略
            start_time=datetime.now() - timedelta(days=30),  # 简化
            end_time=datetime.now(),
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            profit_trades=profit_trades,
            loss_trades=loss_trades,
            avg_profit=0,  # 简化
            avg_loss=0,    # 简化
            profit_factor=0,  # 简化
            equity_curve=equity_curve,
            trade_history=trades
        )
    
    def _save_performance_data(self, strategy_name: str, performance: StrategyPerformance):
        """保存绩效数据"""
        try:
            performance_file = self.performance_path / f"{strategy_name}_performance.json"
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(performance), f, ensure_ascii=False, default=str, indent=2)
            
            logger.info(f"策略 {strategy_name} 绩效数据已保存")
        except Exception as e:
            logger.error(f"保存绩效数据失败: {e}")
    
    def get_strategy_status(self) -> Dict:
        """获取所有策略状态"""
        status = {}
        for name, state in self.strategy_states.items():
            status[name] = {
                'status': state['status'],
                'start_time': state['start_time'].isoformat() if state['start_time'] else None,
                'last_update': state['last_update'].isoformat() if state['last_update'] else None,
                'error_count': state['error_count'],
                'account_id': state.get('account_id'),
                'symbols': state.get('symbols', [])
            }
        return status
    
    def reload_strategy_config(self):
        """热重载策略配置"""
        if not self.hot_reload_enabled:
            return
        
        try:
            # 重新加载配置
            self.load_strategies_from_config()
            logger.info("策略配置热重载完成")
        except Exception as e:
            logger.error(f"策略配置热重载失败: {e}")
    
    def enable_hot_reload(self, enabled: bool = True):
        """启用/禁用热重载"""
        self.hot_reload_enabled = enabled
        logger.info(f"策略热重载已{'启用' if enabled else '禁用'}")
    
    def shutdown(self):
        """关闭策略管理器"""
        logger.info("正在关闭策略管理器...")
        
        # 停止所有策略
        self.stop_all_strategies()
        
        # 等待所有线程结束
        for thread in self.strategy_threads.values():
            thread.join(timeout=5)
        
        logger.info("策略管理器已关闭") 