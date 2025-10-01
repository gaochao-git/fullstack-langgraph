"""
记忆管理API端点 - 使用全局统一响应格式
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.shared.core.exceptions import BusinessException
from src.shared.core.logging import get_logger
from src.shared.schemas.response import UnifiedResponse, success_response, paginated_response, ResponseCode
from src.apps.auth.dependencies import get_current_user
from .schema import (
    MemoryCreate, MemoryUpdate, MemorySearch, 
    MemoryResponse, SystemArchitectureCreate,
    IncidentCreate, UserPreferenceCreate
)
from .service import memory_service

logger = get_logger(__name__)
router = APIRouter(tags=["Memory Management"])


@router.post("/v1/memory/add", response_model=UnifiedResponse)
async def add_memory(
    data: MemoryCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """添加记忆"""
    # 记录操作用户
    if "user_id" not in data.namespace_params:
        data.namespace_params["user_id"] = current_user.get("user_id", "system")
    
    result = await memory_service.add_memory(db, data)
    return success_response(data=result, msg="记忆添加成功")


@router.post("/v1/memory/search", response_model=UnifiedResponse)
async def search_memories(
    data: MemorySearch,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """搜索记忆"""
    memories = await memory_service.search_memories(db, data)
    return success_response(data=memories)


@router.get("/v1/memory/list/{namespace_type}", response_model=UnifiedResponse)
async def list_memories(
    namespace_type: str,
    user_id: Optional[str] = Query(None),
    system_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """列出指定命名空间的所有记忆"""
    # 构建参数
    params = {}
    if user_id:
        params['user_id'] = user_id
    if system_id:
        params['system_id'] = system_id
        
    memories = await memory_service.list_memories_by_namespace(db, namespace_type, **params)
    return success_response(data=memories)


@router.put("/v1/memory/update", response_model=UnifiedResponse)
async def update_memory(
    data: MemoryUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """更新记忆"""
    await memory_service.update_memory(db, data)
    return success_response(msg="记忆更新成功")


@router.delete("/v1/memory/{memory_id}", response_model=UnifiedResponse)
async def delete_memory(
    memory_id: str,
    namespace: str = Query(..., description="命名空间"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """删除记忆"""
    await memory_service.delete_memory(db, namespace, memory_id)
    return success_response(msg="记忆删除成功")


# 专用接口

@router.post("/v1/memory/system-architecture", response_model=UnifiedResponse)
async def store_system_architecture(
    data: SystemArchitectureCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """存储系统架构信息"""
    await memory_service.store_system_architecture(db, data)
    return success_response(msg="系统架构信息已存储")


@router.post("/v1/memory/incident", response_model=UnifiedResponse)
async def store_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """存储故障案例"""
    await memory_service.store_incident(db, data)
    return success_response(msg="故障案例已存储")


@router.post("/v1/memory/user-preference", response_model=UnifiedResponse)
async def store_user_preference(
    data: UserPreferenceCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """存储用户偏好"""
    # 默认使用当前用户ID
    if not data.user_id:
        data.user_id = current_user.get("user_id", "system")
        
    await memory_service.store_user_preference(db, data)
    return success_response(msg="用户偏好已存储")


@router.get("/v1/memory/diagnosis-context", response_model=UnifiedResponse)
async def get_diagnosis_context(
    issue: str = Query(..., description="问题描述"),
    system_id: str = Query(..., description="系统ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取诊断上下文"""
    # 默认使用当前用户ID
    if not user_id:
        user_id = current_user.get("user_id", "system")
        
    context = await memory_service.get_diagnosis_context(db, issue, system_id, user_id)
    return success_response(data=context)


@router.get("/v1/memory/namespaces", response_model=UnifiedResponse)
async def get_namespaces(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有可用的命名空间类型"""
    namespaces = {
        "user": {
            "user_profile": "用户档案",
            "user_expertise": "用户专长",
            "user_preferences": "用户偏好"
        },
        "architecture": {
            "system_topology": "系统拓扑",
            "service_dependencies": "服务依赖",
            "deployment_info": "部署信息"
        },
        "business": {
            "business_flows": "业务流程",
            "sla_requirements": "SLA要求",
            "critical_services": "关键服务"
        },
        "operations": {
            "incident_history": "故障历史",
            "solution_patterns": "解决方案模式",
            "runbooks": "运维手册",
            "best_practices": "最佳实践"
        }
    }
    return success_response(data=namespaces)


