import json
import logging
from typing import Any, Union

import pandas as pd
from tornado.web import RequestHandler

from define.base.exception import BaseException
from define.base.exception import RequestException
from define.enum.error import ErrorCode, ErrorMsg
from define.enum.response_model import Status, Message
from define.enum.staff_admin import RuleAction
from utils.user_admin.models import AuthRuleAsync
from define.base.ApiCode import ApiCode
from utils.format import json_serial, CustomJSONEncoder


class BaseHandler(RequestHandler):

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        # 初始参数
        self.request_data = dict()
        self.api_code = ApiCode()

    def get_body_json_to_dict(self):
        if self.request.method not in ["GET", "OPTIONS"] and self.request.body:
            try:
                body_data = json.loads(self.request.body)
                self.request_data = dict(**self.request_data, **body_data)
            except Exception as e:
                logging.info(e)

    def get_query_to_dict(self):
        arguments = self.request.arguments
        query_params = {
            x: arguments.get(x)[0].decode("utf-8") for x in arguments.keys()
        }
        self.request_data = dict(**self.request_data, **query_params)

    def get_json_argument(self, name, default=None):
        args = json.loads(self.request.body)
        if name in args:
            return args[name]
        elif default is not None:
            return default
        else:
            raise BaseException(ErrorCode.PARAMS_ERROR, ErrorMsg.PARAMS_ERROR)

    def prepare(self):
        # 前置预处理方法, 在执行对应的请求方法之前调用
        # 聚合 body、query、path  参数
        self.get_body_json_to_dict()
        self.get_query_to_dict()

    def finish_json(self, api_code):
        self.set_header('Content-type', 'application/json')
        request_data = dict(code=api_code.code, data=api_code.data, msg=api_code.msg)
        request_json = json.dumps(request_data, default=json_serial)
        self.set_status(api_code.status)
        self.finish(request_json)

    def ensure_json_serializable(self, data):
        json_data = json.dumps(data, cls=CustomJSONEncoder, ensure_ascii=False)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        return json_data

    def write(self, chunk: Union[str, bytes, dict]) -> None:
        if isinstance(chunk, dict):
            chunk = self.ensure_json_serializable(chunk)
        return super().write(chunk)

    def get_current_user(self, raise_exception=True) -> Any:
        if username := self.request.headers.get("user-name"):
            return self.decode_argument(username)
        if raise_exception:
            raise RequestException(Status.FAILED, f"用户不存在")
        return None

    @classmethod
    def handle_paginated_results(cls, query_result, total="total", results="results"):
        query_result = query_result[0]
        paginated_results = query_result["paginatedResults"]
        total_count = query_result["totalCount"][0]["count"] if paginated_results else 0
        return {total: total_count, results: paginated_results}

    @classmethod
    def handle_paginated_df(cls, query_result, total="total", results="results"):
        df = pd.DataFrame(query_result)
        df["totalCount"] = df["totalCount"].apply(lambda x: 0 if not x else x[0]["count"])
        df.rename({"totalCount": total, "paginatedResults": results}, axis=1, inplace=True)
        return df
