"""通用Agent工作流图定义

简化版本，与diagnostic_agent一致的实现方式
"""

from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from .prompts import get_system_prompt
from .configuration import Configuration
from .state import AgentState
from .utils import compile_graph_with_checkpointer
from .tools import get_generic_agent_tools
from src.apps.agent.llm_agents.hooks import create_monitor_hook
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


def create_main_graph():
    """创建主图 - 使用create_react_agent方式"""
    
    async def create_agent(state: AgentState, config: RunnableConfig):
        """创建并运行Agent"""
        # 参数验证
        configurable = config.get("configurable", {}) if config else {}
        agent_id = configurable.get("agent_id")
        if not agent_id: raise ValueError("配置中缺少必需的agent_id参数")
        
        # 获取配置
        configuration = Configuration.from_runnable_config(config)
        llm_config = configuration.get_llm_config()
        
        # 在图中创建LLM实例
        llm = ChatOpenAI(**llm_config)
        
        # 获取工具和提示词
        tools = await get_generic_agent_tools(agent_id)
        system_prompt = get_system_prompt(agent_id)  # 直接调用，让异常自然传播
        
        # 记录请求信息（DEBUG级别）
        logger.debug(f"[Agent请求] agent_id: {agent_id}")
        logger.debug(f"[Agent请求] LLM配置: {llm.__class__.__name__}, model={getattr(llm, 'model_name', 'unknown')}")
        logger.debug(f"[Agent请求] 工具数量: {len(tools)}, 工具列表: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]}")
        logger.debug(f"[Agent请求] 系统提示词: {system_prompt[:100] if system_prompt else 'N/A'}...")
        
        # 创建消息监控 hook，传入 llm_config
        monitor_hook = create_monitor_hook(llm_config)
        
        # 创建并执行智能体
        agent = create_react_agent(
            model=llm, 
            tools=tools, 
            prompt=system_prompt,
            pre_model_hook=monitor_hook
        )
        response = await agent.ainvoke(state, config)
        
        # 记录响应信息（DEBUG级别）
        logger.debug(f"[Agent响应] agent_id: {agent_id}, response: {response}")
        
        return response
    
    # 创建状态图
    builder = StateGraph(AgentState, config_schema=Configuration)
    builder.add_node("agent", create_agent)
    builder.set_entry_point("agent")
    builder.set_finish_point("agent")
    
    return builder


def create_graph():
    """创建并编译图"""
    builder = create_main_graph()
    return compile_graph_with_checkpointer(builder)


# 创建默认图实例
graph = create_graph()

# 导出builder用于动态编译
builder = create_main_graph()