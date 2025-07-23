"""智能运维助手图定义"""

import asyncio
import concurrent.futures
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState
from .utils import compile_graph_with_checkpointer
from .prompts import SYSTEM_PROMPT
from .tools_mcp import get_diagnostic_tools

def create_main_graph(enable_tool_approval: bool = False):
    """创建主图"""
    
    def get_llm_from_config(config: RunnableConfig):
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(
            model_name=configurable.query_generator_model,
            temperature=configurable.model_temperature
        )
    
    async def create_agent_async(state: DiagnosticState, config: RunnableConfig):
        llm = get_llm_from_config(config)
        tools = await get_diagnostic_tools(enable_tool_approval)
        agent = create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)
        return await agent.ainvoke(state, config)
    
    def create_agent(state: DiagnosticState, config: RunnableConfig):
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(create_agent_async(state, config))
            finally:
                loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return executor.submit(run_async).result()
    
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