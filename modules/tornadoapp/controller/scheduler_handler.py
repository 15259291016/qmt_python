"""
定时任务API处理器
提供定时任务的增删改查、暂停恢复、立即触发等操作
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from tornado.web import RequestHandler

from modules.tornadoapp.model.scheduler_model import ScheduledJob, TriggerType, JobStatus
from modules.tornadoapp.scheduler.scheduler_manager import SchedulerManager
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
    """定时任务处理器"""
    
    @try_except_async_request
    @require_permission("system:read")
    async def get(self, job_id: Optional[str] = None):
        """获取任务列表或单个任务详情"""
        manager = get_scheduler_manager()
        
        if job_id:
            # 获取单个任务
            job_info = await manager.get_job_info(job_id)
            if not job_info:
                return FailedResponse(msg="任务不存在")
            return job_info
        else:
            # 获取任务列表
            status = self.get_argument("status", None)
            is_active = self.get_argument("is_active", None)
            if is_active is not None:
                is_active = is_active.lower() == "true"
            
            page = int(self.get_argument("page", 1))
            limit = int(self.get_argument("limit", 20))
            
            # 获取所有任务
            jobs = await manager.list_jobs(status=status, is_active=is_active)
            
            # 分页
            total = len(jobs)
            start = (page - 1) * limit
            end = start + limit
            paginated_jobs = jobs[start:end]
            
            return {
                "jobs": paginated_jobs,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if limit > 0 else 0
                }
            }
    
    @try_except_async_request
    @require_permission("system:write")
    async def post(self):
        """创建定时任务"""
        try:
            data = json.loads(self.request.body)
            
            # 验证必填字段
            required_fields = ["name", "job_id", "func_path", "trigger_type"]
            for field in required_fields:
                if field not in data:
                    return FailedResponse(msg=f"缺少必填字段: {field}")
            
            # 检查job_id是否已存在
            existing_job = await ScheduledJob.find_one(ScheduledJob.job_id == data["job_id"])
            if existing_job:
                return FailedResponse(msg=f"任务ID已存在: {data['job_id']}")
            
            # 创建任务模型
            job = ScheduledJob(
                name=data["name"],
                job_id=data["job_id"],
                func_path=data["func_path"],
                trigger_type=TriggerType(data["trigger_type"]),
                description=data.get("description"),
                args=data.get("args", []),
                kwargs=data.get("kwargs", {}),
                created_by=self.current_user_id if hasattr(self, 'current_user_id') else None
            )
            
            # 根据触发器类型设置参数
            if job.trigger_type == TriggerType.CRON:
                job.day_of_week = data.get("day_of_week")
                job.hour = data.get("hour")
                job.minute = data.get("minute")
                job.second = data.get("second", 0)
            elif job.trigger_type == TriggerType.INTERVAL:
                job.interval_seconds = data.get("interval_seconds")
                job.interval_minutes = data.get("interval_minutes")
                job.interval_hours = data.get("interval_hours")
                job.interval_days = data.get("interval_days")
            elif job.trigger_type == TriggerType.DATE:
                run_date_str = data.get("run_date")
                if run_date_str:
                    job.run_date = datetime.fromisoformat(run_date_str.replace('Z', '+00:00'))
            
            # 保存到数据库
            await job.save()
            
            # 添加到调度器
            manager = get_scheduler_manager()
            await manager.add_job(job)
            
            # 返回任务信息
            job_info = await manager.get_job_info(job.job_id)
            return job_info
        
        except ValueError as e:
            return FailedResponse(msg=f"参数错误: {str(e)}")
        except Exception as e:
            logger.error(f"创建定时任务失败: {e}", exc_info=True)
            return FailedResponse(msg=f"创建定时任务失败: {str(e)}")
    
    @try_except_async_request
    @require_permission("system:write")
    async def put(self, job_id: str):
        """更新定时任务"""
        try:
            data = json.loads(self.request.body)
            
            # 获取任务
            job = await ScheduledJob.find_one(ScheduledJob.job_id == job_id)
            if not job:
                return FailedResponse(msg="任务不存在")
            
            # 更新字段
            if "name" in data:
                job.name = data["name"]
            if "description" in data:
                job.description = data["description"]
            if "args" in data:
                job.args = data["args"]
            if "kwargs" in data:
                job.kwargs = data["kwargs"]
            
            # 更新触发器参数
            if job.trigger_type == TriggerType.CRON:
                if "day_of_week" in data:
                    job.day_of_week = data["day_of_week"]
                if "hour" in data:
                    job.hour = data["hour"]
                if "minute" in data:
                    job.minute = data["minute"]
                if "second" in data:
                    job.second = data["second"]
            elif job.trigger_type == TriggerType.INTERVAL:
                if "interval_seconds" in data:
                    job.interval_seconds = data["interval_seconds"]
                if "interval_minutes" in data:
                    job.interval_minutes = data["interval_minutes"]
                if "interval_hours" in data:
                    job.interval_hours = data["interval_hours"]
                if "interval_days" in data:
                    job.interval_days = data["interval_days"]
            elif job.trigger_type == TriggerType.DATE:
                if "run_date" in data:
                    run_date_str = data["run_date"]
                    job.run_date = datetime.fromisoformat(run_date_str.replace('Z', '+00:00'))
            
            job.updated_at = datetime.utcnow()
            
            # 保存到数据库
            await job.save()
            
            # 更新调度器中的任务
            manager = get_scheduler_manager()
            await manager.update_job(job)
            
            # 返回任务信息
            job_info = await manager.get_job_info(job.job_id)
            return job_info
        
        except ValueError as e:
            return FailedResponse(msg=f"参数错误: {str(e)}")
        except Exception as e:
            logger.error(f"更新定时任务失败: {e}", exc_info=True)
            return FailedResponse(msg=f"更新定时任务失败: {str(e)}")
    
    @try_except_async_request
    @require_permission("system:write")
    async def delete(self, job_id: str):
        """删除定时任务"""
        try:
            manager = get_scheduler_manager()
            await manager.remove_job(job_id)
            return {"message": "任务已删除", "job_id": job_id}
        
        except Exception as e:
            logger.error(f"删除定时任务失败: {e}", exc_info=True)
            return FailedResponse(msg=f"删除定时任务失败: {str(e)}")


class SchedulerJobControlHandler(BaseHandler, PermissionMixin):
    """定时任务控制处理器（暂停、恢复、触发）"""
    
    @try_except_async_request
    @require_permission("system:write")
    async def post(self, job_id: str, action: str):
        """执行任务控制操作"""
        try:
            manager = get_scheduler_manager()
            
            if action == "pause":
                await manager.pause_job(job_id)
                return {"message": "任务已暂停", "job_id": job_id, "action": "pause"}
            
            elif action == "resume":
                await manager.resume_job(job_id)
                return {"message": "任务已恢复", "job_id": job_id, "action": "resume"}
            
            elif action == "trigger":
                await manager.trigger_job(job_id)
                return {"message": "任务已触发", "job_id": job_id, "action": "trigger"}
            
            else:
                return FailedResponse(msg=f"不支持的操作: {action}")
        
        except Exception as e:
            logger.error(f"执行任务操作失败: {e}", exc_info=True)
            return FailedResponse(msg=f"执行任务操作失败: {str(e)}")


class SchedulerStatsHandler(BaseHandler, PermissionMixin):
    """定时任务统计处理器"""
    
    @try_except_async_request
    @require_permission("system:read")
    async def get(self):
        """获取定时任务统计信息"""
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
            
            return {
                "total": total,
                "active": active,
                "paused": paused,
                "removed": removed,
                "by_trigger_type": {
                    "cron": cron_count,
                    "interval": interval_count,
                    "date": date_count
                },
                "execution_stats": {
                    "total_runs": total_runs,
                    "total_errors": total_errors,
                    "error_rate": total_errors / total_runs if total_runs > 0 else 0
                }
            }
        
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}", exc_info=True)
            return FailedResponse(msg=f"获取统计信息失败: {str(e)}")

