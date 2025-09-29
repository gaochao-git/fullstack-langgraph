"""智能运维助手图定义"""

from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from .configuration import INIT_AGENT_CONFIG
from .llm import get_llm_config
from .prompts import get_system_prompt_async
from .tools import get_diagnostic_tools
from src.apps.agent.llm_agents.hooks import create_monitor_hook
from src.apps.agent.llm_agents.decorators import agent
from src.shared.core.logging import get_logger
from src.apps.agent.llm_agents.state_schemas import DiagnosticAgentState  # 导入自定义状态

logger = get_logger(__name__)


@agent(**INIT_AGENT_CONFIG)
async def create_diagnostic_agent(config: RunnableConfig):
    """创建诊断智能体 - 默认使用多智能体架构"""
    from src.apps.agent.checkpoint_factory import get_checkpointer
    
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
    
    # 记录请求信息（DEBUG级别）
    logger.debug(f"[Agent创建] agent_id: {agent_id}")
    logger.debug(f"[Agent创建] LLM配置: {llm.__class__.__name__}, model={getattr(llm, 'model_name', 'unknown')}")
    logger.debug(f"[Agent创建] 工具数量: {len(tools)}, 工具列表: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]}")
    logger.debug(f"[Agent创建] 系统提示词: {system_prompt[:100] if system_prompt else 'N/A'}...")
    
    # 创建消息监控 hook
    monitor_hook = create_monitor_hook(llm_config)
    
    # 获取 checkpointer
    checkpointer = await get_checkpointer()
    
    # 使用增强的 React Agent - 保持完全兼容性
    logger.info(f"[Agent创建] 使用增强的诊断智能体")
    from .enhanced_react_agent import create_enhanced_react_agent
    return create_enhanced_react_agent(llm, tools, checkpointer, monitor_hook)

