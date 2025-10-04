"""
记忆管理API端点 - 完全符合Mem0标准
仅包含Mem0官方API，无任何扩展或废弃接口
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.shared.db.config import get_async_db
from src.shared.core.exceptions import BusinessException
from src.shared.core.logging import get_logger
from src.shared.schemas.response import UnifiedResponse, success_response, ResponseCode
from src.apps.auth.dependencies import get_current_user
from .service import memory_service

logger = get_logger(__name__)
router = APIRouter(tags=["Memory Management"])


def format_memory_times(memory: dict) -> dict:
    """格式化时间字段，从US/Pacific转换到Asia/Shanghai"""
    if not memory:
        return {}

    # 处理created_at和updated_at
    for time_field in ['created_at', 'updated_at']:
        if time_field in memory and memory[time_field]:
            try:
                time_str = memory[time_field]
                if isinstance(time_str, str) and 'T' in time_str:
                    # 解析ISO格式时间（Mem0使用US/Pacific时区）
                    # 2025-10-03T16:37:32.038811-07:00 -> 2025-10-04 07:37:32
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    # 转换到上海时区
                    shanghai_tz = timezone(timedelta(hours=8))
                    dt_shanghai = dt.astimezone(shanghai_tz)
                    # 格式化
                    memory[time_field] = dt_shanghai.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass

    return memory


# ==================== Mem0标准数据模型 ====================

class MemoryAddRequest(BaseModel):
    """添加记忆请求 - 符合Mem0标准"""
    messages: List[Dict[str, str]]
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    infer: bool = True

class MemoryUpdateRequest(BaseModel):
    """更新记忆请求 - 只能更新内容

    注意：Mem0开源版update方法有bug会丢失metadata，
    这是Mem0的问题，不是我们的实现问题
    """
    content: str


# ==================== Mem0核心API ====================

@router.post("/v1/memory", response_model=UnifiedResponse)
async def add_memory(
    request: MemoryAddRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    添加记忆 (Mem0: memory.add())

    完全符合Mem0标准的添加记忆接口。
    支持三层架构：
    - 用户记忆：仅指定user_id
    - 智能体记忆：仅指定agent_id
    - 会话记忆：指定user_id + run_id
    - 交互记忆：指定user_id + agent_id
    """
    # 智能体记忆特殊处理：如果仅有agent_id，不要自动添加user_id
    if request.agent_id and not request.user_id and not request.run_id:
        # 纯智能体记忆，不添加user_id
        logger.info(f"添加纯智能体记忆: agent_id={request.agent_id}")
    elif not request.user_id and not request.agent_id:
        # 如果既没有user_id也没有agent_id，使用当前用户
        request.user_id = current_user.get("username", "system")
        logger.info(f"未指定任何ID，使用当前用户: {request.user_id}")

    try:
        memory = await memory_service._get_memory()

        # 调用标准的add_conversation_memory方法
        result = await memory.add_conversation_memory(
            messages=request.messages,
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            metadata=request.metadata
        )

        logger.info(f"成功添加记忆: user_id={request.user_id}, agent_id={request.agent_id}, run_id={request.run_id}")
        return success_response(
            data={"memory_id": result},
            msg="记忆添加成功"
        )
    except Exception as e:
        logger.error(f"添加记忆失败: {e}")
        raise BusinessException(f"添加记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/memory/search", response_model=UnifiedResponse)
async def search_memories(
    query: str = Query(..., description="搜索查询"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    agent_id: Optional[str] = Query(None, description="智能体ID"),
    run_id: Optional[str] = Query(None, description="会话ID"),
    limit: int = Query(20, description="返回结果数量"),
    threshold: Optional[float] = Query(None, description="相似度阈值"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    搜索记忆 (Mem0: memory.search())

    搜索符合条件的记忆，支持语义搜索。
    """
    # 如果没有指定任何条件，使用当前用户
    # 如果指定了agent_id或run_id，则按指定条件查询
    if not user_id and not agent_id and not run_id:
        user_id = current_user.get("username", "system")

    try:
        memory = await memory_service._get_memory()
        result = await memory.search_memories(
            query=query,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            limit=limit
        )

        # 处理Mem0返回格式
        if isinstance(result, dict):
            memories = result.get("results", [])
        else:
            memories = result

        # 格式化时间字段
        memories = [format_memory_times(mem) for mem in memories]

        logger.info(f"搜索记忆: query='{query[:50]}...', 返回 {len(memories)} 条结果")
        return success_response(data=memories)
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise BusinessException(f"搜索记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/memory", response_model=UnifiedResponse)
async def get_all_memories(
    user_id: Optional[str] = Query(None, description="用户ID"),
    agent_id: Optional[str] = Query(None, description="智能体ID"),
    run_id: Optional[str] = Query(None, description="会话ID"),
    limit: int = Query(100, description="返回结果数量"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取所有记忆 (Mem0: memory.get_all())

    获取指定条件的所有记忆，完全符合Mem0标准。
    """
    # 如果没有指定任何条件，使用当前用户
    # 如果指定了agent_id或run_id，则按指定条件查询
    if not user_id and not agent_id and not run_id:
        user_id = current_user.get("username", "system")

    try:
        memory = await memory_service._get_memory()
        result = await memory.list_all_memories(
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id
        )

        # 处理Mem0返回格式（可能是dict或list）
        if isinstance(result, dict):
            # Mem0可能返回 {"results": [...]} 格式
            memories = result.get("results", [])
        else:
            memories = result

        # 限制返回数量
        if len(memories) > limit:
            memories = memories[:limit]

        # 格式化时间字段
        memories = [format_memory_times(mem) for mem in memories]

        logger.info(f"获取记忆列表: user_id={user_id}, 返回 {len(memories)} 条")
        return success_response(data=memories)
    except Exception as e:
        logger.error(f"获取记忆列表失败: {e}")
        raise BusinessException(f"获取记忆列表失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/memory/{memory_id}", response_model=UnifiedResponse)
async def get_memory(
    memory_id: str = Path(..., description="记忆ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取单个记忆 (Mem0: memory.get())

    通过记忆ID获取单个记忆的详细信息。
    """
    try:
        memory = await memory_service._get_memory()

        # Mem0原生get方法
        if hasattr(memory.memory, 'get'):
            result = memory.memory.get(memory_id)
            if result:
                # 格式化时间字段
                result = format_memory_times(result)
                return success_response(data=result)
            else:
                raise BusinessException(f"记忆不存在: {memory_id}", ResponseCode.NOT_FOUND)
        else:
            raise BusinessException("当前Mem0版本不支持get方法", ResponseCode.NOT_IMPLEMENTED)

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取记忆失败: {e}")
        raise BusinessException(f"获取记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.put("/v1/memory/{memory_id}", response_model=UnifiedResponse)
async def update_memory(
    memory_id: str = Path(..., description="记忆ID"),
    request: MemoryUpdateRequest = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新记忆 (Mem0: memory.update())

    只更新记忆内容，metadata保持不变。
    """
    try:
        memory = await memory_service._get_memory()

        # Mem0的update方法有bug会丢失metadata
        # 需要先获取原记忆，提取metadata，再调用_update_memory
        if hasattr(memory.memory, 'get') and hasattr(memory.memory, '_update_memory'):
            # 获取原记忆
            existing_memory = memory.memory.get(memory_id)
            if not existing_memory:
                raise BusinessException(f"记忆不存在: {memory_id}", ResponseCode.NOT_FOUND)

            # 提取原始metadata
            original_metadata = existing_memory.get('metadata', {})

            # 准备embeddings
            embeddings = memory.memory.embedding_model.embed(request.content, "update")
            existing_embeddings = {request.content: embeddings}

            # 调用内部方法，传入原始metadata
            memory.memory._update_memory(
                memory_id=memory_id,
                data=request.content,
                existing_embeddings=existing_embeddings,
                metadata=original_metadata
            )

            logger.info(f"成功更新记忆内容: {memory_id}, 保留metadata")
            return success_response(
                data={"memory_id": memory_id, "updated": True},
                msg="记忆内容更新成功"
            )
        else:
            raise BusinessException("当前Mem0版本不支持update方法", ResponseCode.NOT_IMPLEMENTED)

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"更新记忆失败: {e}")
        raise BusinessException(f"更新记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.delete("/v1/memory/{memory_id}", response_model=UnifiedResponse)
async def delete_memory(
    memory_id: str = Path(..., description="记忆ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除单个记忆 (Mem0: memory.delete())

    通过记忆ID删除单个记忆。
    """
    try:
        memory = await memory_service._get_memory()

        # Mem0原生delete方法
        if hasattr(memory.memory, 'delete'):
            memory.memory.delete(memory_id)
            logger.info(f"成功删除记忆: {memory_id}")
            return success_response(msg=f"记忆 {memory_id} 已删除")
        else:
            raise BusinessException("当前Mem0版本不支持delete方法", ResponseCode.NOT_IMPLEMENTED)

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"删除记忆失败: {e}")
        raise BusinessException(f"删除记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.delete("/v1/memory", response_model=UnifiedResponse)
async def delete_all_memories(
    user_id: Optional[str] = Query(None, description="用户ID"),
    agent_id: Optional[str] = Query(None, description="智能体ID"),
    run_id: Optional[str] = Query(None, description="会话ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除所有记忆 (Mem0: memory.delete_all())

    删除指定条件的所有记忆。危险操作，需要确认。
    """
    # 如果没有指定任何条件，使用当前用户（防止误删所有数据）
    if not user_id and not agent_id and not run_id:
        user_id = current_user.get("username", "system")

    try:
        memory = await memory_service._get_memory()
        success = await memory.delete_all_memories(
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id
        )
        if success:
            logger.info(f"成功删除记忆: user_id={user_id}, agent_id={agent_id}, run_id={run_id}")
            return success_response(msg="记忆删除成功")
        else:
            raise BusinessException("删除记忆失败", ResponseCode.INTERNAL_ERROR)
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"删除所有记忆失败: {e}")
        raise BusinessException(f"删除所有记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/memory/{memory_id}/history", response_model=UnifiedResponse)
async def get_memory_history(
    memory_id: str = Path(..., description="记忆ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取记忆历史 (Mem0: memory.history())

    获取指定记忆的历史版本记录。
    """
    try:
        memory = await memory_service._get_memory()

        # Mem0原生history方法
        if hasattr(memory.memory, 'history'):
            history = memory.memory.history(memory_id)
            return success_response(data=history)
        else:
            raise BusinessException("当前Mem0版本不支持history方法", ResponseCode.NOT_IMPLEMENTED)

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取记忆历史失败: {e}")
        raise BusinessException(f"获取记忆历史失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.post("/v1/memory/reset", response_model=UnifiedResponse)
async def reset_memory(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    重置记忆系统 (Mem0: memory.reset())

    删除所有记忆并重置系统。极其危险的操作！
    """
    try:
        memory = await memory_service._get_memory()

        # 确保只有管理员可以执行
        if not current_user.get("is_admin", False):
            raise BusinessException("只有管理员可以重置记忆系统", ResponseCode.FORBIDDEN)

        # 调用reset方法
        await memory.reset()
        logger.warning(f"记忆系统已被重置: user={current_user.get('username')}")
        return success_response(msg="记忆系统已重置")

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"重置记忆系统失败: {e}")
        raise BusinessException(f"重置记忆系统失败: {str(e)}", ResponseCode.INTERNAL_ERROR)