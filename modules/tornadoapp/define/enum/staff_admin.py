from enum import Enum


class PageLevel(str, Enum):
    """ 页面信息级别 """
    MENU = 'menu'           # 菜单级
    PAGE = 'page'           # 页面级
    ELEMENT = 'element'     # 组件级
    RULE = 'rule'           # 规则级


class RuleAction(str, Enum):
    """ 规则信息行为 """
    CREATE = 'create'       # 创建
    READ = 'read'           # 读取
    UPDATE = 'update'       # 修改
    DELETE = 'delete'       # 删除
    NONE = "None"            # 无查看和修改权限


class PageName(str, Enum):
    """ 页面名称 """
    Annotation = 'Annotation'   # 标注平台
    Glow = 'Glow'               # Glow 页面
