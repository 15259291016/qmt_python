"""
基础视图类
提供统一的响应格式化功能
"""
from typing import Dict, Any, Optional
from tornado.web import RequestHandler


class BaseView:
    """基础视图类，提供响应格式化方法"""
    
    @staticmethod
    def success_response(data: Any = None, msg: str = "success", code: int = 0) -> Dict[str, Any]:
        """
        成功响应格式
        
        Args:
            data: 响应数据
            msg: 响应消息
            code: 状态码，0表示成功
            
        Returns:
            格式化后的响应字典
        """
        response = {
            "code": code,
            "msg": msg,
            "data": data
        }
        return response
    
    @staticmethod
    def error_response(msg: str = "error", code: int = 1, data: Any = None) -> Dict[str, Any]:
        """
        错误响应格式
        
        Args:
            msg: 错误消息
            code: 错误码，非0表示失败
            data: 错误详情数据
            
        Returns:
            格式化后的错误响应字典
        """
        response = {
            "code": code,
            "msg": msg,
            "data": data
        }
        return response
    
    @staticmethod
    def paginated_response(
        items: list,
        total: int,
        page: int = 1,
        page_size: int = 20,
        msg: str = "success"
    ) -> Dict[str, Any]:
        """
        分页响应格式
        
        Args:
            items: 当前页数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页大小
            msg: 响应消息
            
        Returns:
            格式化后的分页响应字典
        """
        return {
            "code": 0,
            "msg": msg,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

