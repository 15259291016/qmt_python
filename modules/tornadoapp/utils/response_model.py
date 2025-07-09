import functools
import io
import json
import logging
import os
import time
import traceback
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import unquote

import pandas as pd
from rich.console import Console
from rich.logging import RichHandler
from tornado.web import RequestHandler

from modules.tornadoapp.define.base.exception import RequestException
from modules.tornadoapp.define.enum.response_model import (Message,
                                                           StatisticEnum,
                                                           Status)
from modules.tornadoapp.define.enum.ym_operation_mgr import EvalFunctionType
from modules.tornadoapp.utils.config import configs
from modules.tornadoapp.utils.debug import DEBUG
from modules.tornadoapp.utils.format import CustomJSONEncoder
from modules.tornadoapp.utils.logger import logger
from modules.tornadoapp.utils.time_relative import get_utc8_datetime

log_config = configs["log_config"]
is_local = "local" in os.environ.get("DEPLOY_ENV", "")
rich_log = logging.getLogger("rich")
rich_log.setLevel("DEBUG")

if show_rich_log := log_config.get("show_rich_log", True):
    rich_log.addHandler(
        RichHandler(console=Console(width=None if is_local else 150), rich_tracebacks=True, tracebacks_show_locals=True)
    )


def upload_use_record(func=None, type1=None, type2=None, statistic_type=1):
    """
    上传元梦测评相关api使用记录-装饰器
    param statistic_type:
    1、元梦关卡换色测评 2、元梦2d参考图测评 3、LLM测评 4、测评任务GSB测评 5、测评任务MOS测评 6、腾讯文档LLM单独评测任务
    7、腾讯文档LLM对比测评任务 8、视频骨骼评测 9、AIAGENT平台使用统计 10、话术版本管理
    """
    if func is None:
        return functools.partial(upload_use_record, type1=type1, type2=type2, statistic_type=statistic_type)

    @functools.wraps(func)
    async def async_request(self, *args, **kwargs):
        user = self.request.headers.get("user-name") or self.get_query_argument("user_id", "guest")
        user = unquote(user, encoding="utf-8")
        request_data = dict()
        if self.request.method not in ["GET", "OPTIONS"] and self.request.body:
            try:
                body_data = json.loads(self.request.body)
                request_data = dict(**request_data, **body_data)
            except Exception as e:
                logging.info(e)
        arguments = self.request.arguments
        query_params = {x: arguments.get(x)[0].decode("utf-8") for x in arguments.keys()}
        request_data = dict(**request_data, **query_params)
        now_date = get_utc8_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
        if type2:
            if (
                statistic_type == StatisticEnum.YM_COLOR_CHANGE_EVALUATION.value
                or statistic_type == StatisticEnum.YM_2D_REF_GRAPH_EVALUATION.value
            ):
                # export=1 表示导出
                export = int(request_data.get("export", "0"))
                if export == 1:
                    func_type = type2
                else:
                    func_type = type1
            elif statistic_type == StatisticEnum.LLM_EVALUATION.value:
                task_type = request_data.get("task_type")
                if int(task_type) == 1:
                    func_type = type1
                else:
                    func_type = type2
            elif statistic_type == StatisticEnum.EVAL_TASK_GSB.value:
                operation = request_data.get("operation")
                if operation == "测评":
                    func_type = EvalFunctionType.EVAL_TASK.value
                elif operation == "结束":
                    func_type = EvalFunctionType.FINISH_TASK.value
                elif operation == "下载":
                    func_type = EvalFunctionType.DOWNLOAD_RESULT.value
                else:
                    func_type = EvalFunctionType.DELETE_TASK.value
            else:
                is_deleted = int(request_data.get("is_deleted", "0"))
                export = int(request_data.get("export", "0"))
                if is_deleted == 1 or export == 1:
                    func_type = type2
                else:
                    func_type = type1
        else:
            func_type = type1
            
        query = {"use_date": now_date, "user": user, "type": func_type, "statistic_type": statistic_type}
        project = None
        if statistic_type == StatisticEnum.KNOWLEDGE_BASE.value:
            project = request_data.get("project", None)
        if project:
            query["project"] = project
        await func(self, *args, **kwargs)

    return async_request


def try_except_async_request(func=None, flag=True, write_directly=False, custom_return=False, is_paginated_df=False):
    """
    捕获异常请求（异步）并格式化响应-装饰器

    :param func: 函数
    :param flag: 是否需要在最外层套一层对象
    :param write_directly: 是否直接write
    :param custom_return: 是否自定义返回结果，为True时不需要额外处理，注：如果需要上传响应结果到智研，在使用自定义响应custom_return=True时，应当return响应结果
    :param is_paginated_df: 是否是分页后的dataframe，如果是，会和未分页的dataframe处理方式有所不同

    用法：

    >>> # 前提条件
    >>> from tornado.web import Application, RequestHandler
    >>>
    >>> # Application() 要加上关键字参数 module，为当前模块
    >>> Application([], module='annotation')
    >>>
    >>> # 示例
    >>> class DemoHandler(RequestHandler):
    >>>     @try_except_async_request
    >>>     async def get(self):
    >>>         return 'example'
    >>>
    >>> # 相当于
    >>> self.write({'code': 0, 'msg': 'success', 'data': 'example'})
    >>>
    >>> # 若 flag=False
    >>> class DemoHandler(RequestHandler):
    >>>     @try_except_async_request(flag=False)
    >>>     async def get(self):
    >>>         return 'example'
    >>>
    >>> # 相当于
    >>> self.write('example')
    """
    if func is None:
        return functools.partial(
            try_except_async_request,
            flag=flag,
            write_directly=write_directly,
            custom_return=custom_return,
            is_paginated_df=is_paginated_df,
        )

    @functools.wraps(func)
    async def async_request_handler(self: RequestHandler, *args, **kwargs):
        timestamp = int(time.time())
        user = self.request.headers.get("user-name") or self.get_query_argument("user_id", "guest")
        user = unquote(user, encoding="utf-8")
        module = self.settings.get("module", "module not set")
        mode = self.__class__.__name__
        request_url = self.request.uri
        start_ms = time.time() * 1000

        try:
            form_data_args = {
                k: (b_v[0].decode("utf-8") if len(b_v) == 1 else [v.decode("utf-8") for v in b_v])
                for k, b_v in self.request.body_arguments.items()
            }
            json_form_data_args = json.dumps(form_data_args, ensure_ascii=False)
            logger.info(
                timestamp,
                user,
                module,
                request_url,
                "BeforeHandler",
                int(time.time() * 1000 - start_ms),
                f"Request: {self.request.body}",
                json_form_data_args,
            )

            data = await func(self, *args, **kwargs)
            response = data
            if custom_return:
                pass
            else:
                if write_directly:
                    self.write(data)
                else:
                    if isinstance(data, FailedResponse):
                        response = asdict(data)
                    elif isinstance(data, pd.DataFrame):
                        if is_paginated_df:
                            data = data.to_dict(orient="records")[0]
                        else:
                            data = data.to_dict(orient="records")
                        response = pd.DataFrame(
                            {"code": [Status.SUCCESS], "msg": [Message.SUCCESS], "data": [data]}
                        ).to_json(orient="records", lines=True, date_format="iso", date_unit="s", default_handler=str)
                        self.set_header("Content-Type", "application/json; charset=UTF-8")
                    else:
                        response = {"code": Status.SUCCESS, "msg": Message.SUCCESS, "data": data} if flag else data
                    if isinstance(response, dict):
                        self.set_header("Content-Type", "application/json")
                    self.write(json.dumps(response, cls=CustomJSONEncoder))
            logger.info(
                timestamp,
                user,
                module,
                request_url,
                "AfterHandler",
                int(time.time() * 1000 - start_ms),
                f"Response: {json.dumps(response, cls=CustomJSONEncoder, ensure_ascii=False) if isinstance(response, dict) else '(response being not a type of dict will not record in the log)'}",  # 文件等难以直接读取的响应内容不上传到智研日志
            )
        except RequestException as e:
            if flag:
                if not custom_return:
                    self.write({"code": e.code, "msg": repr(e), "data": e.data, "error_msg": traceback.format_exc()})

            logger.error(
                timestamp,
                user,
                module,
                request_url,
                "CustomException",
                int(time.time() * 1000 - start_ms),
                f"e: {e!r}; tb: {traceback.format_exc()}",
            )

        except Exception as e:
            if flag:
                if not custom_return:
                    self.write(
                        {
                            "code": Status.UNKNOWN_ERROR,
                            # "msg": traceback.format_exc(),
                            "msg": repr(e),
                            "data": {},
                            "error_msg": repr(traceback.format_exc()),
                        }
                    )

            logger.error(
                timestamp,
                user,
                module,
                request_url,
                "UnexpectedException",
                int(time.time() * 1000 - start_ms),
                f"e: {e!r}; tb: {traceback.format_exc()}",
            )

    return async_request_handler


@dataclass
class FailedResponse:
    code: int = Status.UNKNOWN_ERROR
    msg: str = ""
    error_msg: str = ""
    data: Any = field(default_factory=dict)
