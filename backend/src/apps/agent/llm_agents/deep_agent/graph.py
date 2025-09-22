"""
Deep Agent 图定义 - 基于 DeepAgents 的实现
"""
from typing import Sequence, Union, Callable, Any, Optional, List
from langchain_core.tools import BaseTool
from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.types import Checkpointer

from .state import DeepAgentState
from .tools import write_todos, write_file, read_file, ls, edit_file
from .prompts import BASE_PROMPT
from .sub_agent import create_task_tool, SubAgentConfig
from ..hooks import create_monitor_hook
from ..agent_utils import get_llm_config_for_agent, get_tools_config_from_db, get_system_tools_map
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


async def create_deep_agent(config: RunnableConfig):
    """
    创建 Deep Agent - 兼容现有系统的实现
    
    通过配置可以实现不同功能：
    - 故障诊断：配置诊断工具和提示词
    - 性能分析：配置性能工具和提示词
    - 其他场景：根据需要配置
    """
    from src.apps.agent.checkpoint_factory import get_checkpointer
    
    # 获取配置
    configurable = config.get("configurable", {}) if config else {}
    agent_id = configurable.get("agent_id")
    if not agent_id:
        raise ValueError("配置中缺少必需的 agent_id 参数")
    
    # 获取 LLM 配置（复用现有系统）
    selected_model = configurable.get("selected_model")
    llm_config = get_llm_config_for_agent(agent_id, selected_model)
    
    # 创建 LLM 实例
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(**llm_config)
    
    # 获取工具配置（复用现有系统）
    tools_config = get_tools_config_from_db(agent_id)
    system_tools_config = tools_config.get('system_tools', [])
    
    # 加载系统工具
    system_tools_map = get_system_tools_map()
    custom_tools = []
    for tool_name in system_tools_config:
        if tool_name in system_tools_map:
            custom_tools.append(system_tools_map[tool_name])
            logger.debug(f"加载系统工具: {tool_name}")
    
    # Deep Agent 内置工具
    builtin_tools = [write_todos, write_file, read_file, ls, edit_file]
    
    # 创建任务工具（简化的子代理）
    sub_agents = configurable.get("sub_agents", [])
    task_tool = create_task_tool(sub_agents)
    
    # 合并所有工具
    all_tools = builtin_tools + custom_tools + [task_tool]
    
    # 获取用户指令（从数据库或配置）
    instructions = configurable.get("instructions", "")
    if not instructions:
        # 尝试从数据库获取
        try:
            from ..agent_utils import get_prompt_config
            from src.shared.db.config import get_sync_db
            db_gen = get_sync_db()
            db = next(db_gen)
            try:
                prompt_config = get_prompt_config(agent_id, db)
                instructions = prompt_config.get("system_prompt", "")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"获取提示词失败: {e}")
            instructions = "你是一个智能助手。"
    
    # 组合提示词（用户指令 + Deep Agent 基础提示）
    full_prompt = instructions + "\n\n" + BASE_PROMPT
    
    # 创建消息监控 hook
    monitor_hook = create_monitor_hook(llm_config)
    
    # 获取 checkpointer
    checkpointer = await get_checkpointer()
    
    # 记录信息
    logger.debug(f"[Deep Agent 创建] agent_id: {agent_id}")
    logger.debug(f"[Deep Agent 创建] 工具数量: {len(all_tools)}")
    logger.debug(f"[Deep Agent 创建] 工具列表: {[t.name if hasattr(t, 'name') else str(t) for t in all_tools]}")
    
    # 创建 React Agent（与 DeepAgents 一致）
    return create_react_agent(
        model=llm,
        tools=all_tools,
        prompt=full_prompt,
        state_schema=DeepAgentState,
        pre_model_hook=monitor_hook,
        checkpointer=checkpointer,
        name=f"{agent_id}-deep-agent"
    )