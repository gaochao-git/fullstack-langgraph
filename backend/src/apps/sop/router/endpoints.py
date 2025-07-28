"""SOP API routes - 使用全局统一响应格式"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.apps.sop.schema.sop import (
    SOPTemplateCreate, SOPTemplateUpdate, SOPQueryParams
)
from src.apps.sop.service.sop_service import sop_service
from src.shared.core.logging import get_logger
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException

logger = get_logger(__name__)
router = APIRouter(tags=["SOP Management"])


@router.post("/sops", response_model=UnifiedResponse)
async def create_sop_template(
    sop_data: SOPTemplateCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建SOP模板"""
    sop_template = await sop_service.create_sop(db, sop_data)
    return success_response(
        data=sop_template.to_dict(),
        msg="SOP模板创建成功",
        code=ResponseCode.CREATED
    )


@router.get("/sops/{sop_id}", response_model=UnifiedResponse)
async def get_sop_template(
    sop_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定SOP模板"""
    sop_template = await sop_service.get_sop_by_id(db, sop_id)
    if not sop_template:
        raise BusinessException(f"SOP模板 {sop_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=sop_template.to_dict(),
        msg="获取SOP模板成功"
    )


@router.get("/sops", response_model=UnifiedResponse)
async def list_sop_templates(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    category: Optional[str] = Query(None, max_length=100, description="分类过滤"),
    severity: Optional[str] = Query(None, description="严重程度过滤"),
    team_name: Optional[str] = Query(None, max_length=100, description="团队过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """查询SOP模板列表"""
    # 构建查询参数
    params = SOPQueryParams(
        search=search,
        category=category,
        severity=severity,
        team_name=team_name,
        limit=size,
        offset=(page - 1) * size
    )
    
    templates, total = await sop_service.list_sops(db, params)
    template_data = [template.to_dict() for template in templates]
    
    return paginated_response(
        items=template_data,
        total=total,
        page=page,
        size=size,
        msg="查询SOP模板列表成功"
    )


@router.put("/sops/{sop_id}", response_model=UnifiedResponse)
async def update_sop_template(
    sop_id: str,
    sop_data: SOPTemplateUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新SOP模板"""
    updated_template = await sop_service.update_sop(db, sop_id, sop_data)
    if not updated_template:
        raise BusinessException(f"SOP模板 {sop_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_template.to_dict(),
        msg="SOP模板更新成功"
    )


@router.delete("/sops/{sop_id}", response_model=UnifiedResponse)
async def delete_sop_template(
    sop_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """删除SOP模板"""
    success = await sop_service.delete_sop(db, sop_id)
    if not success:
        raise BusinessException(f"SOP模板 {sop_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_id": sop_id},
        msg="SOP模板删除成功"
    )


@router.get("/sops/meta/categories", response_model=UnifiedResponse)
async def get_sop_categories(
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有SOP分类"""
    categories = await sop_service.get_categories(db)
    return success_response(
        data=categories,
        msg="获取SOP分类成功"
    )


@router.get("/sops/meta/teams", response_model=UnifiedResponse)
async def get_sop_teams(
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有SOP团队"""
    teams = await sop_service.get_teams(db)
    return success_response(
        data=teams,
        msg="获取SOP团队成功"
    )


@router.get("/sops/meta/statistics", response_model=UnifiedResponse)
async def get_sop_statistics(
    db: AsyncSession = Depends(get_async_db)
):
    """获取SOP统计信息"""
    statistics = await sop_service.get_category_statistics(db)
    return success_response(
        data=statistics,
        msg="获取SOP统计信息成功"
    )