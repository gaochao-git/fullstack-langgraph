"""
Mem0记忆管理Hooks
提供pre_model_hook和post_model_hook用于记忆检索和保存
"""
from typing import Dict
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
import asyncio
import threading

from src.apps.agent.memory_factory import get_enterprise_memory
from src.apps.agent.memory_utils import (
    search_combined_memory,
    build_layered_context,
    save_layered_memories
)
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


async def retrieve_memory_hook(state: Dict, config: RunnableConfig, memory_config: Dict) -> Dict:
    """
    pre_model_hook: LLM调用前检索记忆

    功能：
    1. 从用户消息中提取查询
    2. 并行搜索三层记忆（用户全局/智能体全局/用户-智能体）
    3. 构建分层上下文
    4. 注入到系统消息
    """
    # 获取记忆实例
    memory = await _get_memory()
    if not memory:
        return state

    try:
        # 获取最新的用户消息
        user_message = state["messages"][-1].content if state["messages"] else ""

        # 从配置中获取用户ID和智能体ID
        configurable = config.get("configurable", {})
        user_id = configurable.get("user_name") or configurable.get("user_id") or "default_user"
        agent_id = configurable.get("agent_id")

        if not agent_id:
            from src.shared.core.exceptions import BusinessException, ResponseCode
            raise BusinessException("agent_id is required in configurable", ResponseCode.PARAM_ERROR)

        logger.info(f"🔍 [PRE-HOOK] 开始记忆检索: user_id={user_id}, agent_id={agent_id}")

        # 从配置中获取记忆搜索参数
        search_limit = memory_config.get('memory_search_limit', 3)
        distance_threshold = memory_config.get('memory_distance_threshold', None)

        # 并行检索三层记忆
        combined_memories = await search_combined_memory(
            memory=memory,
            query=user_message,
            user_id=user_id,
            agent_id=agent_id,
            limit_per_level=search_limit,
            threshold=distance_threshold
        )

        # 如果找到相关记忆，构建增强上下文
        if any(memories for memories in combined_memories.values()):
            enhanced_prompt = build_layered_context(combined_memories, max_per_layer=3)

            # 注入到消息开头（只在第一次注入，避免重复）
            if not any(isinstance(msg, SystemMessage) and "📚 相关记忆" in msg.content
                      for msg in state["messages"]):
                state["messages"].insert(0, SystemMessage(content=enhanced_prompt))
                logger.info(f"✅ [PRE-HOOK] 已注入多层记忆上下文")

        # 统计记忆数量
        total_memories = sum(len(v) for v in combined_memories.values())
        logger.info(f"✅ [PRE-HOOK] 记忆检索完成: 共 {total_memories} 条")

    except Exception as e:
        logger.error(f"❌ [PRE-HOOK] 记忆检索失败: {e}", exc_info=True)

    return state


async def save_memory_hook(state: Dict, config: RunnableConfig, memory_config: Dict) -> Dict:
    """
    post_model_hook: LLM调用后保存记忆

    功能：
    1. 提取对话消息
    2. 分层保存到三层记忆
    3. 后台异步执行，不阻塞主流程
    """
    # 获取记忆实例
    memory = await _get_memory()
    if not memory:
        return state

    try:
        # 获取配置信息
        configurable = config.get("configurable", {})
        user_id = configurable.get("user_name") or configurable.get("user_id") or "default_user"
        agent_id = configurable.get("agent_id")

        if not agent_id:
            from src.shared.core.exceptions import BusinessException, ResponseCode
            raise BusinessException("agent_id is required in configurable", ResponseCode.PARAM_ERROR)

        logger.info(f"💾 [POST-HOOK] 准备保存记忆: user_id={user_id}, agent_id={agent_id}")

        # 构建对话消息
        conversation_messages = []
        for msg in state["messages"]:
            if hasattr(msg, 'type'):
                if msg.type == "human":
                    conversation_messages.append({"role": "user", "content": msg.content})
                elif msg.type == "ai":
                    conversation_messages.append({"role": "assistant", "content": msg.content})

        if not conversation_messages:
            logger.warning("⚠️ [POST-HOOK] 没有对话消息可保存")
            return state

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
                logger.error(f"❌ [POST-HOOK] 后台保存记忆失败: {e}", exc_info=True)
            finally:
                loop.close()

        thread = threading.Thread(target=start_background_memory_save, daemon=True)
        thread.start()

        logger.info(f"✅ [POST-HOOK] 已启动后台记忆保存任务")

    except Exception as e:
        logger.error(f"❌ [POST-HOOK] 保存记忆失败: {e}", exc_info=True)

    return state


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


def create_memory_hooks(memory_config: Dict):
    """
    创建记忆hooks的工厂函数

    Args:
        memory_config: 记忆配置，包含enable_memory, memory_search_limit等

    Returns:
        (pre_hook, post_hook) 或 (None, None)
    """
    if not memory_config.get("enable_memory", True):
        return None, None

    # 使用闭包捕获memory_config
    async def pre_hook(state: Dict, config: RunnableConfig) -> Dict:
        return await retrieve_memory_hook(state, config, memory_config)

    async def post_hook(state: Dict, config: RunnableConfig) -> Dict:
        return await save_memory_hook(state, config, memory_config)

    return pre_hook, post_hook
