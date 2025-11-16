import json
import logging
from datetime import date, datetime
from typing import Any, Dict, Union

import pandas as pd
import tornado.web
from bson import ObjectId
from requests import RequestException
from tornado.web import RequestHandler

from modules.tornadoapp.enum.error import ErrorCode, ErrorMsg
from modules.tornadoapp.utils.format import CustomJSONEncoder

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    if isinstance(obj, bytes):
        return str(obj, 'utf-8')
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("Type {}s not serializable".format(type(obj)))

    
class ApiCode:
    def __init__(self, ):
        self.status = 200
        self.code = 0
        self.msg = "请求成功"
        self.data = None

    def success(self, data=None, msg='请求成功'):
        self.msg = msg
        self.data = data
        return self

    def unknown_error(self, msg):
        self.code = -1
        self.msg = msg
        return self

    def params_err(self, form):
        self.code = -1
        self.data = dict()
        msg = ""
        for field in form.errors:
            self.data[field] = form.errors[field]
            msg = form.errors[field][0]
        self.msg = msg
        return self


class BaseHandler(RequestHandler):
    """
    Tornado基础Handler，统一请求参数解析、日志、响应格式化等。
    """

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

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")    # 这个地方可以写域名
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Access-Control-Max-Age", 1000)
        self.set_header("Content-type", "application/json")

    def get_query_to_dict(self):
        arguments = self.request.arguments
        query_params = {
            k: v[0].decode("utf-8") for k, v in arguments.items()
        }
        self.request_data.update(query_params)

    def get_json_argument(self, name, default=None):
        try:
            args = json.loads(self.request.body)
        except Exception:
            args = {}
        if name in args:
            return args[name]
        elif default is not None:
            return default
        else:
            raise BaseException(ErrorCode.PARAMS_ERROR, ErrorMsg.PARAMS_ERROR)

    def prepare(self):
        # 请求日志
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
        username = self.request.headers.get("user-name")
        if username:
            return self.decode_argument(username)
        if raise_exception:
            raise RequestException(ErrorCode.PARAMS_ERROR, ErrorMsg.PARAMS_ERROR)
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

    def finish_data(self, data, code=0, msg="success", status=200):
        """
        统一返回接口数据，data可以是list、dict等任意可序列化对象
        """
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        response = {
            "code": code,
            "data": data,
            "msg": msg
        }
        self.set_status(status)
        self.finish(json.dumps(response, ensure_ascii=False))