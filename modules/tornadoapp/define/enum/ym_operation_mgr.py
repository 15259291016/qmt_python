"""
元梦线上运营
"""
from enum import Enum


class EvalTaskStatus(int, Enum):
    TO_CONFIRM = -1
    PROCEEDING = 0
    FINISHED = 1


class EvalTaskType(int, Enum):
    INDIVIDUAL_EVAL = 1     # 单独测评
    COMPARISON_EVAL = 2     # 对比测评


class EvalRecordStatus(int, Enum):
    """
    测评详情的状态、测评员测评状态共用的枚举类
    注：
        测评任务中测评人的状态(eval_status)只有待测评（0）和已测评（1）两种状态，
        而详情的状态(status)则可以有三种状态：待确认（-1）、待测评（0）和已测评（1）
    """
    TO_CONFIRM = -1
    TO_EVALUATE = 0
    EVALUATED = 1


class TaskType(str, Enum):
    COLOR_CHG = "color_change"
    TD_REF_GRAPH = "2d_ref_graph"


class EvalFunctionType(Enum):
    ALL_DATA_SEARCH = 1     # 所有数据/查询
    ALL_DATA_EXPORT = 2     # 所有数据/导出
    TASK_CREATE = 3         # 测评任务/创建测评任务
    EVAL_ABOUT = 4          # 测评任务/测评相关API调用
    EVAL_DATA_EXPORT = 5    # 测评任务/导出测评数据
    USER_PATH_SEARCH = 6    # 数据分析/行为总览（桑基图）
    USER_PATH_DETAIL = 7    # 数据分析/行为路径分析详情查询
    USER_PATH_DETAIL_EXPORT = 8  # 数据分析/行为路径分析详情导出
    ALL_DATA_IMPORT = 9     # 所有数据/上传文件
    ALL_DATA_UPLOAD = 10    # 所有数据/本地数据导入
    # LLM运营功能统计
    DATA_COLLECTION_CREATE = 11  # 数据集上传
    DATA_COLLECTION_DELETE = 12  # 数据集删除
    ONE_EVALUATION_TASK_CREATE = 13  # 单独测评（创建任务）
    ONE_EVALUATION = 14   # 单独测评（测评）
    ONE_INSPECTION = 15   # 单独测评（质检）
    ONE_EVALUATION_QUICK_CREATE_DATA_COLLECTION = 16  # 单独测评（快速创建数据集）
    ONE_EVALUATION_DELETE = 17  # 单独测评（删除）
    TWO_EVALUATION_CREATE = 18  # 对比测评（创建任务）
    TWO_EVALUATION = 19  # 对比测评（测评）
    TWO_INSPECTION = 20  # 对比测评（质检）
    TWO_EVALUATION_DELETE = 21  # 对比测评（删除）
    # TTS/MOS测评功能统计
    CREATE_TASK = 22  # 创建任务
    EVAL_TASK = 23    # 测评
    FINISH_TASK = 24  # 结束
    BROWSE_RESULT = 25   # 查看结果
    DOWNLOAD_RESULT = 26  # 下载结果
    DELETE_TASK = 27  # 删除任务
    # 腾讯文档LLM运营功能统计
    TDOC_CREATE_TASK = 28  # 创建测评任务
    TDOC_TO_EVALUATION = 29  # 去测评
    TDOC_EVALUATION_DONE = 30  # 完成测评
    TDOC_TO_INSPECTION = 31   # 去质检
    TDOC_INSPECTION_DONE = 32  # 完成质检
    HOK_TASK_INSERT = 33  # 插入骨骼标注任务
    HOK_TASK_SAVE = 34  # 保存骨骼标注任务
    HOK_TASK_DELETE = 35  # 删除骨骼标注任务
    HOK_TASK_GET = 36 # 获取骨骼标注任务
    # AIAgent标注
    AGENT_CREATE_WORLD = 37  # 创建世界
    AGENT_GET_WORLD_LIST = 38  # 获取所有世界列表
    AGENT_GET_EDITABLE_WORLD_LIST = 39  # 获取个人世界列表
    AGENT_GET_WORLD_DETAILS = 40  # 获取世界详情
    AGENT_EDIT_WORLD_DETAILS = 41  # 编辑世界
    AGENT_DELETE_WORLD = 42  # 删除世界
    AGENT_CREATE_SCENARIO = 43  # 创建场景
    AGENT_DELETE_SCENARIO = 44  # 删除场景
    AGENT_GET_SCENARIO_LIST_BY_WORLDID = 45  # 获取场景列表
    AGENT_GET_SCENARIO_DETAILS = 46  # 获取场景详情
    AGENT_EDIT_SCENARIO_DETAILS = 47  # 编辑场景
    AGENT_CREATE_AGENT = 48  # 创建角色
    AGENT_GET_AGENT_DETAIL = 49  # 获取角色详情
    AGENT_MOVE_AGENT_TO_SCENARIO = 50  # 移动角色
    AGENT_GET_SCENARIO_AGENT_LIST = 51  # 获取场景角色列表
    AGENT_CONTROL_AGENT = 52  # 控制角色
    AGENT_EXPORT_WORLD = 53  # 分享世界
    AGENT_JOIN_SCEANARIO = 54  # 加入场景
    AGENT_LEAVE_SCEANARIO = 55  # 离开场景
    AGENT_GET_AGENT_LATEST_ACTION = 56  # 获取某个房间agent 的最后 action
    AGENT_CREATE_ACTION = 57  # 新增 action
    AGENT_EDIT_ACTION = 58  # 编辑 action
    AGENT_GET_ACTION_LIST = 59  # 查询 action 列表
    AGENT_SEARCH_MEMORY = 60  # 检索记忆
    AGENT_SEARCH_KNOWLEDGE = 61  # 检索知识
    AGENT_EDIT_AGENT = 62  # 编辑角色
    # 话术版本管理
    EXPORT_SCRIPT = 63  # 导出话术
    MERGE_TO_GIT = 64   # 合并到Git
    CREATE_VERSION = 65  # 新建版本
    CREATE_TEST_TASK = 66  # 新建跑测任务
    VIEW_EVENT_TEXT_AND_VOICE_INTERFACE = 67  # 查看事件文本与语音接口
    VIEW_VERSION = 68  # 查看版本
    QUERY_SPECIFIED_SCRIPT = 69  # 查询指定话术
    UPLOAD_CONFIGURATION_TABLE = 70  # 上传配置表
    DOWNLOAD_CONFIGURATION_TABLE = 71  # 下载配置表
    # 话术修改
    OVERVIEW_QUERY = 72  # 总览查询
    OVERVIEW_EXPORT = 73  # 总览导出
    VIEW_DETAILS = 74    # 查看详情
    DELETE = 75          # 删除
    CREATE_MODIFICATION = 76  # 新建修改
    REJECT_MODIFICATION = 77  # 打回修改
    PASS_INSPECTION = 78      # 质检通过
    RETEST_INSPECTION = 79    # 重新质检
    PASS_AUDIO_TEST = 80      # 听测通过
    FAIL_AUDIO_TEST = 81      # 听测不通过
    REGENERATE_AUDIO = 82     # 重新生成音频
    CREATE_QUERY = 83         # 新建查询
    # gamecore版本管理
    CREATE_PACKAGING_TASK = 84  # 新建打包任务
    QUERY_PACKAGING_TASK = 85   # 查询打包任务
    # 离线分析管理
    CREATE_ANALYSIS_TASK = 86   # 新建任务
    EXPORT_ANALYSIS_RESULT = 87  # 导出
    QUERY_ANALYSIS_TASK = 88     # 查询任务

class KnowledgeFAQManagementType(int, Enum):
    KNOWLEDGE_FAQ_MANAGEMENT_QUERY = 89     # 查询FAQ
    KNOWLEDGE_FAQ_MANAGEMENT_SAVE = 90     # 新增或编辑FAQ
    KNOWLEDGE_FAQ_MANAGEMENT_DELETE = 91     # 删除FAQ
    
    KNOWLEDGE_FAQ_PATH_SAVE = 92     # 新增或编辑FAQ路径
    KNOWLEDGE_FAQ_PATH_QUERY = 93     # 查询FAQ路径
    KNOWLEDGE_FAQ_PATH_IMPORT = 94     # 导入FAQ路径
    
    
class KnowledgeDocManagementType(int, Enum):
    KNOWLEDGE_DOC_MANAGEMENT_QUERY = 95     # 查询Doc
    KNOWLEDGE_DOC_MANAGEMENT_SAVE = 96     # 保存Doc
    KNOWLEDGE_DOC_MANAGEMENT_EDIT = 97     # 修改Doc
    KNOWLEDGE_DOC_MANAGEMENT_DELETE = 98     # 删除Doc
    
class KnowledgeTemplateManagementType(int, Enum):
    KNOWLEDGE_TEMPLATE_MANAGEMENT_QUERY = 99     # 获取知识模板管理列表
    KNOWLEDGE_TEMPLATE_MANAGEMENT_SAVE = 100     # 创建新模板管理记录
    KNOWLEDGE_TEMPLATE_MANAGEMENT_EDIT = 101     # 单个更新知识模板管理
    KNOWLEDGE_TEMPLATE_MANAGEMENT_DELETE = 102     # 批量删除知识模板管理
    
    KNOWLEDGE_DICTIONARY_QUERY = 103     # 获取知识模板列表
    KNOWLEDGE_DICTIONARY_SAVE = 104     # 批量新增知识模板
    KNOWLEDGE_DICTIONARY_EDIT = 105     # 单个更新知识模板
    KNOWLEDGE_DICTIONARY_DELETE = 106     # 批量删除知识模板
    
#知识图谱
class KnowledgeGraphManagementType(int, Enum):
    KNOWLEDGE_GRAPH_ATTR_QUERY = 107     # 查询知识图谱属性
    KNOWLEDGE_GRAPH_ATTR_EDIT = 108     # 编辑知识图谱属性
    KNOWLEDGE_GRAPH_DETAIL_QUERY = 109     # 查询知识图谱详情
    
    KNOWLEDGE_GRAPH_MANAGEMENT_QUERY = 110     # 查询知识图谱
    KNOWLEDGE_GRAPH_MANAGEMENT_SAVE = 111     # 新增知识图谱
    KNOWLEDGE_GRAPH_MANAGEMENT_EDIT = 112     # 编辑知识图谱
    KNOWLEDGE_GRAPH_MANAGEMENT_DELETE = 113     # 删除知识图谱
    
    KNOWLEDGE_GRAPH_LINK_QUERY = 114     # 查询关联关系描述
    KNOWLEDGE_GRAPH_LINK_SAVE = 115     # 新增关联关系描述
    KNOWLEDGE_GRAPH_LINK_EDIT = 116     # 更新关联关系描述
    KNOWLEDGE_GRAPH_LINK_DELETE = 117     # 删除关联关系描述
    KNOWLEDGE_GRAPH_LINK_EXPORT = 118     # 导出知识图谱
    
    
# query推荐
class KnowledgeQueryRecommendationType(int, Enum):
    KNOWLEDGE_QUERY_RECOMMENDATION_QUERY = 119     # 获取评测管理列表
    KNOWLEDGE_QUERY_RECOMMENDATION_SAVE = 120     # 创建评测管理记录
    KNOWLEDGE_QUERY_RECOMMENDATION_EDIT = 121     # 单个更新知识模板管理
    KNOWLEDGE_QUERY_RECOMMENDATION_DELETE = 122     # 批量删除知识模板管理
    
    KNOWLEDGE_QUERY_TASK_QUERY = 123     # 获取评测任务列表
    KNOWLEDGE_QUERY_TASK_SAVE = 124     # 批量修改评测任务状态
    KNOWLEDGE_QUERY_TASK_SUBMIT = 125     # 提交评测任务
    
# 运营管理
class KnowledgeOperationManagementType(int, Enum):
    KNOWLEDGE_OPERATION_QUERY = 126     # 查询专项
    KNOWLEDGE_OPERATION_CREATE = 127     # 创建专项
    KNOWLEDGE_OPERATION_EDIT = 128     # 更新专项
    KNOWLEDGE_OPERATION_DELETE = 129     # 批量删除专项
    
    KNOWLEDGE_OPERATION_NOTIFICATION = 130     # 专项通知
