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
from .config_service import scan_config_service
from .schema import (
    ScanTaskCreate, ScanTaskProgress, ScanTaskResult,
    ScanConfigCreate, ScanConfigUpdate, ScanConfigResponse
)

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
        config_id=task_data.config_id,
        max_workers=task_data.max_workers,
        batch_length=task_data.batch_length,
        extraction_passes=task_data.extraction_passes,
        max_char_buffer=task_data.max_char_buffer,
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
    task_id: Optional[str] = Query(None, description="任务ID过滤"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """查询扫描任务列表"""
    # 不再默认过滤当前用户，允许查看所有任务
    
    tasks, total = await scan_task_service.list_tasks(
        db=db,
        page=page,
        size=size,
        create_by=create_by,
        task_id=task_id
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


# ==================== 扫描配置管理 API ====================

@router.post("/v1/scan/configs", response_model=UnifiedResponse)
async def create_scan_config(
    config_data: ScanConfigCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """创建扫描配置"""
    create_by = current_user.get('username', 'system') if current_user else 'system'

    config = await scan_config_service.create_config(
        db=db,
        config_data=config_data,
        create_by=create_by
    )

    return success_response(
        data=config,
        msg="创建配置成功",
        code=ResponseCode.CREATED
    )


@router.put("/v1/scan/configs/{config_id}", response_model=UnifiedResponse)
async def update_scan_config(
    config_id: str,
    config_data: ScanConfigUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """更新扫描配置"""
    update_by = current_user.get('username', 'system') if current_user else 'system'

    config = await scan_config_service.update_config(
        db=db,
        config_id=config_id,
        config_data=config_data,
        update_by=update_by
    )

    return success_response(data=config, msg="更新配置成功")


@router.delete("/v1/scan/configs/{config_id}", response_model=UnifiedResponse)
async def delete_scan_config(
    config_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """删除扫描配置"""
    await scan_config_service.delete_config(db=db, config_id=config_id)
    return success_response(msg="删除配置成功")


@router.get("/v1/scan/configs/{config_id}", response_model=UnifiedResponse)
async def get_scan_config(
    config_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取配置详情"""
    config = await scan_config_service.get_config(db=db, config_id=config_id)
    return success_response(data=config, msg="获取配置成功")


@router.get("/v1/scan/configs/default/get", response_model=UnifiedResponse)
async def get_default_scan_config(
    db: AsyncSession = Depends(get_async_db)
):
    """获取默认配置"""
    config = await scan_config_service.get_default_config(db=db)
    if config:
        return success_response(data=config, msg="获取默认配置成功")
    else:
        return success_response(data=None, msg="未设置默认配置")


@router.get("/v1/scan/configs", response_model=UnifiedResponse)
async def list_scan_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    config_name: Optional[str] = Query(None, description="配置名称（模糊查询）"),
    status: Optional[str] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_async_db)
):
    """查询配置列表"""
    config_list, total = await scan_config_service.list_configs(
        db=db,
        page=page,
        size=size,
        config_name=config_name,
        status=status
    )

    return paginated_response(
        items=config_list,
        total=total,
        page=page,
        size=size,
        msg="查询配置列表成功"
    )