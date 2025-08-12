"""通用Agent工作流图定义

简化版本，与diagnostic_agent一致的实现方式
"""

from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig
from .prompts import get_system_prompt
from .configuration import Configuration
from .state import AgentState
from .utils import compile_graph_with_checkpointer
from .tools import get_generic_agent_tools
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


def create_main_graph():
    """创建主图 - 使用create_react_agent方式"""
    
    def get_llm_from_config(config: RunnableConfig):
        """从配置获取LLM实例"""
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(
            model_name=configurable.model_name,
            temperature=configurable.model_temperature
        )
    
    async def create_agent(state: AgentState, config: RunnableConfig):
        """创建并运行Agent"""
        configurable = config.get("configurable", {}) if config else {}
        # 获取agent_id，必须存在，不使用默认值
        agent_id = configurable.get("agent_id")
        if not agent_id: raise RuntimeError("配置中缺少必需的agent_id参数")
        logger.info(f"完整智能体配置: {dict(config) if config else 'None'}")
        
        # 获取LLM实例
        llm = get_llm_from_config(config)
        
        # 获取配置实例并获取工具
        agent_config = Configuration.from_runnable_config(config)
        tools = await get_generic_agent_tools(agent_id)
        
        # 获取系统提示词（必须从数据库获取）
        try:
            system_prompt = get_system_prompt(agent_id)
            logger.info(f"成功获取智能体 '{agent_id}' 的系统提示词")
        except ValueError as e:
            logger.error(f"获取智能体系统提示词失败: {e}")
            # 抛出异常，让上层处理，不允许使用空提示词运行
            raise RuntimeError(f"智能体 '{agent_id}' 配置错误: {e}")
        
        # 创建ReAct agent
        agent = create_react_agent(
            model=llm, 
            tools=tools, 
            prompt=system_prompt
        )
        
        # 执行agent
        return await agent.ainvoke(state, config)
    
    # 创建状态图
    builder = StateGraph(AgentState, config_schema=Configuration)
    builder.add_node("agent", create_agent)
    builder.set_entry_point("agent")
    builder.set_finish_point("agent")
    
    return builder


def create_graph():
    """创建并编译图"""
    workflow = create_main_graph()
    return compile_graph_with_checkpointer(workflow)


# 创建默认图实例
graph = create_graph()

# 导出builder用于动态编译
builder = create_main_graph()