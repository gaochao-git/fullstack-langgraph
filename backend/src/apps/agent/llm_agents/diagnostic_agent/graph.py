"""
诊断智能体图定义
集成：记忆管理 + 子智能体 + 工具调用
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from sqlalchemy import select

from .configuration import INIT_AGENT_CONFIG
from .llm import get_llm_config
from .prompts import get_system_prompt_async
from .tools import get_diagnostic_tools
from .sub_agents import create_simplified_sub_agent_task_tool
from .memory_hooks import create_memory_hooks
from src.apps.agent.llm_agents.decorators import agent
from src.apps.agent.checkpoint_factory import get_checkpointer
from src.apps.agent.models import AgentConfig
from src.shared.core.logging import get_logger
from src.shared.db.config import get_sync_db

logger = get_logger(__name__)


def _get_memory_config(agent_id: str) -> dict:
    """获取智能体的记忆配置"""
    try:
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            result = db.execute(stmt)
            agent_config = result.scalar_one_or_none()

            if agent_config and agent_config.memory_info:
                logger.info(f"✅ 获取到智能体记忆配置: {agent_config.memory_info}")
                return agent_config.memory_info
            else:
                logger.info(f"智能体 {agent_id} 使用默认记忆配置")
                return {
                    "enable_memory": True,
                    "memory_search_limit": 3,
                    "memory_distance_threshold": 0.5
                }
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"无法获取智能体记忆配置，使用默认值: {e}")
        return {
            "enable_memory": True,
            "memory_search_limit": 3,
            "memory_distance_threshold": 0.5
        }


@agent(**INIT_AGENT_CONFIG)
async def create_diagnostic_agent(config: RunnableConfig):
    """
    创建诊断智能体

    功能：
    - 三层记忆管理（Mem0）
    - 子智能体任务分发
    - 工具调用（系统 + MCP）
    """
    # 内置智能体使用文件中定义的常量
    agent_id = INIT_AGENT_CONFIG["agent_id"]

    # 获取大模型配置
    selected_model = config.get("configurable", {}).get("selected_model") if config else None
    llm_config = get_llm_config(agent_id, selected_model)

    # 创建LLM实例
    llm = ChatOpenAI(**llm_config)

    # 获取工具和提示词
    tools = await get_diagnostic_tools(agent_id)
    system_prompt = await get_system_prompt_async(agent_id)

    # 获取checkpointer
    checkpointer = await get_checkpointer()

    # 获取记忆配置
    memory_config = _get_memory_config(agent_id)

    # 创建记忆hooks
    pre_hook, post_hook = create_memory_hooks(memory_config)

    # 创建子智能体任务工具
    sub_agent_task_tool = create_simplified_sub_agent_task_tool(
        tools=tools,
        main_prompt=system_prompt,
        model=llm
    )

    # 合并所有工具
    all_tools = tools + [sub_agent_task_tool]

    # 使用 create_react_agent 创建图（使用默认的 MessagesState）
    graph = create_react_agent(
        model=llm,
        tools=all_tools,
        checkpointer=checkpointer,
        pre_model_hook=pre_hook,
        post_model_hook=post_hook,
    )

    logger.info(f"✅ 诊断Agent已创建 (记忆: {memory_config.get('enable_memory', True)})")

    return graph

