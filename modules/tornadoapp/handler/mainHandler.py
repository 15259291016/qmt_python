import json

import tornado.web

from modules.tornadoapp.handler.baseHandler import BaseHandler
from modules.tornadoapp.model.demomodel import DemoModel
from modules.tornadoapp.utils.response_model import try_except_async_request


def objid_to_str(obj):
    if isinstance(obj, list):
        return [objid_to_str(i) for i in obj]
    if isinstance(obj, dict):
        return {k: objid_to_str(v) for k, v in obj.items()}
    # 针对 PydanticObjectId 或 ObjectId
    if "ObjectId" in str(type(obj)):
        return str(obj)
    return obj


# 创建一个tornado app
class MainHandler(BaseHandler):
    @try_except_async_request
    async def get(self):
        res = await DemoModel.find().to_list()
        res_dict = [item.to_dict() for item in res]
        return res_dict

    @try_except_async_request
    async def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        demo = DemoModel(**data)
        await demo.save()
        return True

    @try_except_async_request
    async def put(self):
        data = json.loads(self.request.body.decode("utf-8"))
        demo = await DemoModel.find_one(DemoModel.id == data["id"])
        demo.name = data["name"]
        demo.age = data["age"]
        demo.email = data["email"]
        demo.phone = data["phone"]
        demo.address = data["address"]
        await demo.save()
        return True

    @try_except_async_request
    async def delete(self):
        data = json.loads(self.request.body.decode("utf-8"))
        demo = await DemoModel.find_one(DemoModel.id == data["id"])
        await demo.delete()
        return True