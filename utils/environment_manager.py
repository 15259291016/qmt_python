#!/usr/bin/env python3
"""
环境管理器
处理模拟和实盘环境的切换和管理
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from enum import Enum

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ConfigServer as Cs

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Environment(Enum):
    """环境枚举"""
    SIMULATION = "SIMULATION"
    PRODUCTION = "PRODUCTION"


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, default_environment: str = 'SIMULATION'):
        """
        初始化环境管理器
        
        Args:
            default_environment: 默认环境
        """
        self.current_environment = Environment(default_environment.upper())
        self.config_cache = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """加载所有环境配置"""
        try:
            environments = Cs.listEnvironments()
            for env_name, env_config in environments.items():
                self.config_cache[env_name] = env_config
            logger.info(f"已加载 {len(environments)} 个环境配置")
        except Exception as e:
            logger.error(f"加载环境配置失败: {e}")
    
    def switch_environment(self, environment: str) -> bool:
        """
        切换环境
        
        Args:
            environment: 目标环境名称
            
        Returns:
            是否切换成功
        """
        try:
            if environment.upper() not in [e.value for e in Environment]:
                logger.error(f"不支持的环境: {environment}")
                return False
            
            if not Cs.validateEnvironment(environment):
                logger.error(f"环境配置无效: {environment}")
                return False
            
            old_env = self.current_environment.value
            self.current_environment = Environment(environment.upper())
            
            logger.info(f"环境切换成功: {old_env} -> {self.current_environment.value}")
            return True
            
        except Exception as e:
            logger.error(f"环境切换失败: {e}")
            return False
    
    def get_current_environment(self) -> str:
        """获取当前环境"""
        return self.current_environment.value
    
    def get_qmt_path(self) -> str:
        """获取当前环境的QMT路径"""
        return Cs.getQmtPath(self.current_environment.value)
    
    def get_account(self) -> str:
        """获取当前环境的账户"""
        return Cs.getAccount(self.current_environment.value)
    
    def get_environment_name(self) -> str:
        """获取当前环境的显示名称"""
        return Cs.getEnvironmentName(self.current_environment.value)
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return Cs.getDatabaseConfig()
    
    def get_tushare_token(self) -> str:
        """获取Tushare Token"""
        return Cs.getTushareToken()
    
    def is_simulation(self) -> bool:
        """是否为模拟环境"""
        return self.current_environment == Environment.SIMULATION
    
    def is_production(self) -> bool:
        """是否为实盘环境"""
        return self.current_environment == Environment.PRODUCTION
    
    def get_environment_info(self) -> Dict[str, Any]:
        """获取当前环境信息"""
        return {
            'environment': self.current_environment.value,
            'name': self.get_environment_name(),
            'qmt_path': self.get_qmt_path(),
            'account': self.get_account(),
            'is_simulation': self.is_simulation(),
            'is_production': self.is_production()
        }
    
    def validate_current_environment(self) -> bool:
        """验证当前环境配置"""
        try:
            qmt_path = self.get_qmt_path()
            account = self.get_account()
            
            if not qmt_path or not account:
                logger.error(f"环境配置不完整: QMT_PATH={qmt_path}, ACCOUNT={account}")
                return False
            
            if not os.path.exists(qmt_path):
                logger.warning(f"QMT路径不存在: {qmt_path}")
                return False
            
            logger.info(f"环境配置验证通过: {self.get_environment_name()}")
            return True
            
        except Exception as e:
            logger.error(f"环境配置验证失败: {e}")
            return False
    
    def list_available_environments(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用环境"""
        return Cs.listEnvironments()
    
    def print_environment_info(self):
        """打印当前环境信息"""
        info = self.get_environment_info()
        print(f"\n当前环境信息:")
        print("=" * 50)
        print(f"环境类型: {info['environment']}")
        print(f"环境名称: {info['name']}")
        print(f"QMT路径: {info['qmt_path']}")
        print(f"账户: {info['account']}")
        print(f"是否模拟: {info['is_simulation']}")
        print(f"是否实盘: {info['is_production']}")
        print("=" * 50)


# 全局环境管理器实例
env_manager = EnvironmentManager()


def get_env_manager() -> EnvironmentManager:
    """获取环境管理器实例"""
    return env_manager


def switch_to_simulation():
    """切换到模拟环境"""
    return env_manager.switch_environment('SIMULATION')


def switch_to_production():
    """切换到实盘环境"""
    return env_manager.switch_environment('PRODUCTION')


def get_current_config() -> Dict[str, Any]:
    """获取当前环境配置"""
    return {
        'qmt_path': env_manager.get_qmt_path(),
        'account': env_manager.get_account(),
        'environment': env_manager.get_current_environment(),
        'database': env_manager.get_database_config(),
        'tushare_token': env_manager.get_tushare_token()
    }


def run_in_environment(environment: str, func, *args, **kwargs):
    """
    在指定环境中运行函数
    
    Args:
        environment: 环境名称
        func: 要运行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果
    """
    old_env = env_manager.get_current_environment()
    
    try:
        # 切换到指定环境
        if env_manager.switch_environment(environment):
            logger.info(f"在 {environment} 环境中执行函数")
            result = func(*args, **kwargs)
            return result
        else:
            logger.error(f"切换到 {environment} 环境失败")
            return None
    finally:
        # 恢复原环境
        env_manager.switch_environment(old_env)


if __name__ == "__main__":
    # 测试环境管理器
    print("🚀 环境管理器测试")
    print("=" * 60)
    
    # 显示当前环境
    env_manager.print_environment_info()
    
    # 列出所有可用环境
    environments = env_manager.list_available_environments()
    print(f"\n可用环境:")
    for env_name, env_config in environments.items():
        print(f"  - {env_name}: {env_config.get('NAME', env_name)}")
    
    # 测试环境切换
    print(f"\n测试环境切换:")
    
    # 切换到实盘环境
    if env_manager.switch_environment('PRODUCTION'):
        env_manager.print_environment_info()
    
    # 切换回模拟环境
    if env_manager.switch_environment('SIMULATION'):
        env_manager.print_environment_info()
    
    # 验证环境配置
    print(f"\n环境配置验证:")
    for env_name in ['SIMULATION', 'PRODUCTION']:
        if env_manager.switch_environment(env_name):
            is_valid = env_manager.validate_current_environment()
            print(f"  {env_name}: {'✅ 有效' if is_valid else '❌ 无效'}")
    
    print("\n✅ 环境管理器测试完成") 