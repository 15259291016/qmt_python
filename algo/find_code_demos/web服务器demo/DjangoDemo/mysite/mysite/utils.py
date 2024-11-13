'''
Date: 2024-08-28 19:57:54
LastEditors: 牛智超
LastEditTime: 2024-08-28 20:02:14
FilePath: \国金项目\algo\在网上找的代码\web服务器demo\DjangoDemo\mysite\mysite\utils.py
'''
# myapp/utils.py

from rest_framework_jwt.settings import api_settings
from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission
from rest_framework import exceptions
from django.contrib.auth.models import User

User = get_user_model()

def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义 JWT 响应处理器，该函数接收 token, user 和 request 参数，
    并返回一个字典作为 HTTP 响应的内容。
    """
    # 获取 JWT 相关的设置
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    
    # 创建 payload
    payload = jwt_payload_handler(user)
    
    # 生成新的 token，这里通常不需要重新生成，因为已经在参数中传递了
    # 如果你需要根据某些条件生成不同的 token，可以在这里处理
    # token = jwt_encode_handler(payload)
    
    # 返回自定义的响应数据
    response_data = {
        'token': token,
        'user_id': user.pk,
        'username': user.username,
        'email': user.email,
        # 你可以在这里添加更多用户信息
    }
    return response_data

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user