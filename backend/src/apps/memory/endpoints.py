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


# 删除手动添加记忆接口 - 应该通过 AI 对话自动学习


@router.post("/v1/memory/search", response_model=UnifiedResponse)
async def search_memories(
    data: MemorySearch,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """搜索记忆"""
    # 自动填充当前用户信息
    if not data.namespace_params.get("user_name"):
        user_name = current_user.get("username", "system")
        data.namespace_params["user_name"] = user_name
        logger.info(f"自动填充用户信息: user_name={user_name}")
    
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


# === 基于 Mem0 原生方法的记忆查看和管理接口 ===

from pydantic import BaseModel

class ConversationMemoryRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: Optional[str] = None
    agent_id: str = "diagnostic_agent"
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/v1/memory/add_conversation", response_model=UnifiedResponse)
async def add_conversation_memory(
    request: ConversationMemoryRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    从对话中添加记忆（新版三层记忆架构）

    会智能分析对话内容并保存到合适的记忆层级：
    - 如果包含用户档案信息 → 用户全局记忆
    - 如果包含有价值的经验 → 智能体全局记忆
    - 默认保存为 → 用户-智能体交互记忆
    """
    # 如果没有指定用户，使用当前用户
    user_id = request.user_id or current_user.get("username", "system")

    try:
        memory = await memory_service._get_memory()

        # 检测是否包含用户档案信息
        user_profile_keywords = ["我是", "我叫", "我负责", "我的专长", "我擅长"]
        content = " ".join([msg.get("content", "") for msg in request.messages])

        has_user_profile = any(keyword in content for keyword in user_profile_keywords)

        memory_ids = []

        # 如果包含用户档案信息，保存为用户全局记忆
        if has_user_profile:
            user_memory_id = await memory.add_user_global_memory(
                messages=request.messages,
                user_id=user_id,
                memory_type="profile",
                metadata={**(request.metadata or {}), "source": "conversation_test"}
            )
            memory_ids.append(user_memory_id)
            logger.info(f"保存了用户全局记忆: {user_memory_id}")

        # 默认保存为用户-智能体交互记忆
        interaction_memory_id = await memory.add_user_agent_memory(
            messages=request.messages,
            user_id=user_id,
            agent_id=request.agent_id,
            memory_type="interaction",
            metadata={**(request.metadata or {}), "source": "conversation_test"}
        )
        memory_ids.append(interaction_memory_id)
        logger.info(f"保存了用户-智能体交互记忆: {interaction_memory_id}")

        return success_response(
            data={"memory_ids": memory_ids, "count": len(memory_ids)},
            msg=f"对话记忆添加成功，保存了 {len(memory_ids)} 条记忆"
        )
    except Exception as e:
        logger.error(f"添加对话记忆失败: {e}")
        raise BusinessException(f"添加对话记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/memory/list_all", response_model=UnifiedResponse)
async def list_all_memories(
    user_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有记忆（Mem0 原生 get_all 方法）"""
    # 如果没有指定用户，使用当前用户
    if not user_id:
        user_id = current_user.get("username", "system")

    try:
        memory = await memory_service._get_memory()
        memories = await memory.list_all_memories(
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id
        )
        return success_response(data=memories)
    except Exception as e:
        logger.error(f"获取记忆列表失败: {e}")
        raise BusinessException(f"获取记忆列表失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/memory/list_by_level", response_model=UnifiedResponse)
async def list_memories_by_level(
    level: Optional[str] = Query(None, description="记忆层级: organization/user_global/agent_global/user_agent/session"),
    user_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    limit: int = Query(100, description="返回结果数量"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    按记忆层级查询记忆（管理员功能）

    Args:
        level: 记忆层级，可选值：
            - organization: 组织级全局记忆（所有人共享）
            - user_global: 用户级全局记忆（该用户所有智能体共享）
            - agent_global: 智能体级全局记忆（该智能体所有用户共享）
            - user_agent: 用户-智能体交互记忆
            - session: 会话临时记忆
            - 不传则返回所有记忆
        user_id: 用户ID（用于筛选user_global和user_agent层级）
        agent_id: 智能体ID（用于筛选agent_global和user_agent层级）
    """
    try:
        memory = await memory_service._get_memory()

        # 如果指定了层级，则按层级查询
        if level:
            if level == "organization":
                # 组织级记忆: user_id=organization
                memories = await memory.list_all_memories(user_id="organization")
            elif level == "user_global":
                if not user_id:
                    user_id = current_user.get("username", "system")
                # 用户全局记忆: 只指定user_id
                memories = await memory.list_all_memories(user_id=user_id)
            elif level == "agent_global":
                if not agent_id:
                    raise BusinessException("查询智能体全局记忆需要指定agent_id", ResponseCode.PARAM_ERROR)
                # 智能体全局记忆: user_id=agent_{agent_id} + agent_id
                memories = await memory.list_all_memories(
                    user_id=f"agent_{agent_id}",
                    agent_id=agent_id
                )
            elif level == "user_agent":
                if not user_id:
                    user_id = current_user.get("username", "system")
                if not agent_id:
                    raise BusinessException("查询用户-智能体记忆需要指定agent_id", ResponseCode.PARAM_ERROR)
                # 用户-智能体记忆: user_id + agent_id
                memories = await memory.list_all_memories(user_id=user_id, agent_id=agent_id)
            elif level == "session":
                # 会话记忆暂时返回空
                memories = []
            else:
                raise BusinessException(f"不支持的记忆层级: {level}", ResponseCode.PARAM_ERROR)
        else:
            # 不指定层级，返回所有记忆
            if not user_id:
                user_id = current_user.get("username", "system")
            memories = await memory.list_all_memories(user_id=user_id, agent_id=agent_id)

        return success_response(data=memories)
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"按层级查询记忆失败: {e}")
        raise BusinessException(f"按层级查询记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.post("/v1/memory/add_organization", response_model=UnifiedResponse)
async def add_organization_memory(
    content: str = Query(..., description="记忆内容"),
    memory_type: str = Query("general", description="记忆类型: system_architecture/standard_procedure/enterprise_policy/technical_decision"),
    category: str = Query("general", description="分类标签"),
    importance: str = Query("medium", description="重要性: low/medium/high"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    手动添加组织级全局记忆（管理员功能）

    Args:
        content: 记忆内容
        memory_type: 记忆类型
            - system_architecture: 系统架构
            - standard_procedure: 标准流程
            - enterprise_policy: 企业规范
            - technical_decision: 技术决策
            - general: 通用知识
        category: 分类标签
        importance: 重要性等级
    """
    try:
        memory = await memory_service._get_memory()

        # 构造消息格式
        messages = [
            {"role": "admin", "content": content}
        ]

        memory_id = await memory.add_organization_memory(
            messages=messages,
            memory_type=memory_type,
            metadata={
                "category": category,
                "importance": importance,
                "source": "manual_admin",
                "created_by": current_user.get("username", "admin")
            }
        )

        return success_response(data={"memory_id": memory_id}, msg="组织记忆添加成功")
    except Exception as e:
        logger.error(f"添加组织记忆失败: {e}")
        raise BusinessException(f"添加组织记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.delete("/v1/memory/delete_all", response_model=UnifiedResponse)
async def delete_all_memories(
    user_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """删除所有记忆（Mem0 原生 delete_all 方法）"""
    # 如果没有指定用户，使用当前用户
    if not user_id:
        user_id = current_user.get("username", "system")
    
    try:
        memory = await memory_service._get_memory()
        success = await memory.delete_all_memories(
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id
        )
        if success:
            return success_response(msg="记忆删除成功")
        else:
            raise BusinessException("记忆删除失败", ResponseCode.INTERNAL_ERROR)
    except Exception as e:
        logger.error(f"删除记忆失败: {e}")
        raise BusinessException(f"删除记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


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


