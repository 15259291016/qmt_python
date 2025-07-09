# -*- encoding: utf-8 -*-
"""
@File     :  link.py
@Time     :  2023/09/20 11:38:40
@Author   :  v_baojzhang
@Version  :  1.0
@Desc     :  链路日志类型
"""

from enum import Enum


class LinkType(Enum):
    WORKFLOW = "workflow"
    WORKFLOW_CONF = "workflow_conf"
    LINKLOG = "link_log"
