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
    # 根据记忆类型自动填充用户信息
    memory_category = data.metadata.get("memory_category", "")
    
    if memory_category == "personal":
        # 个人记忆：使用当前用户信息
        user_name = current_user.get("username", "system")
        data.namespace_params["user_name"] = user_name
    else:
        # 系统记忆：使用系统标识
        if "user_name" not in data.namespace_params:
            data.namespace_params["user_name"] = "system"
    
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


@router.get("/v1/memory/search/{namespace_type}", response_model=UnifiedResponse)
async def search_memories_by_namespace(
    namespace_type: str,
    query: str = Query(..., description="搜索查询"),
    user_name: Optional[str] = Query(None),
    system_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(10, description="返回结果数量"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """检索指定命名空间的记忆（用于AI诊断检索）"""
    # 构建参数
    params = {}
    
    # 为个人记忆自动获取当前用户
    if namespace_type == "user_profile":
        current_user_name = current_user.get("username", "system")
        params['user_name'] = current_user_name
    elif user_name:
        params['user_name'] = user_name
    
    if system_id:
        params['system_id'] = system_id
    
    # 使用搜索接口而不是列表接口
    search_data = MemorySearch(
        namespace=namespace_type,
        query=query,
        limit=limit,
        namespace_params=params
    )
    
    memories = await memory_service.search_memories(db, search_data)
    return success_response(data=memories)


@router.get("/v1/memory/manage/{namespace_type}", response_model=UnifiedResponse)
async def manage_memories(
    namespace_type: str,
    user_name: Optional[str] = Query(None),
    system_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """管理指定命名空间的所有记忆（用于记忆管理界面）"""
    # 构建参数
    params = {}
    
    # 为个人记忆自动获取当前用户
    if namespace_type == "user_profile":
        current_user_name = current_user.get("username", "system")
        params['user_name'] = current_user_name
    elif user_name:
        params['user_name'] = user_name
    
    if system_id:
        params['system_id'] = system_id
    
    # 临时解决方案：使用搜索功能来获取所有记忆，因为 get_all 有问题
    logger.info(f"管理接口: namespace_type={namespace_type}, params={params}")
    
    # 使用一个通用查询来获取所有相关记忆
    search_data = MemorySearch(
        namespace=namespace_type,
        query="个人档案 高超 信息 记忆 内容",  # 使用通用查询词以获取更多记忆
        limit=100,  # 足够大的限制
        namespace_params=params
    )
    
    try:
        memories = await memory_service.search_memories(db, search_data)
        logger.info(f"通过搜索获取到记忆数量: {len(memories)}")
        return success_response(data=memories)
    except Exception as e:
        logger.error(f"管理接口获取记忆失败: {e}")
        # 如果搜索失败，尝试原来的方法
        memories = await memory_service.list_memories_by_namespace(db, namespace_type, **params)
        return success_response(data=memories)


@router.put("/v1/memory/update", response_model=UnifiedResponse)
async def update_memory(
    data: MemoryUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """更新记忆"""
    await memory_service.update_memory(db, data, current_user)
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
    # 默认使用当前用户名
    if not data.user_id:
        user_name = current_user.get("username", "system")
        data.user_id = user_name
        
    await memory_service.store_user_preference(db, data)
    return success_response(msg="用户偏好已存储")


@router.get("/v1/memory/diagnosis-context", response_model=UnifiedResponse)
async def get_diagnosis_context(
    issue: str = Query(..., description="问题描述"),
    system_id: str = Query(..., description="系统ID"),
    user_name: Optional[str] = Query(None, description="用户名"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取诊断上下文"""
    # 默认使用当前用户名
    if not user_name:
        user_name = current_user.get("username", "system")
        
    context = await memory_service.get_diagnosis_context(db, issue, system_id, user_name)
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


# 用户界面管理接口

@router.get("/v1/memory/stats", response_model=UnifiedResponse)
async def get_memory_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取记忆统计信息"""
    user_name = current_user.get("username", "system")
    stats = await memory_service.get_memory_stats(db)
    
    # 添加用户相关的统计
    stats.update({
        "current_user": user_name,
        "user_memory_count": {
            "profile": 0,  # 实际实现时可以统计
            "expertise": 0,
            "preferences": 0
        }
    })
    
    return success_response(data=stats)


@router.get("/v1/memory/user/profile", response_model=UnifiedResponse)
async def get_user_profile_memories(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取当前用户的个人档案记忆"""
    user_name = current_user.get("username", "system")
    
    # 获取用户相关的所有记忆
    profile_memories = await memory_service.list_memories_by_namespace(
        db, "user_profile", user_name=user_name
    )
    expertise_memories = await memory_service.list_memories_by_namespace(
        db, "user_expertise", user_name=user_name
    )
    preference_memories = await memory_service.list_memories_by_namespace(
        db, "user_preferences", user_name=user_name
    )
    
    return success_response(data={
        "profile": profile_memories,
        "expertise": expertise_memories,
        "preferences": preference_memories,
        "user_name": user_name
    })


@router.post("/v1/memory/batch", response_model=UnifiedResponse)
async def batch_create_memories(
    memories: List[MemoryCreate],
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """批量创建记忆"""
    user_name = current_user.get("username", "system")
    results = []
    
    for memory_data in memories:
        # 确保每个记忆都包含用户名
        if "user_name" not in memory_data.namespace_params:
            memory_data.namespace_params["user_name"] = user_name
            
        try:
            result = await memory_service.add_memory(db, memory_data)
            results.append({"success": True, "memory_id": result.get("memory_id")})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    
    success_count = sum(1 for r in results if r["success"])
    return success_response(
        data={"results": results, "success_count": success_count, "total_count": len(memories)},
        msg=f"批量创建完成，成功 {success_count}/{len(memories)} 条"
    )


