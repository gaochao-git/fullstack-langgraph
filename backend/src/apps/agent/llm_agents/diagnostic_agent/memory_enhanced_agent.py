"""
集成三层记忆的增强诊断Agent V2

改进内容：
1. 支持分层记忆检索（组织/用户全局/智能体全局/用户-智能体）
2. 智能组合多层记忆构建上下文
3. 分层保存记忆到不同层级
4. 优化记忆注入策略
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
import json

from src.apps.agent.memory_factory import get_enterprise_memory
from src.apps.agent.memory_utils import (
    search_combined_memory,
    build_layered_context,
    analyze_conversation_for_memory,
    save_layered_memories
)
from src.shared.core.logging import get_logger
from src.shared.db.config import get_sync_db
from .state import DiagnosticState

logger = get_logger(__name__)


class MemoryEnhancedDiagnosticAgent:
    """集成三层记忆的诊断Agent"""

    def __init__(self, llm, tools, checkpointer, memory_config=None):
        self.llm = llm
        self.tools = tools
        self.checkpointer = checkpointer
        self.memory = None
        self.memory_config = memory_config or {}

    async def initialize(self):
        """初始化记忆系统"""
        self.memory = await get_enterprise_memory()

    async def retrieve_context(self, state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
        """从多层记忆中检索相关上下文"""
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

            logger.info(f"🔍 开始多层记忆检索: user_id={user_id}, agent_id={agent_id}, query='{user_message[:50]}...'")

            # 从配置中获取记忆搜索参数
            search_limit = self.memory_config.get('memory_search_limit', 3)  # 每层3条
            distance_threshold = self.memory_config.get('memory_distance_threshold', None)

            # 组合检索多层记忆（使用辅助函数）
            combined_memories = await search_combined_memory(
                memory=self.memory,
                query=user_message,
                user_id=user_id,
                agent_id=agent_id,
                limit_per_level=search_limit,
                threshold=distance_threshold
            )

            # 构建增强的系统提示（使用辅助函数）
            if self._has_relevant_memories(combined_memories):
                enhanced_prompt = build_layered_context(combined_memories, max_per_layer=3)
                # 将增强提示插入到消息列表开头
                state["messages"].insert(0, SystemMessage(content=enhanced_prompt))
                logger.info(f"✅ 已注入多层记忆上下文到系统提示")

            # 保存记忆上下文到状态供后续使用
            state["memory_context"] = combined_memories

            # 统计记忆数量
            total_memories = sum(len(v) for v in combined_memories.values())
            logger.info(f"✅ 记忆检索完成: 共找到 {total_memories} 条记忆")

        except Exception as e:
            logger.error(f"检索记忆上下文失败: {e}", exc_info=True)

        return state

    def _has_relevant_memories(self, combined_memories: Dict[str, List]) -> bool:
        """检查是否有相关记忆"""
        return any(memories for memories in combined_memories.values())


    async def save_diagnosis_result(self, state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
        """分层保存诊断结果到长期记忆"""
        try:
            # 获取配置信息
            configurable = config.get("configurable", {})

            user_id = configurable.get("user_name") or configurable.get("user_id") or "default_user"
            agent_id = configurable.get("agent_id")
            if not agent_id:
                from src.shared.core.exceptions import BusinessException, ResponseCode
                raise BusinessException("agent_id is required in configurable", ResponseCode.PARAM_ERROR)

            logger.info(f"💾 开始分层保存记忆: user_id={user_id}, agent_id={agent_id}")

            # 构建对话消息
            conversation_messages = []
            for msg in state["messages"]:
                if hasattr(msg, 'type'):
                    if msg.type == "human":
                        conversation_messages.append({"role": "user", "content": msg.content})
                    elif msg.type == "ai":
                        conversation_messages.append({"role": "assistant", "content": msg.content})

            if not conversation_messages:
                logger.warning("没有对话消息可保存")
                return state

            # 使用后台任务异步保存记忆
            import asyncio
            import threading

            def start_background_memory_save():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._save_memories_layered(
                        conversation_messages,
                        user_id,
                        agent_id,
                        state
                    ))
                except Exception as e:
                    logger.error(f"后台保存记忆失败: {e}", exc_info=True)
                finally:
                    loop.close()

            thread = threading.Thread(target=start_background_memory_save, daemon=True)
            thread.start()

            logger.info(f"✅ 已启动后台记忆保存任务")

        except Exception as e:
            logger.error(f"保存诊断结果失败: {e}", exc_info=True)

        return state

    async def _save_memories_layered(
        self,
        conversation_messages: List[Dict],
        user_id: str,
        agent_id: str,
        state: DiagnosticState
    ):
        """分层保存记忆"""
        try:
            # 使用辅助函数分析对话内容
            analysis = analyze_conversation_for_memory(conversation_messages)

            # 添加状态相关的分析
            if state.get("diagnosis_result"):
                analysis["has_problem_solution"] = True
                analysis["problem_type"] = self._extract_problem_type(state)

            # 使用辅助函数分层保存记忆
            saved_memories = await save_layered_memories(
                memory=self.memory,
                messages=conversation_messages,
                user_id=user_id,
                agent_id=agent_id,
                analysis=analysis
            )

            # 记录保存结果
            for memory_type, memory_ids in saved_memories.items():
                if memory_ids:
                    logger.info(f"✅ 已保存{memory_type}记忆: {memory_ids}")

        except Exception as e:
            logger.error(f"分层保存记忆失败: {e}", exc_info=True)

    def _contains_user_profile_info(self, messages: List[Dict]) -> bool:
        """检测是否包含用户档案信息"""
        user_profile_keywords = [
            "我是", "我叫", "我负责", "我的专长", "我擅长",
            "我的职位", "我的部门", "我的联系方式"
        ]

        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                if any(keyword in content for keyword in user_profile_keywords):
                    return True
        return False

    def _contains_valuable_experience(self, messages: List[Dict], state: DiagnosticState) -> bool:
        """检测是否包含有价值的诊断经验"""
        # 如果问题已解决，认为是有价值的经验
        if state.get("resolved"):
            return True

        # 如果包含具体的解决方案
        solution_keywords = ["解决", "修复", "优化", "已恢复", "正常了"]
        for msg in messages:
            if msg.get("role") == "assistant":
                content = msg.get("content", "").lower()
                if any(keyword in content for keyword in solution_keywords):
                    return True

        return False

    def _extract_problem_type(self, state: DiagnosticState) -> str:
        """提取问题类型"""
        user_message = ""
        for msg in state["messages"]:
            if hasattr(msg, 'type') and msg.type == "human":
                user_message = msg.content.lower()
                break

        problem_types = {
            "cpu": ["cpu", "处理器"],
            "memory": ["内存", "memory"],
            "disk": ["磁盘", "disk", "存储"],
            "network": ["网络", "network", "连接"],
            "database": ["数据库", "database", "mysql", "postgresql"],
            "service": ["服务", "service", "进程"],
        }

        for ptype, keywords in problem_types.items():
            if any(kw in user_message for kw in keywords):
                return ptype

        return "general"

    def create_graph(self):
        """创建集成三层记忆的诊断图"""
        # 创建工具节点
        tool_node = ToolNode(self.tools)

        # 创建状态图
        workflow = StateGraph(DiagnosticState)

        # 添加节点
        workflow.add_node("retrieve_memory", self.retrieve_context)  # 1. 检索记忆
        workflow.add_node("agent", self.call_model)                  # 2. LLM推理
        workflow.add_node("tools", tool_node)                        # 3. 工具执行
        workflow.add_node("save_memory", self.save_diagnosis_result) # 4. 保存记忆

        # 设置入口
        workflow.add_edge(START, "retrieve_memory")
        workflow.add_edge("retrieve_memory", "agent")

        # 条件路由：LLM → 工具 或 保存记忆
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "tools",
                "end": "save_memory"
            }
        )

        # 工具执行后回到LLM
        workflow.add_edge("tools", "agent")

        # 保存记忆后结束
        workflow.add_edge("save_memory", END)

        # 编译图
        return workflow.compile(checkpointer=self.checkpointer)

    async def call_model(self, state: DiagnosticState, config: RunnableConfig):
        """调用LLM"""
        messages = state["messages"]
        response = await self.llm.ainvoke(messages, config=config)
        return {"messages": [response]}

    def should_continue(self, state: DiagnosticState):
        """判断是否需要调用工具"""
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        return "end"


async def create_memory_enhanced_diagnostic_agent(llm, tools, checkpointer, agent_id="diagnostic_agent"):
    """创建集成三层记忆的诊断Agent"""
    # 获取智能体的memory_info配置
    memory_config = {}
    try:
        from src.apps.agent.service.agent_config_service import AgentConfigService
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            # 直接查询数据库获取 agent 配置
            from sqlalchemy import select
            from src.apps.agent.models import AgentConfig

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

    # 检查是否启用记忆
    if not memory_config.get("enable_memory", True):
        logger.info(f"智能体 {agent_id} 未启用记忆功能")
        # 返回不带记忆的简单图
        from .enhanced_react_agent import create_enhanced_react_agent
        return create_enhanced_react_agent(llm, tools, checkpointer, None)

    # 创建带记忆的智能体
    agent = MemoryEnhancedDiagnosticAgent(llm, tools, checkpointer, memory_config)
    await agent.initialize()
    return agent.create_graph()
