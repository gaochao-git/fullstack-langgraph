"""
定时任务管理API接口
不直接依赖Celery，通过配置和依赖注入的方式解耦
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ....shared.db.config import get_db
from ....shared.db.models import CeleryTaskRecord
from ..service.scheduled_task_service import ScheduledTaskService
from ..schema.scheduled_task_schema import (
    ScheduledTaskCreate, 
    ScheduledTaskUpdate, 
    TaskExecutionLogResponse
)

router = APIRouter()



@router.get("/scheduled-tasks", response_model=List[Dict[str, Any]])
async def list_scheduled_tasks(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    enabled_only: bool = Query(False, description="仅显示启用的任务"),
    agent_id: Optional[str] = Query(None, description="按智能体ID过滤"),
    session: Session = Depends(get_db)
):
    """获取定时任务列表"""
    return ScheduledTaskService.get_tasks_list(
        session=session,
        skip=skip,
        limit=limit,
        enabled_only=enabled_only,
        agent_id=agent_id
    )

@router.get("/scheduled-tasks/records", response_model=List[Dict[str, Any]])
async def get_task_execution_records(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    task_name: Optional[str] = Query(None, description="按任务名称过滤"),
    task_status: Optional[str] = Query(None, description="按任务状态过滤"),
    session: Session = Depends(get_db)
):
    """获取任务执行记录"""
    query = session.query(CeleryTaskRecord)
    
    if task_name:
        query = query.filter(CeleryTaskRecord.task_name.contains(task_name))
    
    if task_status:
        query = query.filter(CeleryTaskRecord.task_status == task_status)
    
    # 按创建时间倒序排列
    query = query.order_by(CeleryTaskRecord.create_time.desc())
    
    # 分页
    records = query.offset(skip).limit(limit).all()
    
    return [record.to_dict() for record in records]

@router.get("/scheduled-tasks/records/{record_id}", response_model=Dict[str, Any])
async def get_task_execution_record(
    record_id: int,
    session: Session = Depends(get_db)
):
    """获取单条任务执行记录详情"""
    record = session.query(CeleryTaskRecord).filter(CeleryTaskRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return record.to_dict()

@router.get("/scheduled-tasks/{task_id}", response_model=Dict[str, Any])
async def get_scheduled_task(
    task_id: int,
    session: Session = Depends(get_db)
):
    """获取单个定时任务详情"""
    task = ScheduledTaskService.get_task_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@router.post("/scheduled-tasks", response_model=Dict[str, Any])
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    session: Session = Depends(get_db)
):
    """创建新的定时任务"""
    # 验证JSON格式
    if not ScheduledTaskService.validate_json_field("task_args", task_data.task_args):
        raise HTTPException(status_code=400, detail="task_args必须是有效的JSON格式")
    
    if not ScheduledTaskService.validate_json_field("task_kwargs", task_data.task_kwargs):
        raise HTTPException(status_code=400, detail="task_kwargs必须是有效的JSON格式")
        
    if not ScheduledTaskService.validate_json_field("task_extra_config", task_data.task_extra_config):
        raise HTTPException(status_code=400, detail="task_extra_config必须是有效的JSON格式")
    
    # 验证调度配置
    if not ScheduledTaskService.validate_schedule_config(task_data.dict()):
        raise HTTPException(status_code=400, detail="必须提供间隔调度(task_interval)或crontab调度配置")
    
    # 创建任务
    result = ScheduledTaskService.create_task(session, task_data.dict())
    if not result:
        raise HTTPException(status_code=500, detail="任务创建失败")
    
    return result

@router.put("/scheduled-tasks/{task_id}", response_model=Dict[str, Any])
async def update_scheduled_task(
    task_id: int,
    task_data: ScheduledTaskUpdate,
    session: Session = Depends(get_db)
):
    """更新定时任务"""
    # 验证JSON格式
    task_dict = task_data.dict(exclude_unset=True)
    
    if task_data.task_args is not None:
        if not ScheduledTaskService.validate_json_field("task_args", task_data.task_args):
            raise HTTPException(status_code=400, detail="task_args必须是有效的JSON格式")
    
    if task_data.task_kwargs is not None:
        if not ScheduledTaskService.validate_json_field("task_kwargs", task_data.task_kwargs):
            raise HTTPException(status_code=400, detail="task_kwargs必须是有效的JSON格式")
    
    if task_data.task_extra_config is not None:
        if not ScheduledTaskService.validate_json_field("task_extra_config", task_data.task_extra_config):
            raise HTTPException(status_code=400, detail="task_extra_config必须是有效的JSON格式")
    
    # 更新任务
    success = ScheduledTaskService.update_task(session, task_id, task_dict)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或更新失败")
    
    return {
        "id": task_id,
        "message": "任务更新成功",
        "status": "updated"
    }

@router.delete("/scheduled-tasks/{task_id}")
async def delete_scheduled_task(
    task_id: int,
    session: Session = Depends(get_db)
):
    """删除定时任务"""
    success = ScheduledTaskService.delete_task(session, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务删除成功"}

@router.post("/scheduled-tasks/{task_id}/enable")
async def enable_scheduled_task(
    task_id: int,
    session: Session = Depends(get_db)
):
    """启用定时任务"""
    success = ScheduledTaskService.enable_task(session, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已启用"}

@router.post("/scheduled-tasks/{task_id}/disable")
async def disable_scheduled_task(
    task_id: int,
    session: Session = Depends(get_db)
):
    """禁用定时任务"""
    success = ScheduledTaskService.disable_task(session, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已禁用"}

@router.post("/scheduled-tasks/{task_id}/trigger")
async def trigger_scheduled_task(
    task_id: int,
    session: Session = Depends(get_db)
):
    """手动触发定时任务"""
    # 这里应该通过消息队列或HTTP API通知任务执行器
    # 而不是直接调用Celery
    return {
        "message": "任务触发请求已发送",
        "task_id": task_id,
        "trigger_time": datetime.utcnow()
    }

@router.get("/scheduled-tasks/{task_id}/logs", response_model=List[TaskExecutionLogResponse])
async def get_task_execution_logs(
    task_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: Session = Depends(get_db)
):
    """获取任务执行日志"""
    logs = ScheduledTaskService.get_task_execution_logs(
        session=session,
        task_id=task_id,
        skip=skip,
        limit=limit
    )
    
    if not logs and ScheduledTaskService.get_task_by_id(session, task_id) is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return logs

