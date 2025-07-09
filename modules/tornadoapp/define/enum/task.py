'''
Author: hanlinwu
E-mail: hanlinwu@tencent.com
Description: AIGC任务基础信息
'''
class AIGCTask(object):
    TASK_ID = "task_id"
    JOB_ID = "job_id"
    MODE = "mode"
    USER = "user"
    STATUS_CODE = "status_code"
    ERROR_CODE = "error_code"
    ERROR_MSG = "error_msg"
    ERROR_DETAIL = "error_detail"
    CREATE_TIME = "create_time"
    START_TIME = "start_time"
    END_TIME = "end_time"

class AIGC_Quality_Report(object):
    COMMIT = "commit"
    COMMIT_DATE = "commit_date"
    MODE = "mode"
    AUTHOR = "author"
    AMOUNT = "test_sample_amount"
    SUCCESS_RATE = "success_rate"
    ENV = 'env'

class AIGC_Pipeline_Info(object):
    MODE = "mode"
    ENV = 'env'
    COMMIT = "commit"
    GIT_ADDR = "git_addr"
    PRINCIPAL = "principal"
    BK_URL = "bk_url"
    LOG_URL = "log_url"
    DEBUG_INTRODUCE = "debug_introduce"

class TaskStatus(object):
    FINISH = 0
    CREATE = 1
    PROCESSING = 2
    ERROR = 3

class LipEmotionBusiness(object):
    NGR_FORMAL = "NGR正式业务"
    NGR_TEST = "NGR调试平台"
    AINPC = "AINPC工具"
    WEB_TEST = "网页测试"