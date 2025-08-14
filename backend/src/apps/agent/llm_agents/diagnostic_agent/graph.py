"""智能运维助手图定义"""

import logging
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState
from .utils import compile_graph_with_checkpointer
from .prompts import get_system_prompt
from .tools import get_diagnostic_tools
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

def create_main_graph(enable_tool_approval: bool = False):
    """创建主图"""
    
    def get_llm_from_config(config: RunnableConfig):
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(model_name=configurable.query_generator_model, temperature=configurable.model_temperature)
    
    async def create_agent(state: DiagnosticState, config: RunnableConfig):
        # 参数验证
        configurable = config.get("configurable", {}) if config else {}
        agent_id = configurable.get("agent_id")
        if not agent_id:
            raise ValueError("配置中缺少必需的agent_id参数")
        
        # 初始化所有资源
        llm = get_llm_from_config(config)
        tools = await get_diagnostic_tools(agent_id)
        system_prompt = get_system_prompt(agent_id)  # 直接调用，让异常自然传播
        
        # 记录请求信息（DEBUG级别）
        logger.debug(f"[Agent请求] agent_id: {agent_id}")
        logger.debug(f"[Agent请求] LLM配置: {llm.__class__.__name__}, model={getattr(llm, 'model_name', 'unknown')}")
        logger.debug(f"[Agent请求] 工具数量: {len(tools)}, 工具列表: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]}")
        logger.debug(f"[Agent请求] 系统提示词: {system_prompt.messages[0].content if system_prompt.messages else 'N/A'}")
        
        # 创建并执行智能体
        agent = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
        response = await agent.ainvoke(state, config)
        
        # 记录响应信息（DEBUG级别）
        logger.debug(f"[Agent响应] agent_id: {agent_id}, response: {response}")
        
        return response
    
    builder = StateGraph(DiagnosticState, config_schema=Configuration)
    builder.add_node("agent", create_agent)
    builder.set_entry_point("agent")
    builder.set_finish_point("agent")
    
    return builder

def compile_main_graph(enable_tool_approval: bool = False):
    """编译主图"""
    builder = create_main_graph(enable_tool_approval)
    return compile_graph_with_checkpointer(builder)

# 默认导出
graph = compile_main_graph()
builder = create_main_graph()