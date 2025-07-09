'''
Author: hanlinwu
E-mail: hanlinwu@tencent.com
Description: 数据格式化
'''
import json
import logging
from datetime import date, datetime, timedelta
from enum import Enum

from beanie import PydanticObjectId
from bson import ObjectId

from utils.time_util import datetime2str


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj)

def format_res(code,data,msg):
    res = {
        "code":code,
        "data":data,
        "msg":msg
    }
    return json.dumps(res, cls=JSONEncoder)

def format_res_for_lip(code,data,msg):
    res = {
        "error_code":code,
        "error_msg":msg
    }
    res.update(data)
    return json.dumps(res, cls=JSONEncoder)


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


def get_role_info(req):
    role_name = req.get_argument("role_name", default="")
    business_id = int(req.get_argument("business_id", default=0))
    part = int(req.get_argument("part", default=1))
    role_info = {
        "role_name" : role_name,
        "business_id" : int(business_id),
        "part" : int(part),
    }
    logging.info("role_info:", role_info)
    return role_info


class CustomJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime):
            return datetime2str(o)
        if isinstance(o, date):
            return o.strftime("%F")
        if isinstance(o, bytes):
            return str(o, "utf-8")
        if isinstance(o, ObjectId) or isinstance(o, PydanticObjectId):
            return str(o)
        if isinstance(o, Enum):
            return o.value
        return str(o)


class MongoResJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime("%F %X")
        if isinstance(o, date):
            return o.strftime("%F")
        if isinstance(o, bytes):
            return str(o, "utf-8")
        if isinstance(o, ObjectId):
            return str(o)
        return str(o)