"""
定时任务API处理器（Pydantic版本）
使用类型注解自动生成Swagger文档
"""
import logging
from typing import Optional, Union
from datetime import datetime

from modules.tornadoapp.model.scheduler_model import ScheduledJob, TriggerType, JobStatus
from modules.tornadoapp.scheduler.scheduler_manager import SchedulerManager
from modules.tornadoapp.schemas.scheduler_schemas import (
    ScheduledJobCreateRequest,
    ScheduledJobUpdateRequest,
    ScheduledJobResponse,
    ScheduledJobListResponse,
    JobControlRequest,
    JobControlResponse,
    SchedulerStatsResponse
)
from modules.tornadoapp.utils.permission_decorator import (
    require_permission, PermissionMixin
)
from modules.tornadoapp.utils.response_model import try_except_async_request, FailedResponse
from modules.tornadoapp.define.base.handler import BaseHandler

logger = logging.getLogger(__name__)


def get_scheduler_manager() -> SchedulerManager:
    """获取调度器管理器实例"""
    from main import scheduler
    return SchedulerManager(scheduler)


class SchedulerJobHandler(BaseHandler, PermissionMixin):
    """定时任务处理器 - 使用Pydantic自动生成文档"""
    
    @try_except_async_request
    @require_permission("system:read")
    async def get(
        self,
        job_id: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 20
    ) -> Union[ScheduledJobResponse, ScheduledJobListResponse]:
        """
        获取任务列表或单个任务详情
        
        Args:
            job_id: 任务ID（可选，不传则返回列表）
            status: 任务状态筛选
            is_active: 是否激活筛选
            page: 页码
            limit: 每页数量
        """
        manager = get_scheduler_manager()
        
        if job_id:
            # 获取单个任务
            job_info = await manager.get_job_info(job_id)
            if not job_info:
                return FailedResponse(msg="任务不存在")
            return ScheduledJobResponse(**job_info)
        else:
            # 获取任务列表
            jobs = await manager.list_jobs(status=status, is_active=is_active)
            
            # 分页
            total = len(jobs)
            start = (page - 1) * limit
            end = start + limit
            paginated_jobs = [ScheduledJobResponse(**job) for job in jobs[start:end]]
            
            return ScheduledJobListResponse(
                jobs=paginated_jobs,
                pagination={
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if limit > 0 else 0
                }
            )
    
    @try_except_async_request
    @require_permission("system:write")
    async def post(self) -> ScheduledJobResponse:
        """
        创建定时任务
        
        请求体自动解析为ScheduledJobCreateRequest
        """
        try:
            # 从请求体解析Pydantic模型
            request = self.parse_pydantic_model(ScheduledJobCreateRequest)
            # 检查job_id是否已存在
            existing_job = await ScheduledJob.find_one(ScheduledJob.job_id == request.job_id)
            if existing_job:
                return FailedResponse(msg=f"任务ID已存在: {request.job_id}")
            
            # 创建任务模型
            job = ScheduledJob(
                name=request.name,
                job_id=request.job_id,
                func_path=request.func_path,
                trigger_type=request.trigger_type,
                description=request.description,
                args=request.args,
                kwargs=request.kwargs,
                created_by=self.current_user_id if hasattr(self, 'current_user_id') else None
            )
            
            # 根据触发器类型设置参数
            if job.trigger_type == TriggerType.CRON:
                job.day_of_week = request.day_of_week
                job.hour = request.hour
                job.minute = request.minute
                job.second = request.second
            elif job.trigger_type == TriggerType.INTERVAL:
                job.interval_seconds = request.interval_seconds
                job.interval_minutes = request.interval_minutes
                job.interval_hours = request.interval_hours
                job.interval_days = request.interval_days
            elif job.trigger_type == TriggerType.DATE:
                if request.run_date:
                    try:
                        # 处理ISO格式日期，支持Z和+00:00时区
                        date_str = request.run_date.replace('Z', '+00:00')
                        job.run_date = datetime.fromisoformat(date_str)
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"日期格式解析失败: {request.run_date}, 错误: {e}")
                        raise ValueError(f"日期格式错误: {request.run_date}，请使用ISO格式（如：2024-12-31T23:59:59）")
            
            # 保存到数据库
            await job.save()
            
            # 添加到调度器
            manager = get_scheduler_manager()
            await manager.add_job(job)
            
            # 返回任务信息
            job_info = await manager.get_job_info(job.job_id)
            return ScheduledJobResponse(**job_info)
        
        except ValueError as e:
            logger.warning(f"创建定时任务参数错误: {e}")
            return FailedResponse(msg=f"参数错误: {str(e)}")
        except KeyError as e:
            logger.warning(f"创建定时任务缺少必要字段: {e}")
            return FailedResponse(msg=f"缺少必要字段: {str(e)}")
        except Exception as e:
            logger.error(f"创建定时任务失败: {e}", exc_info=True)
            return FailedResponse(msg=f"创建定时任务失败: {str(e)}")
    
    @try_except_async_request
    @require_permission("system:write")
    async def put(self, job_id: str) -> ScheduledJobResponse:
        """
        更新定时任务
        
        Args:
            job_id: 任务ID（路径参数）
        
        请求体自动解析为ScheduledJobUpdateRequest
        """
        try:
            # 从请求体解析Pydantic模型
            request = self.parse_pydantic_model(ScheduledJobUpdateRequest)
            # 获取任务
            job = await ScheduledJob.find_one(ScheduledJob.job_id == job_id)
            if not job:
                return FailedResponse(msg="任务不存在")
            
            # 更新字段
            if request.name is not None:
                job.name = request.name
            if request.description is not None:
                job.description = request.description
            if request.args is not None:
                job.args = request.args
            if request.kwargs is not None:
                job.kwargs = request.kwargs
            
            # 更新触发器参数
            if job.trigger_type == TriggerType.CRON:
                if request.day_of_week is not None:
                    job.day_of_week = request.day_of_week
                if request.hour is not None:
                    job.hour = request.hour
                if request.minute is not None:
                    job.minute = request.minute
                if request.second is not None:
                    job.second = request.second
            elif job.trigger_type == TriggerType.INTERVAL:
                if request.interval_seconds is not None:
                    job.interval_seconds = request.interval_seconds
                if request.interval_minutes is not None:
                    job.interval_minutes = request.interval_minutes
                if request.interval_hours is not None:
                    job.interval_hours = request.interval_hours
                if request.interval_days is not None:
                    job.interval_days = request.interval_days
            elif job.trigger_type == TriggerType.DATE:
                if request.run_date is not None:
                    try:
                        # 处理ISO格式日期，支持Z和+00:00时区
                        date_str = request.run_date.replace('Z', '+00:00')
                        job.run_date = datetime.fromisoformat(date_str)
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"日期格式解析失败: {request.run_date}, 错误: {e}")
                        raise ValueError(f"日期格式错误: {request.run_date}，请使用ISO格式（如：2024-12-31T23:59:59）")
            
            job.updated_at = datetime.utcnow()
            
            # 保存到数据库
            await job.save()
            
            # 更新调度器中的任务
            manager = get_scheduler_manager()
            await manager.update_job(job)
            
            # 返回任务信息
            job_info = await manager.get_job_info(job.job_id)
            return ScheduledJobResponse(**job_info)
        
        except ValueError as e:
            logger.warning(f"更新定时任务参数错误: {e}")
            return FailedResponse(msg=f"参数错误: {str(e)}")
        except Exception as e:
            logger.error(f"更新定时任务失败: {e}", exc_info=True)
            return FailedResponse(msg=f"更新定时任务失败: {str(e)}")
    
    @try_except_async_request
    @require_permission("system:write")
    async def delete(self, job_id: str) -> dict:
        """
        删除定时任务
        
        Args:
            job_id: 任务ID
        """
        try:
            manager = get_scheduler_manager()
            await manager.remove_job(job_id)
            return {"message": "任务已删除", "job_id": job_id}
        
        except KeyError as e:
            logger.warning(f"删除定时任务，任务不存在: {e}")
            return FailedResponse(msg="任务不存在")
        except Exception as e:
            logger.error(f"删除定时任务失败: {e}", exc_info=True)
            return FailedResponse(msg=f"删除定时任务失败: {str(e)}")


class SchedulerJobControlHandler(BaseHandler, PermissionMixin):
    """定时任务控制处理器（暂停、恢复、触发）"""
    
    @try_except_async_request
    @require_permission("system:write")
    async def post(self, job_id: str, action: str) -> JobControlResponse:
        """
        执行任务控制操作
        
        Args:
            job_id: 任务ID（路径参数）
            action: 操作类型（路径参数: pause/resume/trigger）
        """
        try:
            # 从路径参数构建请求
            request = JobControlRequest(action=action)
            manager = get_scheduler_manager()
            
            if request.action == "pause":
                await manager.pause_job(job_id)
                return JobControlResponse(
                    message="任务已暂停",
                    job_id=job_id,
                    action="pause"
                )
            
            elif request.action == "resume":
                await manager.resume_job(job_id)
                return JobControlResponse(
                    message="任务已恢复",
                    job_id=job_id,
                    action="resume"
                )
            
            elif request.action == "trigger":
                await manager.trigger_job(job_id)
                return JobControlResponse(
                    message="任务已触发",
                    job_id=job_id,
                    action="trigger"
                )
            
            else:
                return FailedResponse(msg=f"不支持的操作: {request.action}")
        
        except KeyError as e:
            logger.warning(f"执行任务操作，任务不存在: {e}")
            return FailedResponse(msg="任务不存在")
        except ValueError as e:
            logger.warning(f"执行任务操作参数错误: {e}")
            return FailedResponse(msg=f"参数错误: {str(e)}")
        except Exception as e:
            logger.error(f"执行任务操作失败: {e}", exc_info=True)
            return FailedResponse(msg=f"执行任务操作失败: {str(e)}")


class SchedulerStatsHandler(BaseHandler, PermissionMixin):
    """定时任务统计处理器"""
    
    @try_except_async_request
    @require_permission("system:read")
    async def get(self) -> SchedulerStatsResponse:
        """
        获取定时任务统计信息
        """
        try:
            # 获取所有任务
            all_jobs = await ScheduledJob.find().to_list()
            
            # 统计
            total = len(all_jobs)
            active = len([j for j in all_jobs if j.status == JobStatus.ACTIVE])
            paused = len([j for j in all_jobs if j.status == JobStatus.PAUSED])
            removed = len([j for j in all_jobs if j.status == JobStatus.REMOVED])
            
            # 按触发器类型统计
            cron_count = len([j for j in all_jobs if j.trigger_type == TriggerType.CRON])
            interval_count = len([j for j in all_jobs if j.trigger_type == TriggerType.INTERVAL])
            date_count = len([j for j in all_jobs if j.trigger_type == TriggerType.DATE])
            
            # 总执行次数和错误次数
            total_runs = sum(j.run_count or 0 for j in all_jobs)
            total_errors = sum(j.error_count or 0 for j in all_jobs)
            
            return SchedulerStatsResponse(
                total=total,
                active=active,
                paused=paused,
                removed=removed,
                by_trigger_type={
                    "cron": cron_count,
                    "interval": interval_count,
                    "date": date_count
                },
                execution_stats={
                    "total_runs": total_runs,
                    "total_errors": total_errors,
                    "error_rate": total_errors / total_runs if total_runs > 0 else 0
                }
            )
        
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}", exc_info=True)
            return FailedResponse(msg=f"获取统计信息失败: {str(e)}")

