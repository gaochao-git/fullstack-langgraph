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
from src.apps.sop.service.alarm_service import alarm_service
from src.shared.core.logging import get_logger
from src.shared.schemas.response import (UnifiedResponse, success_response, paginated_response, ResponseCode)
from src.shared.core.exceptions import BusinessException
from src.apps.auth.dependencies import get_current_user

logger = get_logger(__name__)
router = APIRouter(tags=["SOP Management"])


@router.post("/v1/sops", response_model=UnifiedResponse)
async def create_sop_template(
    sop_data: SOPTemplateCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """创建SOP模板"""
    # 获取当前用户名
    username = current_user.get("username", "system")
    
    # 将用户信息添加到数据中
    sop_data_dict = sop_data.dict()
    sop_data_dict["create_by"] = username
    
    # 创建SOP
    sop_template = await sop_service.create_sop(db, sop_data_dict)
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
    severity: Optional[str] = Query(None, description="严重程度过滤"),
    team_name: Optional[str] = Query(None, max_length=100, description="团队过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """查询SOP模板列表"""
    # 构建查询参数
    params = SOPQueryParams(
        search=search,
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
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """更新SOP模板"""
    # 获取当前用户名
    username = current_user.get("username", "system")
    
    # 将用户信息添加到数据中
    sop_data_dict = sop_data.dict()
    sop_data_dict["update_by"] = username
    
    # 更新SOP
    updated_template = await sop_service.update_sop(db, sop_id, sop_data_dict)
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


# ============ 报警相关接口 ============

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


@router.get("/v1/sops/alarms", response_model=UnifiedResponse)
async def get_alarms(
    alarm_level: Optional[List[str]] = Query(None, description="严重级别过滤，支持多选"),
    alarm_time: Optional[str] = Query(None, description="时间过滤，返回大于等于此时间的告警"),
    team_tag: Optional[List[str]] = Query(None, description="团队标签过滤，支持多选"),
    idc_tag: Optional[List[str]] = Query(None, description="机房标签过滤，支持多选"),
    alarm_ip: Optional[str] = Query(None, description="主机IP过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=1000, description="每页数量")
):
    """
    获取报警系统的当前报警
    
    注意：外部报警接口需要返回统一格式的数据
    """
    logger.info(f"Getting alarms with filters: level={alarm_level}, time>={alarm_time}, team={team_tag}, idc={idc_tag}, ip={alarm_ip}")
    
    try:
        result = await alarm_service.get_alarms(
            alarm_level=alarm_level,
            alarm_time=alarm_time,
            team_tag=team_tag,
            idc_tag=idc_tag,
            alarm_ip=alarm_ip,
            page=page,
            page_size=page_size
        )
        
        # 如果结果是分页格式，直接返回
        if isinstance(result, dict) and 'data' in result:
            logger.info(f"Successfully retrieved {result.get('total', 0)} total alarms, page {result.get('page', 1)}")
            return success_response(
                data=result,
                msg="获取报警成功"
            )
        else:
            # 兼容旧格式
            logger.info(f"Successfully retrieved alarms (legacy format)")
            return success_response(
                data=result,
                msg="获取报警成功"
            )
        
    except BusinessException as e:
        logger.error(f"Business exception getting alarms: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting alarms: {e}", exc_info=True)
        raise BusinessException(
            f"获取报警失败: {str(e)}",
            ResponseCode.BAD_GATEWAY
        )


# 保留原有的Zabbix接口作为Zabbix特定实现
@router.get("/v1/sops/zabbix/problems", response_model=UnifiedResponse)
async def get_zabbix_problems(
    host_id: Optional[str] = Query(None, description="主机ID"),
    severity_min: int = Query(2, ge=0, le=5, description="最小严重级别"),
    recent_only: bool = Query(True, description="只获取最近的问题"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """获取Zabbix当前的问题（专用于Zabbix系统）"""
    logger.info(f"Getting Zabbix problems with params: severity_min={severity_min}, recent_only={recent_only}, limit={limit}")
    
    try:
        zabbix_service = get_zabbix_service()
        
        async with zabbix_service:
            host_ids = [host_id] if host_id else None
            problems = await zabbix_service.get_problems(
                host_ids=host_ids,
                severity_min=severity_min,
                recent_only=recent_only,
                limit=limit
            )
            logger.info(f"Successfully retrieved {len(problems)} problems from Zabbix")
        
        return success_response(
            data=problems,
            msg="获取Zabbix问题成功"
        )
        
    except BusinessException as e:
        logger.error(f"Business exception getting Zabbix problems: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting Zabbix problems: {e}", exc_info=True)
        raise BusinessException(
            f"获取Zabbix问题失败: {str(e)}",
            ResponseCode.BAD_GATEWAY
        )


# Zabbix特定接口
@router.get("/v1/sops/zabbix/problem-items", response_model=UnifiedResponse)
async def get_zabbix_problem_items(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """获取有问题的监控项key列表"""
    try:
        zabbix_service = get_zabbix_service()
        
        async with zabbix_service:
            item_keys = await zabbix_service.get_problem_items(limit=limit)
        
        # 格式化为选项格式
        options = [
            {
                "value": key,
                "label": key
            }
            for key in item_keys
        ]
        
        return success_response(
            data=options,
            msg="获取问题监控项成功"
        )
        
    except Exception as e:
        logger.error(f"Failed to get Zabbix problem items: {e}")
        raise BusinessException(
            f"获取问题监控项失败: {str(e)}",
            ResponseCode.BAD_GATEWAY
        )


@router.get("/v1/sops/zabbix/hosts", response_model=UnifiedResponse)
async def get_zabbix_hosts():
    """获取Zabbix监控的主机列表"""
    try:
        zabbix_service = get_zabbix_service()
        
        async with zabbix_service:
            hosts = await zabbix_service.get_hosts()
        
        return success_response(
            data=hosts,
            msg="获取Zabbix主机列表成功"
        )
        
    except Exception as e:
        logger.error(f"Failed to get Zabbix hosts: {e}")
        raise BusinessException(
            f"获取Zabbix主机列表失败: {str(e)}",
            ResponseCode.BAD_GATEWAY
        )