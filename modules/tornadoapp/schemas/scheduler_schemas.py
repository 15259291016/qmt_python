"""
定时任务API的Pydantic模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from modules.tornadoapp.model.scheduler_model import TriggerType, JobStatus


class CronTriggerRequest(BaseModel):
    """Cron触发器参数"""
    day_of_week: Optional[str] = Field(None, description="星期几 (0-6 或 mon-fri)", example="0-4")
    hour: Optional[int] = Field(None, description="小时 (0-23)", ge=0, le=23, example=15)
    minute: Optional[int] = Field(None, description="分钟 (0-59)", ge=0, le=59, example=40)
    second: Optional[int] = Field(0, description="秒 (0-59)", ge=0, le=59, example=0)


class IntervalTriggerRequest(BaseModel):
    """Interval触发器参数"""
    interval_seconds: Optional[int] = Field(None, description="间隔秒数", ge=1, example=60)
    interval_minutes: Optional[int] = Field(None, description="间隔分钟数", ge=1, example=5)
    interval_hours: Optional[int] = Field(None, description="间隔小时数", ge=1, example=1)
    interval_days: Optional[int] = Field(None, description="间隔天数", ge=1, example=1)


class DateTriggerRequest(BaseModel):
    """Date触发器参数"""
    run_date: str = Field(..., description="执行日期时间 (ISO格式)", example="2024-12-31T23:59:59")


class ScheduledJobCreateRequest(BaseModel):
    """创建定时任务请求"""
    name: str = Field(..., description="任务名称", min_length=1, max_length=100, example="数据下载任务")
    job_id: str = Field(..., description="任务ID（唯一）", min_length=1, max_length=100, example="download_data")
    func_path: str = Field(..., description="任务函数路径，格式：module.path:function_name", example="utils.data:download_all_data")
    trigger_type: TriggerType = Field(..., description="触发器类型", example=TriggerType.CRON)
    description: Optional[str] = Field(None, description="任务描述", max_length=500, example="每周一至周五15:40执行数据下载")
    args: List[Any] = Field(default=[], description="位置参数列表", example=[])
    kwargs: Dict[str, Any] = Field(default={}, description="关键字参数字典", example={})
    
    # Cron触发器参数
    day_of_week: Optional[str] = Field(None, description="星期几 (Cron)", example="0-4")
    hour: Optional[int] = Field(None, description="小时 (Cron)", ge=0, le=23, example=15)
    minute: Optional[int] = Field(None, description="分钟 (Cron)", ge=0, le=59, example=40)
    second: Optional[int] = Field(0, description="秒 (Cron)", ge=0, le=59, example=0)
    
    # Interval触发器参数
    interval_seconds: Optional[int] = Field(None, description="间隔秒数", ge=1, example=60)
    interval_minutes: Optional[int] = Field(None, description="间隔分钟数", ge=1, example=5)
    interval_hours: Optional[int] = Field(None, description="间隔小时数", ge=1, example=1)
    interval_days: Optional[int] = Field(None, description="间隔天数", ge=1, example=1)
    
    # Date触发器参数
    run_date: Optional[str] = Field(None, description="执行日期时间 (ISO格式)", example="2024-12-31T23:59:59")


class ScheduledJobUpdateRequest(BaseModel):
    """更新定时任务请求"""
    name: Optional[str] = Field(None, description="任务名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="任务描述", max_length=500)
    args: Optional[List[Any]] = Field(None, description="位置参数列表")
    kwargs: Optional[Dict[str, Any]] = Field(None, description="关键字参数字典")
    
    # Cron触发器参数
    day_of_week: Optional[str] = Field(None, description="星期几 (Cron)")
    hour: Optional[int] = Field(None, description="小时 (Cron)", ge=0, le=23)
    minute: Optional[int] = Field(None, description="分钟 (Cron)", ge=0, le=59)
    second: Optional[int] = Field(None, description="秒 (Cron)", ge=0, le=59)
    
    # Interval触发器参数
    interval_seconds: Optional[int] = Field(None, description="间隔秒数", ge=1)
    interval_minutes: Optional[int] = Field(None, description="间隔分钟数", ge=1)
    interval_hours: Optional[int] = Field(None, description="间隔小时数", ge=1)
    interval_days: Optional[int] = Field(None, description="间隔天数", ge=1)
    
    # Date触发器参数
    run_date: Optional[str] = Field(None, description="执行日期时间 (ISO格式)")


class ScheduledJobResponse(BaseModel):
    """定时任务响应"""
    job_id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    func_path: str = Field(..., description="任务函数路径")
    trigger_type: TriggerType = Field(..., description="触发器类型")
    description: Optional[str] = Field(None, description="任务描述")
    args: List[Any] = Field(default=[], description="位置参数列表")
    kwargs: Dict[str, Any] = Field(default={}, description="关键字参数字典")
    status: JobStatus = Field(..., description="任务状态")
    is_active: bool = Field(..., description="是否激活")
    next_run_time: Optional[datetime] = Field(None, description="下次执行时间")
    last_run_time: Optional[datetime] = Field(None, description="上次执行时间")
    run_count: int = Field(..., description="执行次数")
    error_count: int = Field(..., description="错误次数")
    last_error: Optional[str] = Field(None, description="最后错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者ID")


class ScheduledJobListResponse(BaseModel):
    """定时任务列表响应"""
    jobs: List[ScheduledJobResponse] = Field(..., description="任务列表")
    pagination: Dict[str, Any] = Field(..., description="分页信息")


class JobControlRequest(BaseModel):
    """任务控制请求"""
    action: str = Field(..., description="操作类型: pause/resume/trigger", example="pause")


class JobControlResponse(BaseModel):
    """任务控制响应"""
    message: str = Field(..., description="操作结果消息")
    job_id: str = Field(..., description="任务ID")
    action: str = Field(..., description="执行的操作")


class SchedulerStatsResponse(BaseModel):
    """定时任务统计响应"""
    total: int = Field(..., description="总任务数")
    active: int = Field(..., description="激活任务数")
    paused: int = Field(..., description="暂停任务数")
    removed: int = Field(..., description="已删除任务数")
    by_trigger_type: Dict[str, int] = Field(..., description="按触发器类型统计")
    execution_stats: Dict[str, Any] = Field(..., description="执行统计信息")

