"""定时任务管理路由 - 使用统一响应格式"""

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json
from src.shared.db.models import now_shanghai

from src.shared.db.config import get_async_db
from src.apps.scheduled_task.schema import (
    ScheduledTaskCreate, ScheduledTaskUpdate, ScheduledTaskQueryParams,
    TaskExecutionLogResponse, CeleryTaskRecordQueryParams, TaskStatusUpdate,
    TaskTriggerResponse
)
from src.apps.scheduled_task.service import scheduled_task_service
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException
from src.shared.core.logging import get_logger
from src.apps.auth.dependencies import get_current_user_optional

logger = get_logger(__name__)
router = APIRouter(tags=["Scheduled Task Management"])


# 具体路径路由 - 必须放在参数化路径之前

@router.get("/v1/scheduled-tasks/records", response_model=UnifiedResponse)
async def get_task_execution_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    task_name: Optional[str] = Query(None, max_length=200, description="任务名称过滤"),
    task_status: Optional[str] = Query(None, max_length=50, description="任务状态过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取任务执行记录"""
    records, total = await scheduled_task_service.list_task_records(
        db,
        page=page,
        size=size,
        task_name=task_name,
        task_status=task_status
    )
    return paginated_response(
        items=records,
        total=total,
        page=page,
        size=size,
        msg="查询任务执行记录成功"
    )


@router.get("/v1/scheduled-tasks/meta/statistics", response_model=UnifiedResponse)
async def get_scheduled_task_statistics(
    db: AsyncSession = Depends(get_async_db)
):
    """获取定时任务统计信息"""
    task_stats = await scheduled_task_service.get_task_statistics(db)
    record_stats = await scheduled_task_service.get_record_statistics(db)
    
    return success_response(
        data={
            "task_statistics": task_stats,
            "record_statistics": record_stats
        },
        msg="获取统计信息成功"
    )


@router.get("/v1/scheduled-tasks", response_model=UnifiedResponse)
async def list_scheduled_tasks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    enabled_only: bool = Query(False, description="仅显示启用的任务"),
    agent_id: Optional[str] = Query(None, max_length=100, description="智能体ID过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """查询定时任务列表"""
    tasks, total = await scheduled_task_service.list_tasks(
        db, 
        page=page,
        size=size,
        enabled_only=enabled_only,
        agent_id=agent_id,
        search=search
    )
    return paginated_response(
        items=tasks,
        total=total,
        page=page,
        size=size,
        msg="查询定时任务列表成功"
    )


@router.post("/v1/scheduled-tasks", response_model=UnifiedResponse)
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """创建定时任务"""
    task_dict = task_data.dict()
    
    # 设置创建者
    creator_username = 'system'
    if current_user:
        creator_username = current_user.get('username', 'system')
    task_dict['create_by'] = creator_username
    
    # 如果是智能体任务，自动设置执行用户为创建者
    if task_dict.get('task_extra_config'):
        try:
            extra_config = json.loads(task_dict['task_extra_config'])
            if extra_config.get('task_type') == 'agent':
                # 将执行用户设置为创建者，便于审计
                extra_config['user'] = creator_username
                task_dict['task_extra_config'] = json.dumps(extra_config, ensure_ascii=False)
                logger.info(f"智能体定时任务的执行用户已自动设置为创建者: {creator_username}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"解析 task_extra_config 失败: {e}")
    
    task = await scheduled_task_service.create_task(db, task_dict)
    return success_response(
        data=task,
        msg="定时任务创建成功",
        code=ResponseCode.CREATED
    )


# 参数化路径路由 - 必须放在具体路径之后

@router.get("/v1/scheduled-tasks/records/{record_id}", response_model=UnifiedResponse)
async def get_task_execution_record(
    record_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取单条任务执行记录详情"""
    record = await scheduled_task_service.get_task_record_by_id(db, record_id)
    if not record:
        raise BusinessException(f"执行记录 {record_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=record,
        msg="获取执行记录成功"
    )


@router.get("/v1/scheduled-tasks/{task_id}/logs", response_model=UnifiedResponse)
async def get_task_execution_logs(
    task_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=1000, description="返回的记录数"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取任务执行日志"""
    logs = await scheduled_task_service.get_task_execution_logs(
        db,
        task_id=task_id,
        skip=skip,
        limit=limit
    )
    
    if not logs and await scheduled_task_service.get_task_by_id(db, task_id) is None:
        raise BusinessException(f"定时任务 {task_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=logs,
        msg="获取任务执行日志成功"
    )


@router.post("/v1/scheduled-tasks/{task_id}/enable", response_model=UnifiedResponse)
async def enable_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """启用定时任务"""
    success = await scheduled_task_service.enable_task(db, task_id)
    if not success:
        raise BusinessException(f"定时任务 {task_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"task_id": task_id, "enabled": True},
        msg="任务已启用"
    )


@router.post("/v1/scheduled-tasks/{task_id}/disable", response_model=UnifiedResponse)
async def disable_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """禁用定时任务"""
    success = await scheduled_task_service.disable_task(db, task_id)
    if not success:
        raise BusinessException(f"定时任务 {task_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"task_id": task_id, "enabled": False},
        msg="任务已禁用"
    )


@router.post("/v1/scheduled-tasks/{task_id}/trigger", response_model=UnifiedResponse)
async def trigger_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """手动触发定时任务"""
    task = await scheduled_task_service.get_task_by_id(db, task_id)
    if not task:
        raise BusinessException(f"定时任务 {task_id} 不存在", ResponseCode.NOT_FOUND)
    
    # 这里应该通过消息队列或HTTP API通知任务执行器
    # 而不是直接调用Celery
    return success_response(
        data={
            "message": "任务触发请求已发送",
            "task_id": task_id,
            "trigger_time": now_shanghai()
        },
        msg="任务触发成功"
    )


@router.get("/v1/scheduled-tasks/{task_id}", response_model=UnifiedResponse)
async def get_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定定时任务"""
    task = await scheduled_task_service.get_task_by_id(db, task_id)
    if not task:
        raise BusinessException(f"定时任务 {task_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=task,
        msg="获取定时任务成功"
    )


@router.put("/v1/scheduled-tasks/{task_id}", response_model=UnifiedResponse)
async def update_scheduled_task(
    task_id: int,
    task_data: ScheduledTaskUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """更新定时任务"""
    update_dict = task_data.dict(exclude_unset=True)
    # 设置更新者
    if current_user:
        update_dict['update_by'] = current_user.get('username', 'system')
    else:
        update_dict['update_by'] = 'system'
    
    updated_task = await scheduled_task_service.update_task(db, task_id, update_dict)
    if not updated_task:
        raise BusinessException(f"定时任务 {task_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_task,
        msg="定时任务更新成功"
    )


@router.delete("/v1/scheduled-tasks/{task_id}", response_model=UnifiedResponse)
async def delete_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """删除定时任务"""
    success = await scheduled_task_service.delete_task(db, task_id)
    if not success:
        raise BusinessException(f"定时任务 {task_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_id": task_id},
        msg="定时任务删除成功"
    )