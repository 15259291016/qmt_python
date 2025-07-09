import os

import yaml


def returnConfigPath():
    """
    返回配置文件夹路径
    :return:
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(current_path), 'config')
    return config_path + os.sep


def returnConfigData():
    """
    返回配置文件数据（YAML格式）
    :return:
    """
    config_path = returnConfigPath()
    config_file_path = os.path.join(config_path, "Config.yaml")
    with open(config_file_path, mode='r', encoding='UTF-8') as file:
        configData = yaml.safe_load(file)
    return configData
