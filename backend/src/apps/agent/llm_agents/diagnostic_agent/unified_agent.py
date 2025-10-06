"""
统一的诊断Agent实现
集成：记忆管理 + 子智能体 + 工具调用

使用 create_react_agent + hooks 统一实现，替代原来的两个分离实现：
- memory_enhanced_agent.py (有记忆，无子智能体)
- enhanced_react_agent.py (无记忆，有子智能体)
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.store.base import BaseStore
import asyncio
import threading

from src.apps.agent.memory_factory import get_enterprise_memory
from src.apps.agent.memory_utils import (
    search_combined_memory,
    build_layered_context,
    save_layered_memories
)
from src.shared.core.logging import get_logger
from src.shared.db.config import get_sync_db
from .state import DiagnosticState
from .sub_agents import create_simplified_sub_agent_task_tool

logger = get_logger(__name__)


class UnifiedDiagnosticAgent:
    """统一的诊断Agent - 同时支持记忆和子智能体"""

    def __init__(self, llm, tools, checkpointer, memory_config=None):
        self.llm = llm
        self.tools = tools
        self.checkpointer = checkpointer
        self.memory = None
        self.memory_config = memory_config or {}
        self.enable_memory = self.memory_config.get("enable_memory", True)

    async def initialize(self):
        """初始化记忆系统"""
        if self.enable_memory:
            self.memory = await get_enterprise_memory()
            logger.info("✅ Mem0记忆系统已初始化")

    async def retrieve_memory_hook(self, state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
        """
        pre_model_hook: LLM调用前检索记忆

        功能：
        1. 从用户消息中提取查询
        2. 并行搜索三层记忆（用户全局/智能体全局/用户-智能体）
        3. 构建分层上下文
        4. 注入到系统消息
        """
        if not self.enable_memory or not self.memory:
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
            search_limit = self.memory_config.get('memory_search_limit', 3)
            distance_threshold = self.memory_config.get('memory_distance_threshold', None)

            # 并行检索三层记忆
            combined_memories = await search_combined_memory(
                memory=self.memory,
                query=user_message,
                user_id=user_id,
                agent_id=agent_id,
                limit_per_level=search_limit,
                threshold=distance_threshold
            )

            # 如果找到相关记忆，构建增强上下文
            if self._has_relevant_memories(combined_memories):
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

    async def save_memory_hook(self, state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
        """
        post_model_hook: LLM调用后保存记忆

        功能：
        1. 提取对话消息
        2. 分层保存到三层记忆
        3. 后台异步执行，不阻塞主流程
        """
        if not self.enable_memory or not self.memory:
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
                    loop.run_until_complete(self._save_memories_async(
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

    async def _save_memories_async(
        self,
        conversation_messages: List[Dict],
        user_id: str,
        agent_id: str
    ):
        """异步保存记忆到Mem0三层"""
        try:
            saved_memories = await save_layered_memories(
                memory=self.memory,
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

    def _has_relevant_memories(self, combined_memories: Dict[str, List]) -> bool:
        """检查是否有相关记忆"""
        return any(memories for memories in combined_memories.values())

    def create_graph(self, main_prompt: str = "你是一个智能运维助手，负责协调和分配诊断任务。"):
        """
        创建统一的诊断图

        使用 create_react_agent 替代手动 StateGraph：
        - pre_model_hook: 记忆检索
        - post_model_hook: 记忆保存
        - tools: 系统工具 + MCP工具 + 子智能体任务工具
        """
        # 创建子智能体任务工具
        sub_agent_task_tool = create_simplified_sub_agent_task_tool(
            tools=self.tools,
            main_prompt=main_prompt,
            model=self.llm
        )

        # 合并所有工具
        all_tools = self.tools + [sub_agent_task_tool]

        # 使用 create_react_agent 创建图
        # 注意：不指定 state_schema，让 create_react_agent 使用默认的 MessagesState
        graph = create_react_agent(
            model=self.llm,
            tools=all_tools,
            checkpointer=self.checkpointer,
            # 记忆管理hooks
            pre_model_hook=self.retrieve_memory_hook if self.enable_memory else None,
            post_model_hook=self.save_memory_hook if self.enable_memory else None,
        )

        logger.info(f"✅ 统一诊断Agent已创建 (记忆: {self.enable_memory})")
        return graph


async def create_unified_diagnostic_agent(llm, tools, checkpointer, agent_id="diagnostic_agent", system_prompt: str = None):
    """
    创建统一的诊断Agent

    功能：
    - 三层记忆管理（Mem0）
    - 子智能体任务分发
    - 工具调用（系统 + MCP）

    替代：
    - memory_enhanced_agent.py
    - enhanced_react_agent.py
    """
    # 如果没有提供系统提示词，使用默认值
    if system_prompt is None:
        system_prompt = "你是一个智能运维助手，负责协调和分配诊断任务。"
    # 获取智能体的memory_info配置
    memory_config = {}
    try:
        from sqlalchemy import select
        from src.apps.agent.models import AgentConfig

        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            result = db.execute(stmt)
            agent_config = result.scalar_one_or_none()

            if agent_config and agent_config.memory_info:
                memory_config = agent_config.memory_info
                logger.info(f"✅ 获取到智能体记忆配置: {memory_config}")
            else:
                logger.info(f"智能体 {agent_id} 使用默认记忆配置")
                memory_config = {
                    "enable_memory": True,
                    "memory_search_limit": 3,
                    "memory_distance_threshold": 0.5
                }
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"无法获取智能体记忆配置，使用默认值: {e}")
        memory_config = {
            "enable_memory": True,
            "memory_search_limit": 3,
            "memory_distance_threshold": 0.5
        }

    # 创建统一Agent
    agent = UnifiedDiagnosticAgent(llm, tools, checkpointer, memory_config)

    # 初始化记忆系统
    if memory_config.get("enable_memory", True):
        await agent.initialize()

    return agent.create_graph(main_prompt=system_prompt)
