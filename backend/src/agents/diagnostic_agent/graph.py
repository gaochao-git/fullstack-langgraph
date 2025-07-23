"""
智能运维助手图定义 - 混合工具架构

工具分配策略:
- 系统工具: SOP相关 + 时间工具 (5个)
- MCP工具: SSH + MySQL + Elasticsearch + Zabbix (11个)
- 总计: 16个工具，无重复，各司其职
"""

import os
import logging
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

logger = logging.getLogger(__name__)

# 提示词已迁移到 prompts.py 文件中统一管理

def create_main_graph(enable_tool_approval: bool = True):
    """
    创建主图 - 合并系统工具和MCP工具
    
    Args:
        enable_tool_approval: 是否启用工具审批功能，默认True
    """
    approval_status = "启用工具审批" if enable_tool_approval else "禁用工具审批"
    print(f"📍 创建智能运维助手 (系统工具+MCP工具, {approval_status})")
    
    def get_llm_from_config(config: RunnableConfig):
        """从配置中获取LLM实例"""
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(
            model_name=configurable.query_generator_model,
            temperature=configurable.model_temperature
        )
    
    
    # 创建agent的异步版本
    async def create_agent_with_config_async(state: DiagnosticState, config: RunnableConfig):
        """创建带合并工具配置的agent节点"""
        llm = get_llm_from_config(config)
        
        # 获取合并后的工具
        tools = await get_diagnostic_tools(enable_tool_approval)
        
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=SYSTEM_PROMPT,
        )
        
        # 使用ainvoke
        result = await agent.ainvoke(state, config)
        return result
    
    # 同步包装器
    def create_agent_with_config(state: DiagnosticState, config: RunnableConfig):
        """同步包装器 - 在独立事件循环中运行异步代码"""
        def run_in_new_loop():
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(create_agent_with_config_async(state, config))
            finally:
                loop.close()
        
        # 在线程池中运行
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_new_loop)
            return future.result()
    
    # 使用StateGraph包装，保持与原有接口的兼容性
    builder = StateGraph(DiagnosticState, config_schema=Configuration)
    builder.add_node("agent", create_agent_with_config)
    builder.set_entry_point("agent")
    builder.set_finish_point("agent")
    
    return builder

# 编译主图（只支持PostgreSQL持久化）
def compile_main_graph(enable_tool_approval: bool = True):
    """
    编译主图（只支持PostgreSQL持久化）
    Args:
        enable_tool_approval: 是否启用工具审批功能，默认True
    """
    builder = create_main_graph(enable_tool_approval)
    return compile_graph_with_checkpointer(builder)

# 默认不启用工具审批
ENABLE_TOOL_APPROVAL = False

# 导出主要使用的图和构建器
def get_diagnostic_graph():
    """获取诊断图"""
    return compile_main_graph(ENABLE_TOOL_APPROVAL)

def get_diagnostic_builder():
    """获取诊断构建器"""
    return create_main_graph(ENABLE_TOOL_APPROVAL)

# 为了向后兼容，保留原有的导出
graph = compile_main_graph(ENABLE_TOOL_APPROVAL)
builder = create_main_graph(ENABLE_TOOL_APPROVAL)