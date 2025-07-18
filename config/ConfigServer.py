import os
import yaml
from typing import Dict, Any, Optional


def returnConfigPath():
    """
    返回配置文件夹路径
    :return: 配置文件夹路径
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(current_path), 'config')
    return config_path + os.sep


def returnConfigData():
    """
    返回配置文件数据（YAML格式）
    :return: 配置数据字典
    """
    config_path = returnConfigPath()
    config_file_path = os.path.join(config_path, "Config.yaml")
    with open(config_file_path, mode='r', encoding='UTF-8') as file:
        configData = yaml.safe_load(file)
    return configData


def getEnvironmentConfig(environment: str = 'SIMULATION') -> Dict[str, Any]:
    """
    获取指定环境的配置
    
    Args:
        environment: 环境名称 ('SIMULATION' 或 'PRODUCTION')
        
    Returns:
        环境配置字典
    """
    config_data = returnConfigData()
    
    if environment.upper() == 'SIMULATION':
        return config_data.get('SIMULATION', {})
    elif environment.upper() == 'PRODUCTION':
        return config_data.get('PRODUCTION', {})
    else:
        raise ValueError(f"不支持的环境: {environment}")


def getDatabaseConfig() -> Dict[str, Any]:
    """
    获取数据库配置
    
    Returns:
        数据库配置字典
    """
    config_data = returnConfigData()
    return config_data.get('DATABASE', {})


def getTushareToken() -> str:
    """
    获取Tushare Token
    
    Returns:
        Tushare Token字符串
    """
    config_data = returnConfigData()
    return config_data.get('toshare_token', '')


def getQmtPath(environment: str = 'SIMULATION') -> str:
    """
    获取指定环境的QMT路径
    
    Args:
        environment: 环境名称
        
    Returns:
        QMT路径
    """
    env_config = getEnvironmentConfig(environment)
    return env_config.get('QMT_PATH', '')


def getAccount(environment: str = 'SIMULATION') -> str:
    """
    获取指定环境的账户
    
    Args:
        environment: 环境名称
        
    Returns:
        账户字符串
    """
    env_config = getEnvironmentConfig(environment)
    return env_config.get('ACCOUNT', '')


def getEnvironmentName(environment: str = 'SIMULATION') -> str:
    """
    获取指定环境的名称
    
    Args:
        environment: 环境名称
        
    Returns:
        环境显示名称
    """
    env_config = getEnvironmentConfig(environment)
    return env_config.get('NAME', environment)


def validateEnvironment(environment: str) -> bool:
    """
    验证环境配置是否有效
    
    Args:
        environment: 环境名称
        
    Returns:
        是否有效
    """
    try:
        env_config = getEnvironmentConfig(environment)
        return bool(env_config.get('QMT_PATH') and env_config.get('ACCOUNT'))
    except:
        return False


def listEnvironments() -> Dict[str, Dict[str, Any]]:
    """
    列出所有可用环境
    
    Returns:
        环境配置字典
    """
    config_data = returnConfigData()
    environments = {}
    
    if 'SIMULATION' in config_data:
        environments['SIMULATION'] = config_data['SIMULATION']
    if 'PRODUCTION' in config_data:
        environments['PRODUCTION'] = config_data['PRODUCTION']
    
    return environments
