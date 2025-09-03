"""智能运维助手图定义"""

from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from .configuration import Configuration, INIT_AGENT_CONFIG
from .prompts import get_system_prompt_async
from .tools import get_diagnostic_tools
from src.apps.agent.llm_agents.hooks import create_monitor_hook
from src.apps.agent.llm_agents.decorators import agent
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


@agent(**INIT_AGENT_CONFIG)
async def create_diagnostic_agent(config: RunnableConfig, checkpointer=None):
    """创建诊断智能体"""
    # 内置智能体使用文件中定义的常量
    agent_id = INIT_AGENT_CONFIG["agent_id"]
    
    # 获取配置
    configuration = Configuration.from_runnable_config(config)
    llm_config = configuration.get_llm_config()
    
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
    
    # 直接使用 create_react_agent 创建并返回图
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        pre_model_hook=monitor_hook,
        checkpointer=checkpointer,
        name=f"{agent_id}-agent"
    )

