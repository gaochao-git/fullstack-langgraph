"""敏感数据扫描API端点"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException
from src.apps.auth.dependencies import get_current_user_optional
from .service import scan_task_service
from .schema import ScanTaskCreate, ScanTaskProgress, ScanTaskResult

router = APIRouter(tags=["Sensitive Data Scan"])


@router.post("/v1/scan/tasks", response_model=UnifiedResponse)
async def create_scan_task(
    task_data: ScanTaskCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """创建敏感数据扫描任务"""
    create_by = current_user.get('username', 'system') if current_user else 'system'
    
    # 创建扫描任务
    task = await scan_task_service.create_scan_task(
        db=db,
        file_ids=task_data.file_ids,
        create_by=create_by
    )
    
    return success_response(
        data=task,
        msg="扫描任务创建成功",
        code=ResponseCode.CREATED
    )


@router.get("/v1/scan/tasks/{task_id}/progress", response_model=UnifiedResponse)
async def get_task_progress(
    task_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取扫描任务进度"""
    progress = await scan_task_service.get_task_progress(db, task_id)
    return success_response(data=progress, msg="获取任务进度成功")


@router.get("/v1/scan/tasks/{task_id}/result", response_model=UnifiedResponse)
async def get_task_result(
    task_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取扫描任务结果"""
    result = await scan_task_service.get_task_result(db, task_id)
    return success_response(data=result, msg="获取任务结果成功")


@router.get("/v1/scan/tasks", response_model=UnifiedResponse)
async def list_scan_tasks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    create_by: Optional[str] = Query(None, description="创建者过滤"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """查询扫描任务列表"""
    # 如果未指定创建者，默认查询当前用户的任务
    if not create_by and current_user:
        create_by = current_user.get('username')
    
    tasks, total = await scan_task_service.list_tasks(
        db=db,
        page=page,
        size=size,
        create_by=create_by
    )
    
    return paginated_response(
        items=tasks,
        total=total,
        page=page,
        size=size,
        msg="查询任务列表成功"
    )


@router.get("/v1/scan/results/{task_id}/{file_id}/jsonl", response_class=PlainTextResponse)
async def get_scan_result_jsonl(
    task_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取扫描结果的JSONL内容"""
    content = await scan_task_service.get_result_jsonl_content(db, task_id, file_id)
    return PlainTextResponse(content=content, media_type="application/x-ndjson")


@router.get("/v1/scan/results/{task_id}/{file_id}/html", response_model=UnifiedResponse)
async def get_scan_result_html(
    task_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取扫描结果的HTML报告"""
    content = await scan_task_service.get_result_html_content(db, task_id, file_id)
    return success_response(data={"html": content}, msg="获取HTML报告成功")