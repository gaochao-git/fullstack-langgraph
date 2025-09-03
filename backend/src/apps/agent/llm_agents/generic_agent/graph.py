"""通用Agent工作流图定义

简化版本，直接使用create_react_agent
"""

from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from .prompts import get_system_prompt_async
from .configuration import Configuration
from .tools import get_generic_agent_tools
from src.apps.agent.llm_agents.hooks import create_monitor_hook
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


# 注意：generic_agent 是模板，不要使用 @agent 装饰器注册
# 前端会基于此模板创建自定义 Agent
async def create_generic_agent(config: RunnableConfig, checkpointer=None):
    """创建通用智能体"""
    # 参数验证
    configurable = config.get("configurable", {}) if config else {}
    agent_id = configurable.get("agent_id")
    if not agent_id:
        raise ValueError("配置中缺少必需的agent_id参数")
    
    # 获取配置
    configuration = Configuration.from_runnable_config(config)
    llm_config = configuration.get_llm_config()
    
    # 创建LLM实例
    llm = ChatOpenAI(**llm_config)
    
    # 获取工具和提示词
    tools = await get_generic_agent_tools(agent_id)
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