"""
IDC运维报告模块API端点
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.auth.dependencies import get_current_user
from src.shared.schemas.response import success_response, paginated_response
from src.shared.core.logging import get_logger
from src.shared.db.config import get_async_db

from .schema import (
    IDCReportCreate,
    IDCReportUpdate,
    IDCReportResponse,
    IDCReportListParams,
    IDCReportStats,
    IDCLocationResponse,
    GenerateReportResponse
)
from .service.idc_report_service import IDCReportService

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[IDCReportResponse])
async def get_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    keyword: str = Query(None, description="关键词搜索"),
    idc_location: str = Query(None, description="IDC位置筛选"),
    report_type: str = Query(None, description="报告类型筛选"),
    status: str = Query(None, description="状态筛选"),
    start_date: str = Query(None, description="开始时间筛选"),
    end_date: str = Query(None, description="结束时间筛选"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取IDC报告列表"""
    # 构建查询参数
    params = IDCReportListParams(
        page=page,
        page_size=page_size,
        keyword=keyword,
        idc_location=idc_location,
        report_type=report_type,
        status=status
    )

    # 处理时间参数
    if start_date:
        from datetime import datetime
        params.start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        from datetime import datetime
        params.end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

    reports, total = await IDCReportService.get_report_list(db, params)

    return paginated_response(
        data=[IDCReportResponse.model_validate(report) for report in reports],
        page=page,
        page_size=page_size,
        total=total
    )


@router.get("/{report_id}", response_model=IDCReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个报告详情"""
    report = await IDCReportService.get_report_by_id(db, report_id)
    if not report:
        from src.shared.core.exceptions import BusinessException
        from src.shared.schemas.response import ResponseCode
        raise BusinessException(ResponseCode.NOT_FOUND, "报告不存在")

    return success_response(IDCReportResponse.model_validate(report))


@router.post("/", response_model=GenerateReportResponse)
async def create_report(
    data: IDCReportCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新的IDC报告生成任务"""
    report = await IDCReportService.create_report(db, data, current_user.get("username", "system"))

    # 这里可以触发异步报告生成任务
    # await trigger_report_generation(report.report_id)

    return success_response(GenerateReportResponse(
        report_id=report.report_id,
        message="报告生成任务已创建，正在后台生成中",
        status=report.status,
        estimated_time=30  # 预计30分钟完成
    ))


@router.put("/{report_id}", response_model=IDCReportResponse)
async def update_report(
    report_id: UUID,
    data: IDCReportUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """更新报告信息"""
    report = await IDCReportService.update_report(db, report_id, data, current_user.get("username", "system"))
    return success_response(IDCReportResponse.model_validate(report))


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """删除报告"""
    await IDCReportService.delete_report(db, report_id, current_user.get("username", "system"))
    return success_response({"message": "报告删除成功"})


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """下载报告文件"""
    report = await IDCReportService.get_report_by_id(db, report_id)
    if not report:
        from src.shared.core.exceptions import BusinessException
        from src.shared.schemas.response import ResponseCode
        raise BusinessException(ResponseCode.NOT_FOUND, "报告不存在")

    if not report.file_path or not report.file_name:
        from src.shared.core.exceptions import BusinessException
        from src.shared.schemas.response import ResponseCode
        raise BusinessException(ResponseCode.BUSINESS_ERROR, "报告文件不存在")

    # 检查文件是否存在
    import os
    if not os.path.exists(report.file_path):
        from src.shared.core.exceptions import BusinessException
        from src.shared.schemas.response import ResponseCode
        raise BusinessException(ResponseCode.BUSINESS_ERROR, "报告文件已丢失")

    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type='application/octet-stream'
    )


@router.get("/locations", response_model=List[IDCLocationResponse])
async def get_idc_locations(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取IDC位置列表"""
    locations = await IDCReportService.get_idc_locations(db)
    return success_response([IDCLocationResponse.model_validate(loc) for loc in locations])


@router.get("/stats", response_model=IDCReportStats)
async def get_report_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取报告统计信息"""
    stats = await IDCReportService.get_report_stats(db)
    return success_response(stats)