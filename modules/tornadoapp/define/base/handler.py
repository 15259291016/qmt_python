import json
import logging
from typing import Any, Union, Type, TypeVar, get_type_hints, get_origin, get_args
from inspect import signature, Parameter

import pandas as pd
from tornado.web import RequestHandler
from pydantic import BaseModel, ValidationError

from .exception import BaseException
from .exception import RequestException
from modules.tornadoapp.define.enum.error import ErrorCode, ErrorMsg
from modules.tornadoapp.define.enum.response_model import Status, Message
from modules.tornadoapp.define.enum.staff_admin import RuleAction
# from utils.user_admin.models import AuthRuleAsync
from .ApiCode import ApiCode
from modules.tornadoapp.utils.format import json_serial, CustomJSONEncoder

T = TypeVar('T', bound=BaseModel)


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
            except json.JSONDecodeError as e:
                logging.warning(f"JSON解析失败: {e}")
            except Exception as e:
                logging.error(f"请求体解析失败: {e}", exc_info=True)

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
    
    def parse_pydantic_model(self, model_class: Type[T], data: dict = None) -> T:
        """
        解析Pydantic模型（从请求体或传入数据）
        
        Args:
            model_class: Pydantic模型类
            data: 数据字典，如果为None则从请求体解析
        
        Returns:
            Pydantic模型实例
        
        Raises:
            ValidationError: 验证失败
        """
        if data is None:
            if not self.request.body:
                raise BaseException(ErrorCode.PARAMS_ERROR, "请求体为空")
            try:
                data = json.loads(self.request.body)
            except json.JSONDecodeError as e:
                raise BaseException(ErrorCode.PARAMS_ERROR, f"JSON解析失败: {str(e)}")
        
        try:
            return model_class(**data)
        except ValidationError as e:
            error_msg = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
            raise BaseException(ErrorCode.PARAMS_ERROR, f"参数验证失败: {error_msg}")
    
    def parse_query_params(self, model_class: Type[T]) -> T:
        """
        从查询参数解析Pydantic模型
        
        Args:
            model_class: Pydantic模型类
        
        Returns:
            Pydantic模型实例
        """
        query_data = {}
        for key in self.request.arguments:
            value = self.get_argument(key, None)
            if value is not None:
                # 尝试类型转换
                sig = signature(model_class)
                if key in sig.parameters:
                    param = sig.parameters[key]
                    param_type = param.annotation
                    if param_type != Parameter.empty:
                        # 简单类型转换
                        if param_type == bool:
                            value = value.lower() in ('true', '1', 'yes', 'on')
                        elif param_type == int:
                            try:
                                value = int(value)
                            except (ValueError, TypeError):
                                raise BaseException(ErrorCode.PARAMS_ERROR, f"参数 {key} 必须是整数")
                        elif param_type == float:
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                raise BaseException(ErrorCode.PARAMS_ERROR, f"参数 {key} 必须是数字")
                query_data[key] = value
        
        try:
            return model_class(**query_data)
        except ValidationError as e:
            error_msg = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
            raise BaseException(ErrorCode.PARAMS_ERROR, f"查询参数验证失败: {error_msg}")

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
