"""
定时任务管理器
负责与APScheduler交互，管理定时任务的增删改查
"""
import importlib
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job

from modules.tornadoapp.model.scheduler_model import ScheduledJob, TriggerType, JobStatus

logger = logging.getLogger(__name__)


class SchedulerManager:
    """定时任务管理器"""
    
    def __init__(self, scheduler: BackgroundScheduler):
        """
        初始化调度器管理器
        
        Args:
            scheduler: APScheduler实例
        """
        self.scheduler = scheduler
    
    def _import_function(self, func_path: str) -> Callable:
        """
        动态导入函数
        
        Args:
            func_path: 函数路径，格式：module.path:function_name
        
        Returns:
            函数对象
        """
        try:
            module_path, func_name = func_path.split(":")
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            if not callable(func):
                raise ValueError(f"{func_path} 不是一个可调用对象")
            return func
        except Exception as e:
            logger.error(f"导入函数失败 {func_path}: {e}")
            raise
    
    def _create_trigger(self, job: ScheduledJob):
        """
        根据任务配置创建触发器
        
        Args:
            job: 定时任务模型
        
        Returns:
            触发器对象
        """
        if job.trigger_type == TriggerType.CRON:
            # Cron触发器
            trigger_kwargs = {}
            if job.day_of_week:
                trigger_kwargs['day_of_week'] = job.day_of_week
            if job.hour is not None:
                trigger_kwargs['hour'] = job.hour
            if job.minute is not None:
                trigger_kwargs['minute'] = job.minute
            if job.second is not None:
                trigger_kwargs['second'] = job.second
            return CronTrigger(**trigger_kwargs)
        
        elif job.trigger_type == TriggerType.INTERVAL:
            # 间隔触发器
            trigger_kwargs = {}
            if job.interval_seconds:
                trigger_kwargs['seconds'] = job.interval_seconds
            if job.interval_minutes:
                trigger_kwargs['minutes'] = job.interval_minutes
            if job.interval_hours:
                trigger_kwargs['hours'] = job.interval_hours
            if job.interval_days:
                trigger_kwargs['days'] = job.interval_days
            if not trigger_kwargs:
                raise ValueError("间隔触发器必须指定至少一个时间间隔参数")
            return IntervalTrigger(**trigger_kwargs)
        
        elif job.trigger_type == TriggerType.DATE:
            # 日期触发器
            if not job.run_date:
                raise ValueError("日期触发器必须指定run_date")
            return DateTrigger(run_date=job.run_date)
        
        else:
            raise ValueError(f"不支持的触发器类型: {job.trigger_type}")
    
    async def add_job(self, job: ScheduledJob) -> bool:
        """
        添加定时任务
        
        Args:
            job: 定时任务模型
        
        Returns:
            是否成功
        """
        try:
            # 导入函数
            func = self._import_function(job.func_path)
            
            # 创建触发器
            trigger = self._create_trigger(job)
            
            # 添加任务到调度器
            scheduler_job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job.job_id,
                args=job.args or [],
                kwargs=job.kwargs or {},
                replace_existing=True
            )
            
            # 更新任务的执行信息
            job.next_run_time = scheduler_job.next_run_time
            job.status = JobStatus.ACTIVE
            job.is_active = True
            await job.save()
            
            logger.info(f"定时任务已添加: {job.job_id}, 下次执行时间: {job.next_run_time}")
            return True
        
        except Exception as e:
            logger.error(f"添加定时任务失败 {job.job_id}: {e}")
            job.last_error = str(e)
            job.error_count = (job.error_count or 0) + 1
            await job.save()
            raise
    
    async def update_job(self, job: ScheduledJob) -> bool:
        """
        更新定时任务
        
        Args:
            job: 定时任务模型
        
        Returns:
            是否成功
        """
        try:
            # 先移除旧任务
            await self.remove_job(job.job_id)
            
            # 重新添加任务
            return await self.add_job(job)
        
        except Exception as e:
            logger.error(f"更新定时任务失败 {job.job_id}: {e}")
            raise
    
    async def remove_job(self, job_id: str) -> bool:
        """
        移除定时任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"定时任务已移除: {job_id}")
            
            # 更新数据库中的任务状态
            job = await ScheduledJob.find_one(ScheduledJob.job_id == job_id)
            if job:
                job.status = JobStatus.REMOVED
                job.is_active = False
                await job.save()
            
            return True
        
        except Exception as e:
            logger.error(f"移除定时任务失败 {job_id}: {e}")
            raise
    
    async def pause_job(self, job_id: str) -> bool:
        """
        暂停定时任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            scheduler_job = self.scheduler.get_job(job_id)
            if scheduler_job:
                self.scheduler.pause_job(job_id)
                logger.info(f"定时任务已暂停: {job_id}")
            
            # 更新数据库
            job = await ScheduledJob.find_one(ScheduledJob.job_id == job_id)
            if job:
                job.status = JobStatus.PAUSED
                await job.save()
            
            return True
        
        except Exception as e:
            logger.error(f"暂停定时任务失败 {job_id}: {e}")
            raise
    
    async def resume_job(self, job_id: str) -> bool:
        """
        恢复定时任务
        
        Args:
            job_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            scheduler_job = self.scheduler.get_job(job_id)
            if scheduler_job:
                self.scheduler.resume_job(job_id)
                logger.info(f"定时任务已恢复: {job_id}")
            else:
                # 如果调度器中没有，从数据库恢复
                job = await ScheduledJob.find_one(ScheduledJob.job_id == job_id)
                if job and job.is_active:
                    await self.add_job(job)
            
            # 更新数据库
            job = await ScheduledJob.find_one(ScheduledJob.job_id == job_id)
            if job:
                job.status = JobStatus.ACTIVE
                job.next_run_time = self.scheduler.get_job(job_id).next_run_time if self.scheduler.get_job(job_id) else None
                await job.save()
            
            return True
        
        except Exception as e:
            logger.error(f"恢复定时任务失败 {job_id}: {e}")
            raise
    
    async def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            job_id: 任务ID
        
        Returns:
            任务信息字典
        """
        try:
            # 从数据库获取
            job = await ScheduledJob.find_one(ScheduledJob.job_id == job_id)
            if not job:
                return None
            
            # 从调度器获取实时信息
            scheduler_job = self.scheduler.get_job(job_id)
            
            info = {
                "id": str(job.id),
                "name": job.name,
                "job_id": job.job_id,
                "func_path": job.func_path,
                "trigger_type": job.trigger_type,
                "status": job.status,
                "is_active": job.is_active,
                "args": job.args,
                "kwargs": job.kwargs,
                "description": job.description,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "run_count": job.run_count,
                "error_count": job.error_count,
                "last_error": job.last_error,
            }
            
            # 添加触发器相关信息
            if job.trigger_type == TriggerType.CRON:
                info["trigger"] = {
                    "day_of_week": job.day_of_week,
                    "hour": job.hour,
                    "minute": job.minute,
                    "second": job.second,
                }
            elif job.trigger_type == TriggerType.INTERVAL:
                info["trigger"] = {
                    "seconds": job.interval_seconds,
                    "minutes": job.interval_minutes,
                    "hours": job.interval_hours,
                    "days": job.interval_days,
                }
            elif job.trigger_type == TriggerType.DATE:
                info["trigger"] = {
                    "run_date": job.run_date.isoformat() if job.run_date else None,
                }
            
            # 添加调度器实时信息
            if scheduler_job:
                info["next_run_time"] = scheduler_job.next_run_time.isoformat() if scheduler_job.next_run_time else None
                info["scheduler_status"] = "scheduled"
            else:
                info["next_run_time"] = job.next_run_time.isoformat() if job.next_run_time else None
                info["scheduler_status"] = "not_scheduled"
            
            info["last_run_time"] = job.last_run_time.isoformat() if job.last_run_time else None
            
            return info
        
        except Exception as e:
            logger.error(f"获取任务信息失败 {job_id}: {e}")
            raise
    
    async def list_jobs(self, status: Optional[str] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        列出所有定时任务
        
        Args:
            status: 状态过滤
            is_active: 是否激活过滤
        
        Returns:
            任务信息列表
        """
        try:
            # 构建查询条件
            query = {}
            if status:
                query["status"] = status
            if is_active is not None:
                query["is_active"] = is_active
            
            # 从数据库获取
            jobs = await ScheduledJob.find(query).to_list()
            
            # 获取每个任务的详细信息
            job_list = []
            for job in jobs:
                info = await self.get_job_info(job.job_id)
                if info:
                    job_list.append(info)
            
            return job_list
        
        except Exception as e:
            logger.error(f"列出定时任务失败: {e}")
            raise
    
    async def trigger_job(self, job_id: str) -> bool:
        """
        立即触发任务执行
        
        Args:
            job_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            scheduler_job = self.scheduler.get_job(job_id)
            if scheduler_job:
                scheduler_job.modify(next_run_time=datetime.now())
                logger.info(f"定时任务已触发: {job_id}")
                return True
            else:
                # 如果调度器中没有，尝试从数据库恢复
                job = await ScheduledJob.find_one(ScheduledJob.job_id == job_id)
                if job:
                    await self.add_job(job)
                    scheduler_job = self.scheduler.get_job(job_id)
                    if scheduler_job:
                        scheduler_job.modify(next_run_time=datetime.now())
                        return True
                raise ValueError(f"任务不存在: {job_id}")
        
        except Exception as e:
            logger.error(f"触发定时任务失败 {job_id}: {e}")
            raise

