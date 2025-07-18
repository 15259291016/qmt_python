# coding=utf-8
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

import tornado.web
import tornado.ioloop

from .manager import StrategyManager

logger = logging.getLogger(__name__)


class StrategyStatusHandler(tornado.web.RequestHandler):
    """策略状态查询接口"""
    
    def initialize(self, strategy_manager: StrategyManager):
        self.strategy_manager = strategy_manager
    
    def get(self):
        """获取所有策略状态"""
        try:
            status = self.strategy_manager.get_strategy_status()
            self.write({
                'code': 200,
                'message': '获取策略状态成功',
                'data': status
            })
        except Exception as e:
            logger.error(f"获取策略状态失败: {e}")
            self.write({
                'code': 500,
                'message': f'获取策略状态失败: {e}',
                'data': None
            })


class StrategyControlHandler(tornado.web.RequestHandler):
    """策略控制接口"""
    
    def initialize(self, strategy_manager: StrategyManager):
        self.strategy_manager = strategy_manager
    
    def post(self):
        """控制策略启停"""
        try:
            data = json.loads(self.request.body)
            action = data.get('action')
            strategy_name = data.get('strategy_name')
            
            if not action or not strategy_name:
                self.write({
                    'code': 400,
                    'message': '缺少必要参数: action, strategy_name',
                    'data': None
                })
                return
            
            if action == 'start':
                success = self.strategy_manager.start_strategy(strategy_name)
                message = f"策略 {strategy_name} 启动{'成功' if success else '失败'}"
            elif action == 'stop':
                success = self.strategy_manager.stop_strategy(strategy_name)
                message = f"策略 {strategy_name} 停止{'成功' if success else '失败'}"
            elif action == 'start_all':
                self.strategy_manager.start_all_strategies()
                message = "所有策略启动成功"
                success = True
            elif action == 'stop_all':
                self.strategy_manager.stop_all_strategies()
                message = "所有策略停止成功"
                success = True
            else:
                self.write({
                    'code': 400,
                    'message': f'不支持的操作: {action}',
                    'data': None
                })
                return
            
            self.write({
                'code': 200 if success else 500,
                'message': message,
                'data': {'success': success}
            })
            
        except Exception as e:
            logger.error(f"策略控制失败: {e}")
            self.write({
                'code': 500,
                'message': f'策略控制失败: {e}',
                'data': None
            })


class StrategyPerformanceHandler(tornado.web.RequestHandler):
    """策略绩效查询接口"""
    
    def initialize(self, strategy_manager: StrategyManager):
        self.strategy_manager = strategy_manager
    
    def get(self, strategy_name: str = None):
        """获取策略绩效"""
        try:
            if strategy_name:
                # 获取单个策略绩效
                performance = self.strategy_manager.calculate_performance(strategy_name)
                if performance:
                    self.write({
                        'code': 200,
                        'message': f'获取策略 {strategy_name} 绩效成功',
                        'data': asdict(performance)
                    })
                else:
                    self.write({
                        'code': 404,
                        'message': f'策略 {strategy_name} 绩效数据不存在',
                        'data': None
                    })
            else:
                # 获取所有策略绩效
                performances = {}
                for name in self.strategy_manager.strategies:
                    perf = self.strategy_manager.calculate_performance(name)
                    if perf:
                        performances[name] = asdict(perf)
                
                self.write({
                    'code': 200,
                    'message': '获取所有策略绩效成功',
                    'data': performances
                })
                
        except Exception as e:
            logger.error(f"获取策略绩效失败: {e}")
            self.write({
                'code': 500,
                'message': f'获取策略绩效失败: {e}',
                'data': None
            })


class StrategyConfigHandler(tornado.web.RequestHandler):
    """策略配置管理接口"""
    
    def initialize(self, strategy_manager: StrategyManager):
        self.strategy_manager = strategy_manager
    
    def get(self):
        """获取策略配置"""
        try:
            configs = []
            for name, strategy in self.strategy_manager.strategies.items():
                config = {
                    'name': name,
                    'class': strategy.__class__.__name__,
                    'params': strategy.get_params() if hasattr(strategy, 'get_params') else {},
                    'status': self.strategy_manager.strategy_states[name]['status'],
                    'account_id': self.strategy_manager.strategy_states[name].get('account_id'),
                    'symbols': self.strategy_manager.strategy_states[name].get('symbols', [])
                }
                configs.append(config)
            
            self.write({
                'code': 200,
                'message': '获取策略配置成功',
                'data': configs
            })
            
        except Exception as e:
            logger.error(f"获取策略配置失败: {e}")
            self.write({
                'code': 500,
                'message': f'获取策略配置失败: {e}',
                'data': None
            })
    
    def post(self):
        """更新策略配置"""
        try:
            data = json.loads(self.request.body)
            strategy_name = data.get('strategy_name')
            account_id = data.get('account_id')
            symbols = data.get('symbols', [])
            
            if not strategy_name or not account_id:
                self.write({
                    'code': 400,
                    'message': '缺少必要参数: strategy_name, account_id',
                    'data': None
                })
                return
            
            success = self.strategy_manager.assign_strategy_to_account(strategy_name, account_id, symbols)
            
            self.write({
                'code': 200 if success else 500,
                'message': f'策略配置更新{"成功" if success else "失败"}',
                'data': {'success': success}
            })
            
        except Exception as e:
            logger.error(f"更新策略配置失败: {e}")
            self.write({
                'code': 500,
                'message': f'更新策略配置失败: {e}',
                'data': None
            })


class StrategyLogHandler(tornado.web.RequestHandler):
    """策略日志查询接口"""
    
    def initialize(self, strategy_manager: StrategyManager):
        self.strategy_manager = strategy_manager
    
    def get(self, strategy_name: str = None):
        """获取策略日志"""
        try:
            from pathlib import Path
            
            if strategy_name:
                # 获取单个策略日志
                log_files = list(self.strategy_manager.log_path.glob(f"{strategy_name}_*.json"))
                logs = []
                
                for log_file in log_files[-5:]:  # 最近5个日志文件
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                log_data = json.loads(line.strip())
                                logs.append(log_data)
                            except:
                                continue
                
                self.write({
                    'code': 200,
                    'message': f'获取策略 {strategy_name} 日志成功',
                    'data': logs[-100:]  # 最近100条日志
                })
            else:
                # 获取所有策略日志概览
                log_overview = {}
                for name in self.strategy_manager.strategies:
                    log_files = list(self.strategy_manager.log_path.glob(f"{name}_*.json"))
                    log_overview[name] = {
                        'log_files_count': len(log_files),
                        'latest_log_file': log_files[-1].name if log_files else None
                    }
                
                self.write({
                    'code': 200,
                    'message': '获取策略日志概览成功',
                    'data': log_overview
                })
                
        except Exception as e:
            logger.error(f"获取策略日志失败: {e}")
            self.write({
                'code': 500,
                'message': f'获取策略日志失败: {e}',
                'data': None
            })


class StrategyHotReloadHandler(tornado.web.RequestHandler):
    """策略热重载接口"""
    
    def initialize(self, strategy_manager: StrategyManager):
        self.strategy_manager = strategy_manager
    
    def post(self):
        """热重载策略配置"""
        try:
            data = json.loads(self.request.body)
            enabled = data.get('enabled', True)
            
            if enabled:
                self.strategy_manager.reload_strategy_config()
                message = "策略配置热重载完成"
            else:
                self.strategy_manager.enable_hot_reload(False)
                message = "策略热重载已禁用"
            
            self.write({
                'code': 200,
                'message': message,
                'data': {'enabled': enabled}
            })
            
        except Exception as e:
            logger.error(f"策略热重载失败: {e}")
            self.write({
                'code': 500,
                'message': f'策略热重载失败: {e}',
                'data': None
            })


def add_strategy_handlers(app, strategy_manager: StrategyManager):
    """添加策略管理API路由"""
    
    handlers = [
        (r"/api/strategy/status", StrategyStatusHandler, {"strategy_manager": strategy_manager}),
        (r"/api/strategy/control", StrategyControlHandler, {"strategy_manager": strategy_manager}),
        (r"/api/strategy/performance", StrategyPerformanceHandler, {"strategy_manager": strategy_manager}),
        (r"/api/strategy/performance/([^/]+)", StrategyPerformanceHandler, {"strategy_manager": strategy_manager}),
        (r"/api/strategy/config", StrategyConfigHandler, {"strategy_manager": strategy_manager}),
        (r"/api/strategy/logs", StrategyLogHandler, {"strategy_manager": strategy_manager}),
        (r"/api/strategy/logs/([^/]+)", StrategyLogHandler, {"strategy_manager": strategy_manager}),
        (r"/api/strategy/hot-reload", StrategyHotReloadHandler, {"strategy_manager": strategy_manager}),
    ]
    
    app.add_handlers(r".*", handlers)
    logger.info("策略管理API路由已添加") 