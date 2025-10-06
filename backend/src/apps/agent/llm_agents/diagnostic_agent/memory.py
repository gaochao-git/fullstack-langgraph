"""
Mem0记忆管理
提供记忆检索和保存功能
"""
from typing import Dict, Optional
from langchain_core.runnables import RunnableConfig
from sqlalchemy import select
import asyncio
import threading

from src.apps.agent.memory_factory import get_enterprise_memory
from src.apps.agent.memory_utils import (
    search_combined_memory,
    build_layered_context,
    save_layered_memories
)
from src.apps.agent.models import AgentConfig
from src.shared.db.config import get_async_db_context
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 全局记忆实例缓存
_memory_instance = None


async def _get_memory():
    """获取全局记忆实例（懒加载）"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = await get_enterprise_memory()
    return _memory_instance


async def _get_memory_config(agent_id: str) -> dict:
    """获取智能体的记忆配置"""
    try:
        async with get_async_db_context() as db:
            stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            result = await db.execute(stmt)
            agent_config = result.scalar_one_or_none()

            if agent_config and agent_config.memory_info:
                return agent_config.memory_info
            else:
                return {"enable_memory": True}
    except Exception as e:
        logger.warning(f"获取记忆配置失败，使用默认值: {e}")
        return {"enable_memory": True}


async def retrieve_memory_context(query: str, config: Dict, agent_id: str) -> Optional[str]:
    """
    检索记忆上下文（公共接口）

    Args:
        query: 用户查询
        config: 运行配置
        agent_id: 智能体ID

    Returns:
        记忆上下文字符串，如果没有记忆或未启用返回None
    """
    try:
        # 获取记忆配置
        memory_config = await _get_memory_config(agent_id)

        # 如果未启用记忆，直接返回
        if not memory_config.get("enable_memory", True):
            return None

        # 检索记忆
        return await _retrieve_memory_for_query(query, config, memory_config)
    except Exception as e:
        logger.error(f"检索记忆失败: {e}", exc_info=True)
        return None


async def save_memory_context(final_state: Dict, config: Dict, agent_id: str) -> None:
    """
    保存记忆上下文（公共接口）

    Args:
        final_state: 图的最终状态
        config: 运行配置
        agent_id: 智能体ID
    """
    try:
        # 获取记忆配置
        memory_config = await _get_memory_config(agent_id)

        # 如果未启用记忆，直接返回
        if not memory_config.get("enable_memory", True):
            return

        # 保存记忆
        await _save_memory_after_graph(final_state, config, memory_config)
    except Exception as e:
        logger.error(f"保存记忆失败: {e}", exc_info=True)


async def _retrieve_memory_for_query(query: str, config: RunnableConfig, memory_config: Dict) -> Optional[str]:
    """
    基于查询检索记忆并返回上下文字符串

    Args:
        query: 用户查询
        config: 运行配置（包含user_id、agent_id等）
        memory_config: 记忆配置

    Returns:
        记忆上下文字符串，如果没有记忆返回None
    """
    memory = await _get_memory()
    if not memory:
        return None

    try:
        # 从配置中获取用户ID和智能体ID
        configurable = config.get("configurable", {})
        user_id = configurable.get("user_name") or configurable.get("user_id") or "default_user"
        agent_id = configurable.get("agent_id")

        if not agent_id:
            logger.warning("缺少agent_id，跳过记忆检索")
            return None

        logger.info(f"🔍 [图执行前] 检索记忆: query='{query[:50]}...', user_id={user_id}, agent_id={agent_id}")

        # 从配置中获取记忆搜索参数
        search_limit = memory_config.get('memory_search_limit', 3)
        distance_threshold = memory_config.get('memory_distance_threshold', None)

        # 并行检索三层记忆（基于语义搜索）
        combined_memories = await search_combined_memory(
            memory=memory,
            query=query,
            user_id=user_id,
            agent_id=agent_id,
            limit_per_level=search_limit,
            threshold=distance_threshold
        )

        # 如果找到相关记忆，构建上下文
        if any(memories for memories in combined_memories.values()):
            memory_context = build_layered_context(combined_memories, max_per_layer=3)
            total_memories = sum(len(v) for v in combined_memories.values())
            logger.info(f"✅ [图执行前] 检索到 {total_memories} 条历史记忆")
            return memory_context
        else:
            logger.info("ℹ️ [图执行前] 未找到相关历史记忆")
            return None

    except Exception as e:
        logger.error(f"❌ [图执行前] 记忆检索失败: {e}", exc_info=True)
        return None


async def retrieve_memory_hook(state: Dict, config: RunnableConfig, memory_config: Dict) -> Dict:
    """
    pre_model_hook: 在第一次LLM调用前检索记忆并注入到消息中

    Args:
        state: 图状态（包含messages）
        config: 运行配置
        memory_config: 记忆配置

    Returns:
        更新后的state
    """
    # 检查是否已检索过记忆（避免重复）
    from langchain_core.messages import SystemMessage
    has_memory = any(isinstance(msg, SystemMessage) and "📚 相关记忆" in msg.content
                     for msg in state.get("messages", []))
    if has_memory:
        return state

    memory = await _get_memory()
    if not memory:
        return state

    try:
        # 从配置中获取用户ID和智能体ID
        configurable = config.get("configurable", {})
        user_id = configurable.get("user_name") or configurable.get("user_id") or "default_user"
        agent_id = configurable.get("agent_id")

        if not agent_id:
            return state

        # 获取最新的用户消息作为查询
        messages = state.get("messages", [])
        if not messages:
            return state

        query = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        logger.info(f"🔍 [PRE-HOOK] 检索记忆: query='{query[:50]}...', user_id={user_id}, agent_id={agent_id}")

        # 从配置中获取记忆搜索参数
        search_limit = memory_config.get('memory_search_limit', 3)
        distance_threshold = memory_config.get('memory_distance_threshold', None)

        # 并行检索三层记忆（基于语义搜索）
        combined_memories = await search_combined_memory(
            memory=memory,
            query=query,
            user_id=user_id,
            agent_id=agent_id,
            limit_per_level=search_limit,
            threshold=distance_threshold
        )

        # 如果找到相关记忆，构建上下文并注入
        if any(memories for memories in combined_memories.values()):
            memory_context = build_layered_context(combined_memories, max_per_layer=3)
            total_memories = sum(len(v) for v in combined_memories.values())

            # 注入到消息开头
            system_message = SystemMessage(content=memory_context)
            state["messages"].insert(0, system_message)

            logger.info(f"✅ [PRE-HOOK] 检索到 {total_memories} 条历史记忆并注入")
        else:
            logger.info("ℹ️ [PRE-HOOK] 未找到相关历史记忆")

    except Exception as e:
        logger.error(f"❌ [PRE-HOOK] 记忆检索失败: {e}", exc_info=True)

    return state


def create_memory_hooks(memory_config: Dict):
    """创建记忆hooks"""
    if not memory_config.get("enable_memory", True):
        return None, None

    async def pre_hook(state: Dict, config: RunnableConfig) -> Dict:
        return await retrieve_memory_hook(state, config, memory_config)

    async def post_hook(state: Dict, config: RunnableConfig) -> Dict:
        return await save_memory_after_graph(state, config, memory_config)

    return pre_hook, post_hook


async def _save_memory_after_graph(state: Dict, config: RunnableConfig, memory_config: Dict) -> None:
    """
    在图执行完成后保存记忆

    Args:
        state: 图的最终状态（包含完整对话消息）
        config: 运行配置
        memory_config: 记忆配置
    """
    memory = await _get_memory()
    if not memory:
        return

    try:
        # 获取配置信息
        configurable = config.get("configurable", {})
        user_id = configurable.get("user_name") or configurable.get("user_id") or "default_user"
        agent_id = configurable.get("agent_id")

        if not agent_id:
            logger.warning("缺少agent_id，跳过记忆保存")
            return

        logger.info(f"💾 [图完成后] 准备保存记忆: user_id={user_id}, agent_id={agent_id}")

        # 只保存最后一轮对话（最新的 user + assistant 消息对）
        messages = state.get("messages", [])
        if not messages:
            logger.warning("⚠️ [图完成后] 没有消息可保存")
            return

        # 从后往前找最后一轮对话
        last_user_msg = None
        last_ai_msg = None

        for msg in reversed(messages):
            if hasattr(msg, 'type'):
                if msg.type == "ai" and last_ai_msg is None:
                    last_ai_msg = {"role": "assistant", "content": msg.content}
                elif msg.type == "human" and last_user_msg is None:
                    last_user_msg = {"role": "user", "content": msg.content}
                    # 找到一对完整的对话，退出
                    if last_ai_msg:
                        break

        if not last_user_msg or not last_ai_msg:
            logger.warning("⚠️ [图完成后] 没有完整的对话轮次可保存")
            return

        # 构建最后一轮对话
        conversation_messages = [last_user_msg, last_ai_msg]
        logger.info(f"📝 [图完成后] 提取最后一轮对话: user='{last_user_msg['content'][:50]}...'")

        # 后台异步保存记忆（不阻塞主流程）
        def start_background_memory_save():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_save_memories_async(
                    memory,
                    conversation_messages,
                    user_id,
                    agent_id
                ))
            except Exception as e:
                logger.error(f"❌ [图完成后] 后台保存记忆失败: {e}", exc_info=True)
            finally:
                loop.close()

        thread = threading.Thread(target=start_background_memory_save, daemon=True)
        thread.start()

        logger.info(f"✅ [图完成后] 已启动后台记忆保存任务")

    except Exception as e:
        logger.error(f"❌ [图完成后] 保存记忆失败: {e}", exc_info=True)


async def _save_memories_async(memory, conversation_messages, user_id, agent_id):
    """异步保存记忆到Mem0三层"""
    try:
        saved_memories = await save_layered_memories(
            memory=memory,
            messages=conversation_messages,
            user_id=user_id,
            agent_id=agent_id
        )

        # 记录保存结果
        for memory_type, memory_ids in saved_memories.items():
            if memory_ids:
                logger.info(f"✅ 已保存{memory_type}记忆: {memory_ids}")

    except Exception as e:
        logger.error(f"❌ 分层保存记忆失败: {e}", exc_info=True)
