import yaml
import os


def returnConfigPath():
    """
    返回配置文件夹路径
    :return:
    """
    current_path = os.path.dirname(__file__)
    current_list_path = current_path.split('\\')[0:-1]
    configPath = '/'.join(current_list_path) + '/config/'
    return configPath


def returnConfigData():
    """
    返回配置文件数据（YAML格式）
    :return:
    """
    current_path = returnConfigPath()
    configData = yaml.load(open(current_path + '/Config.yaml', mode='r', encoding='UTF-8'), yaml.Loader)
    return configData