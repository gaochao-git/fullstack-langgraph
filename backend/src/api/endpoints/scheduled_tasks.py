"""
定时任务管理API接口
"""

import json
import sys
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 添加celery_task到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../celery_task'))

try:
    from celery_app.models import get_session, PeriodicTask, Task, PeriodicTaskRun
    from celery_app.celery import app as celery_app
except ImportError as e:
    print(f"Warning: Could not import Celery modules: {e}")
    # 创建占位符类以避免运行时错误
    class PeriodicTask:
        pass
    class Task:
        pass
    class PeriodicTaskRun:
        pass
    
    def get_session():
        return None
    
    celery_app = None

router = APIRouter()

# Pydantic 模型
class ScheduledTaskCreate(BaseModel):
    task_name: str = Field(..., description="任务名称")
    task_path: str = Field(..., description="任务路径，如 'celery_app.tasks.example_task'")
    task_description: Optional[str] = Field(None, description="任务描述")
    task_extra_config: Optional[str] = Field(None, description="任务配置JSON字符串（包含task_type、agent_id、task_timeout等）")
    task_interval: Optional[int] = Field(None, description="间隔秒数（用于间隔调度）")
    task_crontab_minute: Optional[str] = Field(None, description="Crontab分钟")
    task_crontab_hour: Optional[str] = Field(None, description="Crontab小时")
    task_crontab_day_of_week: Optional[str] = Field(None, description="Crontab星期")
    task_crontab_day_of_month: Optional[str] = Field(None, description="Crontab日期")
    task_crontab_month_of_year: Optional[str] = Field(None, description="Crontab月份")
    task_args: Optional[str] = Field(None, description="任务参数（JSON格式）")
    task_kwargs: Optional[str] = Field(None, description="任务关键字参数（JSON格式）")
    task_enabled: bool = Field(True, description="是否启用任务")

class ScheduledTaskUpdate(BaseModel):
    task_name: Optional[str] = None
    task_path: Optional[str] = None
    task_description: Optional[str] = None
    task_extra_config: Optional[str] = None
    task_interval: Optional[int] = None
    task_crontab_minute: Optional[str] = None
    task_crontab_hour: Optional[str] = None
    task_crontab_day_of_week: Optional[str] = None
    task_crontab_day_of_month: Optional[str] = None
    task_crontab_month_of_year: Optional[str] = None
    task_args: Optional[str] = None
    task_kwargs: Optional[str] = None
    task_enabled: Optional[bool] = None

class ScheduledTaskResponse(BaseModel):
    id: int
    task_name: str
    task_path: str
    task_description: Optional[str]
    task_extra_config: Optional[str]
    task_interval: Optional[int]
    task_crontab_minute: Optional[str]
    task_crontab_hour: Optional[str]
    task_crontab_day_of_week: Optional[str]
    task_crontab_day_of_month: Optional[str]
    task_crontab_month_of_year: Optional[str]
    task_args: Optional[str]
    task_kwargs: Optional[str]
    task_enabled: bool
    task_last_run_time: Optional[datetime]
    task_run_count: int
    create_time: datetime
    update_time: datetime
    create_by: Optional[str]
    update_by: Optional[str]

class TaskExecutionLogResponse(BaseModel):
    id: int
    task_name: str
    task_schedule_time: datetime
    task_execute_time: datetime
    task_status: str
    task_result: Optional[str]
    create_time: datetime

class CeleryTaskResponse(BaseModel):
    id: int
    task_id: str
    task_name: str
    task_status: str
    create_time: datetime
    task_start_time: Optional[datetime]
    task_complete_time: Optional[datetime]
    task_result: Optional[str]
    task_traceback: Optional[str]
    task_retry_count: int

def get_db_session():
    """获取数据库会话"""
    if get_session is None:
        raise HTTPException(status_code=503, detail="数据库连接不可用")
    return get_session()

@router.get("/scheduled-tasks", response_model=List[ScheduledTaskResponse])
async def list_scheduled_tasks(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    enabled_only: bool = Query(False, description="仅显示启用的任务"),
    agent_id: Optional[str] = Query(None, description="按智能体ID过滤")
):
    """获取定时任务列表"""
    session = get_db_session()
    try:
        query = session.query(PeriodicTask)
        if enabled_only:
            query = query.filter(PeriodicTask.task_enabled == True)
            
        # 按智能体ID过滤（需要解析task_extra_config中的agent_id）
        if agent_id:
            # 使用MySQL的JSON_EXTRACT函数来查询JSON字段
            query = query.filter(PeriodicTask.task_extra_config.like(f'%"agent_id": "{agent_id}"%'))
        
        tasks = query.offset(skip).limit(limit).all()
        return [ScheduledTaskResponse(**task.__dict__) for task in tasks]
    finally:
        session.close()

@router.get("/scheduled-tasks/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(task_id: int):
    """获取单个定时任务详情"""
    session = get_db_session()
    try:
        task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return ScheduledTaskResponse(**task.__dict__)
    finally:
        session.close()

@router.post("/scheduled-tasks", response_model=ScheduledTaskResponse)
async def create_scheduled_task(task_data: ScheduledTaskCreate):
    """创建新的定时任务"""
    session = get_db_session()
    try:
        # 检查任务名称是否已存在
        existing = session.query(PeriodicTask).filter(PeriodicTask.task_name == task_data.task_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="任务名称已存在")
        
        # 验证JSON格式
        if task_data.task_args:
            try:
                json.loads(task_data.task_args)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="task_args必须是有效的JSON格式")
        
        if task_data.task_kwargs:
            try:
                json.loads(task_data.task_kwargs)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="task_kwargs必须是有效的JSON格式")
        
        # 验证调度配置
        if not task_data.task_interval and not any([
            task_data.task_crontab_minute,
            task_data.task_crontab_hour,
            task_data.task_crontab_day_of_week,
            task_data.task_crontab_day_of_month,
            task_data.task_crontab_month_of_year
        ]):
            raise HTTPException(status_code=400, detail="必须提供间隔调度(task_interval)或crontab调度配置")
        
        new_task = PeriodicTask(**task_data.dict())
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        
        return ScheduledTaskResponse(**new_task.__dict__)
    finally:
        session.close()

@router.put("/scheduled-tasks/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(task_id: int, task_data: ScheduledTaskUpdate):
    """更新定时任务"""
    session = get_db_session()
    try:
        task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 验证JSON格式
        if task_data.task_args is not None:
            try:
                json.loads(task_data.task_args)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="task_args必须是有效的JSON格式")
        
        if task_data.task_kwargs is not None:
            try:
                json.loads(task_data.task_kwargs)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="task_kwargs必须是有效的JSON格式")
        
        # 更新字段
        for field, value in task_data.dict(exclude_unset=True).items():
            setattr(task, field, value)
        
        task.update_time = datetime.now()
        session.commit()
        session.refresh(task)
        
        return ScheduledTaskResponse(**task.__dict__)
    finally:
        session.close()

@router.delete("/scheduled-tasks/{task_id}")
async def delete_scheduled_task(task_id: int):
    """删除定时任务"""
    session = get_db_session()
    try:
        task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        session.delete(task)
        session.commit()
        
        return {"message": "任务删除成功"}
    finally:
        session.close()

@router.post("/scheduled-tasks/{task_id}/enable")
async def enable_scheduled_task(task_id: int):
    """启用定时任务"""
    session = get_db_session()
    try:
        task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task.task_enabled = True
        task.update_time = datetime.now()
        session.commit()
        
        return {"message": "任务已启用"}
    finally:
        session.close()

@router.post("/scheduled-tasks/{task_id}/disable")
async def disable_scheduled_task(task_id: int):
    """禁用定时任务"""
    session = get_db_session()
    try:
        task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task.task_enabled = False
        task.update_time = datetime.now()
        session.commit()
        
        return {"message": "任务已禁用"}
    finally:
        session.close()

@router.post("/scheduled-tasks/{task_id}/run-now")
async def run_scheduled_task_now(task_id: int):
    """立即执行定时任务"""
    if celery_app is None:
        raise HTTPException(status_code=503, detail="Celery应用不可用")
    
    session = get_db_session()
    try:
        task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 解析参数
        args = json.loads(task.task_args) if task.task_args else []
        kwargs = json.loads(task.task_kwargs) if task.task_kwargs else {}
        
        # 发送任务到Celery
        result = celery_app.send_task(task.task_path, args=args, kwargs=kwargs)
        
        return {
            "message": "任务已发送执行",
            "task_id": result.id,
            "task_name": task.task_name
        }
    finally:
        session.close()

@router.get("/scheduled-tasks/{task_id}/execution-logs", response_model=List[TaskExecutionLogResponse])
async def get_task_execution_logs(
    task_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000)
):
    """获取任务执行日志"""
    session = get_db_session()
    try:
        task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        logs = (session.query(PeriodicTaskRun)
                .filter(PeriodicTaskRun.task_name == task.task_name)
                .order_by(PeriodicTaskRun.task_execute_time.desc())
                .offset(skip)
                .limit(limit)
                .all())
        
        return [TaskExecutionLogResponse(**log.__dict__) for log in logs]
    finally:
        session.close()

@router.get("/celery-tasks", response_model=List[CeleryTaskResponse])
async def list_celery_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    status: Optional[str] = Query(None, description="按状态过滤")
):
    """获取Celery任务执行记录"""
    session = get_db_session()
    try:
        query = session.query(Task).order_by(Task.create_time.desc())
        
        if status:
            query = query.filter(Task.task_status == status)
        
        tasks = query.offset(skip).limit(limit).all()
        return [CeleryTaskResponse(**task.__dict__) for task in tasks]
    finally:
        session.close()

@router.get("/celery-tasks/{task_id}", response_model=CeleryTaskResponse)
async def get_celery_task(task_id: str):
    """获取单个Celery任务详情"""
    session = get_db_session()
    try:
        task = session.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return CeleryTaskResponse(**task.__dict__)
    finally:
        session.close()

@router.get("/celery-status")
async def get_celery_status():
    """获取Celery服务状态"""
    if celery_app is None:
        return {"status": "unavailable", "message": "Celery应用不可用"}
    
    try:
        # 检查worker状态
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        
        worker_count = len(stats) if stats else 0
        active_task_count = sum(len(tasks) for tasks in active.values()) if active else 0
        
        return {
            "status": "running" if worker_count > 0 else "no_workers",
            "worker_count": worker_count,
            "active_task_count": active_task_count,
            "workers": list(stats.keys()) if stats else []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"无法获取Celery状态: {str(e)}"
        }

@router.post("/refresh-schedule")
async def refresh_schedule():
    """手动刷新定时任务调度配置"""
    if celery_app is None:
        raise HTTPException(status_code=503, detail="Celery应用不可用")
    
    try:
        # 发送刷新调度的任务
        result = celery_app.send_task('celery_app.dynamic_scheduler.refresh_periodic_tasks_schedule')
        
        # 等待任务完成（最多等待10秒）
        task_result = result.get(timeout=10)
        
        return {
            "message": "调度配置刷新成功",
            "task_id": result.id,
            "result": task_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新调度配置失败: {str(e)}")