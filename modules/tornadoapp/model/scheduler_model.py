from beanie import Document, Indexed
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field
from enum import Enum


class TriggerType(str, Enum):
    """触发器类型"""
    CRON = "cron"           # Cron表达式
    INTERVAL = "interval"   # 间隔触发
    DATE = "date"          # 单次执行


class JobStatus(str, Enum):
    """任务状态"""
    ACTIVE = "active"       # 激活
    PAUSED = "paused"      # 暂停
    REMOVED = "removed"    # 已删除


class ScheduledJob(Document):
    """定时任务模型"""
    
    name: Indexed(str) = Field(..., description="任务名称")
    job_id: Indexed(str, unique=True) = Field(..., description="任务ID（唯一）")
    func_path: str = Field(..., description="任务函数路径，格式：module.path:function_name")
    trigger_type: TriggerType = Field(..., description="触发器类型")
    
    # Cron触发器参数
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    day_of_week: Optional[str] = Field(None, description="星期几 (0-6 或 mon-fri)")
    hour: Optional[int] = Field(None, description="小时 (0-23)")
    minute: Optional[int] = Field(None, description="分钟 (0-59)")
    second: Optional[int] = Field(None, description="秒 (0-59)")
    
    # Interval触发器参数
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    interval_minutes: Optional[int] = Field(None, description="间隔分钟数")
    interval_hours: Optional[int] = Field(None, description="间隔小时数")
    interval_days: Optional[int] = Field(None, description="间隔天数")
    
    # Date触发器参数
    run_date: Optional[datetime] = Field(None, description="执行日期时间")
    
    # 任务参数
    args: List[Any] = Field(default=[], description="位置参数列表")
    kwargs: Dict[str, Any] = Field(default={}, description="关键字参数字典")
    
    # 任务状态
    status: JobStatus = Field(default=JobStatus.ACTIVE, description="任务状态")
    is_active: bool = Field(default=True, description="是否激活")
    
    # 执行信息
    next_run_time: Optional[datetime] = Field(None, description="下次执行时间")
    last_run_time: Optional[datetime] = Field(None, description="上次执行时间")
    run_count: int = Field(default=0, description="执行次数")
    error_count: int = Field(default=0, description="错误次数")
    last_error: Optional[str] = Field(None, description="最后错误信息")
    
    # 元数据
    description: Optional[str] = Field(None, description="任务描述")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者ID")
    
    class Settings:
        name = "scheduled_jobs"
        indexes = [
            "job_id",
            "name",
            "status",
            "is_active",
            ("name", "status"),
            ("status", "is_active"),
        ]
    
    class Config:
        schema_extra = {
            "example": {
                "name": "数据下载任务",
                "job_id": "download_data",
                "func_path": "utils.data:download_all_data",
                "trigger_type": "cron",
                "day_of_week": "0-4",
                "hour": 15,
                "minute": 40,
                "args": [],
                "kwargs": {},
                "description": "每周一至周五15:40执行数据下载",
                "status": "active",
                "is_active": True
            }
        }

