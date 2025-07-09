from enum import Enum
from typing import Iterable


class AuthAccess(int, Enum):
    """
    入口权限ID

    !!! 注意：禁止修改原有的，可添加；添加新入口时尽量递增，保证唯一
    """
    UserAdmin = 1                   # 用户管理
    Glow = 2                        # Glow页面
    AiDraw = 3                      # AiDraw原画绘制
    Demos = 4                       # 更多体验-菜单级
    Annotation = 5                  # 标注平台
    Evaluation = 6                  # 测评平台
    GpuReport = 7                   # GPU资源统计
    LipEmotionReport = 8            # 口型表情运营日报
    DynamicScene = 9                # 动态场景管理
    InstanceManager = 10            # 实例管理-菜单级
    DevOps = 11                     # 测评系统-菜单级
    LipEmotion = 12                 # 唇形表情
    BlipCaption = 13                # blip图片预处理
    Dialogue = 14                   # NPC·对话管线-菜单级
    Anchor = 15                     # 主播对话
    MusicDance = 16                 # 音乐舞蹈
    AiFace = 17                     # 捏脸
    TTS = 18                        # 语音合成
    SceneMotion = 19                # 智能动作
    VideoCapture = 20               # 身体动捕
    FaceCapture = 21                # 面部动捕
    FaceCaptureOld = 22
    FaceRetarget = 23               # 面部重定向
    BodyRetarget = 24               # 身体重定向
    SuitMatch = 25                  # 怪物猎人
    MiniGPT = 26                    # minigpt图片预处理
    SVS = 27                        # 歌声合成
    AigcPipelines = 28              # 管线管理-菜单级
    Alpha = 29                      # Alpha云游戏
    AiNpc = 30                      # AINPC直播间
    AiDrawTrainer = 31              # AiDraw模型训练
    YuanMeng = 32                   # Glow 角色列表 元梦之星的权限
    WangZhe = 33                    # Glow 角色列表 王者荣耀的权限
    AiDrawPipeline = 34             # AI·绘画管线-菜单级
    Stats = 35                      # 报表系统-菜单级
    Operation = 36                  # 运营平台-菜单级
    PerformanceReport = 37          # 性能报告-菜单级
    DynamicSceneReport = 38         # DynamicScene 性能报告
    DialougeSystemDemo = 39         # DialougeSystemDemo 性能报告
    AlphaPlusProject = 40           # AlphaPlusProject 性能报告
    AlphaVerseInstance = 41         # AlphaVerse 实例管理
    AiDrawInstance = 42             # AiDraw 实例管理
    KohyaInstance = 43              # Kohya 实例管理
    BuildingInstance = 44           # Building 实例管理
    AlphaPlusInstance = 45          # AlphaPlus 实例管理
    DynamicSceneInstance = 46       # DynamicScene 实例管理
    AlgorithmDeployment = 47        # 算法部署
    PipelinesTest = 48              # 管线测试报告
    TTSV2Test = 49                  # TTSV2 测试报告
    LipEmotionTest = 50             # LipEmotion 测试报告
    MusicDanceTest = 51             # MusicDance 测试报告
    SceneMotionTest = 52            # SceneMotion 测试报告
    AuthorityManagement = 53        # 权限管理-菜单级
    GroupAdmin = 54                 # 用户组管理
    Animation = 55                  # NPC·动画管线-菜单级
    TaskSummary = 56                # 所有任务
    TTS2 = 57                       # 语音合成 游戏角色
    GlowRole = 58                   # Glow 角色列表 所有角色的权限
    ConceptDemos = 59               # ConceptDemos 概念Demos
    InteriorMaterial = 60           # 室内材质
    Admin = 61                      # 后台管理按钮
    AppraisalTask = 62              # 评测任务页面
    AppraisalResult = 63            # 评测结果页面
    Home = 64                       # 首页

    @classmethod
    def serialize(cls, values: Iterable[int], elem_type: str):
        s = set(cls)

        return {
            'str': [cls(v).name for v in values if v in s],
            'dict': [{'id': v, 'name': cls(v).name} for v in values if v in s]
        }.get(elem_type, [])



