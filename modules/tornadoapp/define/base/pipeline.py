'''
Author: hanlinwu
E-mail: hanlinwu@tencent.com
Description: 算法管线基类
'''
from trpc import context
from trpc.client.options import *
from trpc.codec.serialization import SerializationType
from trpc.codec.serialization_json import JsonSerializer
from tornado.web import RequestHandler
import random
import traceback
import json
import time
import base64
import tornado
from utils import config
from utils.logger import logger
from utils.polaris import get_node_list_by_name
from utils.task_manager import async_task_manager
from define.base.exception import BaseException
from define.enum.error import ErrorCode, ErrorMsg
from define.stub.trpc_trpc_python_group_aigc import pb,rpc
from define.stub.trpc_trpc_python_group_aigc_web.lip import rpc as lip_rpc


class BasePipeline(object):
    def __init__(self, name : str, user_polaris=None) -> None:
        self.pipeline_config = config.get_config('pipelines')[name]
        self.mode = self.pipeline_config['mode']
        self.polaris = user_polaris or self.pipeline_config['polaris']
        self.protocol = self.pipeline_config['protocol']
        self.env = self.pipeline_config['env']
        self.timeout = self.pipeline_config['timeout']
        self.proxy = rpc.TaskClientProxyImpl()
        self.proxy_lip = lip_rpc.LipTaskHttpClientProxyImpl()

    async def create_task(self, user : str) -> dict:
        task = await async_task_manager.create(self.mode, user)
        return task

    async def preprocess(self, task_id, user, request: RequestHandler, task: dict = {}) -> pb.Request_aigc:
        '''
            旧通用管线参数预处理
        '''
        try:
            _s = time.time()
            task.update(request.request.arguments)
            req = pb.Request_aigc()
            req.task_info = json.dumps(task)
            logger.info(task_id, user, "sdk", self.mode, "PreProcess", str(round(time.time() - _s, 3)), json.dumps(task))
            return req
        except Exception as exc:
            logger.error(task_id, user, "sdk", self.mode, "PreProcess", "0", "错误码 : %s\n错误信息 : %s\n错误堆栈 : "%(ErrorCode.PARAMS_ERROR, ErrorMsg.PARAMS_ERROR) + traceback.format_exc())
            raise BaseException(ErrorCode.PARAMS_ERROR, ErrorMsg.PARAMS_ERROR, detail=traceback.format_exc())
    
    async def process(self, task_id, user, request : pb.Request_aigc) -> pb.Reply_aigc:
        '''
            旧通用管线trpc请求发起
        '''
        try:
            _s = time.time()
            node_list = await get_node_list_by_name(self.polaris, self.env)
            node = node_list[random.randint(0, len(node_list))%len(node_list)]
            ctx = context.Context()
            options = [
                with_timeout(self.timeout),
                with_target(f'ip://{node.address}'),
                with_protocol(self.protocol),
                with_serialization_type(SerializationType.PB),
                with_network('tcp')
            ]
            logger.info(task_id, user, "sdk", self.mode, "ProcessStart", str(round(time.time() - _s, 3)), str(node.address))
            result = await self.proxy.asyncExecute(ctx, request, options)
            logger.info(task_id, user, "sdk", self.mode, "ProcessEnd", str(round(time.time() - _s, 3)))
            return result
        except Exception as exc:
            logger.error(task_id, user, "sdk", self.mode, "Process", "0", "错误码 : %s\n错误信息 : %s\n错误堆栈 : "%(ErrorCode.SERVICE_ERROR, ErrorMsg.SERVICE_ERROR) + traceback.format_exc())
            raise BaseException(ErrorCode.SERVICE_ERROR, ErrorMsg.SERVICE_ERROR, detail=traceback.format_exc())
    
    async def postprocess(self, task_id, user, result : pb.Reply_aigc) -> dict:
        '''
            结果后处理
        '''
        try:
            _s = time.time()
            logger.info(task_id, user, "sdk", self.mode, "PostProcess", str(round(time.time() - _s, 3)))
            return json.loads(JsonSerializer.serialize(result))["result_info"]
        except Exception as exc:
            logger.error(task_id, user, "sdk", self.mode, "PostProcess", "0", "错误码 : %s\n错误信息 : %s\n错误堆栈 : "%(ErrorCode.RESULT_ERROR, ErrorMsg.RESULT_ERROR) + traceback.format_exc())
            raise BaseException(ErrorCode.RESULT_ERROR, ErrorMsg.RESULT_ERROR, detail=traceback.format_exc())
        
    async def run(self, task_id, user,request: RequestHandler,task :dict = {}):
        input = await self.preprocess(task_id, user,request, task)
        result = await self.process(task_id, user,input)
        output = await self.postprocess(task_id, user,result)
        return output
    
    def get_file(self, req: RequestHandler, name):
        bin_file = req.request.files.get(name)
        if bin_file == None:
            bin_file = req.get_argument("bin_file")
            bin_file = base64.b64decode(bin_file)
        else:
            bin_file = bin_file[0]["body"]
        return bin_file
    
    def change_argument_type(self, arg: str):
        if arg.isdigit():
            return int(arg)
        if "".join(arg.strip("+").strip("-").split(".")).isdigit() and arg.count('.')==1:
            return float(arg)
        if arg == "false" or arg =="False":
            return False
        if arg == "true" or arg == "True":
            return True
        return arg
        
        
# basePipeline = BasePipeline()