"""
基础服务类
提供通用业务逻辑方法
"""
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseService:
    """基础服务类，提供通用业务逻辑方法"""
    
    def __init__(self):
        self.logger = logger
    
    def validate_params(self, params: Dict[str, Any], required: List[str]) -> tuple:
        """
        验证参数
        
        Args:
            params: 参数字典
            required: 必需参数列表
            
        Returns:
            (是否有效, 错误消息)
        """
        for key in required:
            if key not in params or params[key] is None:
                return False, f"缺少必需参数: {key}"
        return True, None
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            
        Returns:
            错误响应字典
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg
        }

