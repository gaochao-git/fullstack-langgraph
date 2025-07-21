"""智能运维助手图定义 - 使用create_react_agent的简化实现"""

import os
import logging
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState
from .tools_with_approval import get_tools_with_selective_approval
from .tools import all_tools
from .utils import compile_graph_with_checkpointer
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# 提示词已迁移到 prompts.py 文件中统一管理

def create_main_graph(enable_tool_approval: bool = True):
    """
    创建简化的主图 - 直接使用create_react_agent
    
    Args:
        enable_tool_approval: 是否启用工具审批功能，默认True
    """
    approval_status = "启用工具审批" if enable_tool_approval else "禁用工具审批"
    print(f"📍 创建简化的智能运维助手 ({approval_status})")
    
    def get_llm_from_config(config: RunnableConfig):
        """从配置中获取LLM实例"""
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(
            model_name=configurable.query_generator_model,
            temperature=configurable.model_temperature
        )
    
    # 创建react agent
    def create_agent_with_config(state: DiagnosticState, config: RunnableConfig):
        """创建带配置的agent节点"""
        llm = get_llm_from_config(config)
        
        # 根据配置选择工具列表
        if enable_tool_approval:
            tools = get_tools_with_selective_approval()
            print("🔒 使用带审批功能的工具列表")
        else:
            tools = all_tools
            print("🔓 使用无审批的原始工具列表")
        
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=SYSTEM_PROMPT,
        )
        
        # 运行agent
        result = agent.invoke(state, config)
        return result
    
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
graph = compile_main_graph(ENABLE_TOOL_APPROVAL)
builder = create_main_graph(ENABLE_TOOL_APPROVAL)