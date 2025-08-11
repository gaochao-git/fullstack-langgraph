"""SOP API routes - 使用全局统一响应格式"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.apps.sop.schema import (
    SOPTemplateCreate, SOPTemplateUpdate, SOPQueryParams,
    SOPProblemRuleCreate, SOPProblemRuleUpdate, SOPProblemRuleQuery,
    ZabbixItemOption
)
from src.apps.sop.service.sop_service import sop_service
from src.apps.sop.service.sop_problem_rule_service import sop_problem_rule_service
from src.apps.sop.service.zabbix_service import get_zabbix_service
from src.shared.core.logging import get_logger
from src.shared.schemas.response import (UnifiedResponse, success_response, paginated_response, ResponseCode)
from src.shared.core.exceptions import BusinessException
# from src.shared.core.dependencies import get_current_user

logger = get_logger(__name__)
router = APIRouter(tags=["SOP Management"])


@router.post("/v1/sops", response_model=UnifiedResponse)
async def create_sop_template(
    sop_data: SOPTemplateCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建SOP模板"""
    sop_template = await sop_service.create_sop(db, sop_data)
    return success_response(
        data=sop_template,
        msg="SOP模板创建成功",
        code=ResponseCode.CREATED
    )


@router.get("/v1/sops/{sop_id}", response_model=UnifiedResponse)
async def get_sop_template(
    sop_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定SOP模板"""
    sop_template = await sop_service.get_sop_by_id(db, sop_id)
    if not sop_template:
        raise BusinessException(f"SOP模板 {sop_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=sop_template,
        msg="获取SOP模板成功"
    )


@router.get("/v1/sops", response_model=UnifiedResponse)
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
    
    # 使用优化后的批量转换方法
    template_data, total = await sop_service.list_sops_dict(db, params)
    
    return paginated_response(
        items=template_data,
        total=total,
        page=page,
        size=size,
        msg="查询SOP模板列表成功"
    )


@router.put("/v1/sops/{sop_id}", response_model=UnifiedResponse)
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
        data=updated_template,
        msg="SOP模板更新成功"
    )


@router.delete("/v1/sops/{sop_id}", response_model=UnifiedResponse)
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


@router.get("/v1/sops/meta/categories", response_model=UnifiedResponse)
async def get_sop_categories(
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有SOP分类 - 统一对象格式"""
    categories = await sop_service.get_category_options(db)
    return success_response(
        data=categories,
        msg="获取SOP分类成功"
    )


@router.get("/v1/sops/meta/teams", response_model=UnifiedResponse)
async def get_sop_teams(
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有SOP团队 - 统一对象格式"""
    teams = await sop_service.get_team_options(db)
    return success_response(
        data=teams,
        msg="获取SOP团队成功"
    )


@router.get("/v1/sops/meta/severity", response_model=UnifiedResponse)
async def get_sop_severity_options(
    db: AsyncSession = Depends(get_async_db)
):
    """获取SOP严重程度选项 - 统一对象格式"""
    severity_options = await sop_service.get_severity_options(db)
    return success_response(
        data=severity_options,
        msg="获取SOP严重程度选项成功"
    )


@router.get("/v1/sops/meta/statistics", response_model=UnifiedResponse)
async def get_sop_statistics(
    db: AsyncSession = Depends(get_async_db)
):
    """获取SOP统计信息"""
    statistics = await sop_service.get_category_statistics(db)
    return success_response(
        data=statistics,
        msg="获取SOP统计信息成功"
    )


# ============ SOP Problem Rule 相关接口 ============

@router.get("/v1/sop-problem-rules", response_model=UnifiedResponse)
async def list_sop_problem_rules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sop_id: Optional[str] = Query(None, description="SOP ID"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取SOP问题规则列表"""
    query = SOPProblemRuleQuery(
        page=page,
        page_size=page_size,
        search=search,
        sop_id=sop_id,
        is_enabled=is_enabled
    )
    
    rules, total = await sop_problem_rule_service.list_rules(db, query)
    
    return paginated_response(
        items=rules,
        total=total,
        page=page,
        size=page_size,
        msg="获取规则列表成功"
    )


@router.get("/v1/sop-problem-rules/{rule_id}", response_model=UnifiedResponse)
async def get_sop_problem_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取SOP问题规则详情"""
    rule = await sop_problem_rule_service.get_rule(db, rule_id)
    if not rule:
        raise BusinessException(f"规则 {rule_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=rule,
        msg="获取规则详情成功"
    )


@router.post("/v1/sop-problem-rules", response_model=UnifiedResponse)
async def create_sop_problem_rule(
    rule_data: SOPProblemRuleCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建SOP问题规则"""
    rule = await sop_problem_rule_service.create_rule(
        db, 
        rule_data, 
        "system"  # 暂时使用固定值
    )
    
    return success_response(
        data=rule.to_dict() if hasattr(rule, 'to_dict') else rule,
        msg="创建规则成功",
        code=ResponseCode.CREATED
    )


@router.put("/v1/sop-problem-rules/{rule_id}", response_model=UnifiedResponse)
async def update_sop_problem_rule(
    rule_id: int,
    rule_data: SOPProblemRuleUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新SOP问题规则"""
    rule = await sop_problem_rule_service.update_rule(
        db,
        rule_id,
        rule_data,
        "system"  # 暂时使用固定值
    )
    
    return success_response(
        data=rule.to_dict() if hasattr(rule, 'to_dict') else rule,
        msg="更新规则成功"
    )


@router.delete("/v1/sop-problem-rules/{rule_id}", response_model=UnifiedResponse)
async def delete_sop_problem_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """删除SOP问题规则"""
    await sop_problem_rule_service.delete_rule(db, rule_id)
    
    return success_response(
        data={"deleted_id": rule_id},
        msg="删除规则成功"
    )


# ============ Zabbix 相关接口 ============

@router.get("/v1/sops/zabbix/items", response_model=UnifiedResponse)
async def get_zabbix_items(
    search: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """获取Zabbix监控项列表"""
    try:
        zabbix_service = get_zabbix_service()
        
        async with zabbix_service:
            if search:
                # 搜索特定的监控项
                items = await zabbix_service.get_items(
                    search={"name": search},
                    limit=limit
                )
                # 格式化为选项 - 只显示key
                options = [
                    {
                        "value": item["key_"],
                        "label": item["key_"]
                    }
                    for item in items
                ]
            else:
                # 获取常用监控项
                options = await zabbix_service.get_common_items()
        
        return success_response(
            data=options,
            msg="获取Zabbix监控项成功"
        )
        
    except Exception as e:
        logger.error(f"Failed to get Zabbix items: {e}")
        raise BusinessException(
            f"获取Zabbix监控项失败: {str(e)}",
            ResponseCode.BAD_GATEWAY
        )