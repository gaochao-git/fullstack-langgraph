"""智能运维助手图定义 - 使用create_react_agent的简化实现"""

import os
import logging
from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState
from .tools_with_approval import get_tools_with_selective_approval
from .utils import compile_graph_with_checkpointer
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# 提示词已迁移到 prompts.py 文件中统一管理

def create_main_graph():
    """
    创建简化的主图 - 直接使用create_react_agent
    """
    print("📍 创建简化的智能运维助手")
    
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
        
        # 创建react agent，使用选择性审批的工具
        tools_with_approval = get_tools_with_selective_approval()
        agent = create_react_agent(
            model=llm,
            tools=tools_with_approval,  # 使用带选择性审批的工具
            prompt=SYSTEM_PROMPT,
            # 不需要 interrupt_before，因为中断逻辑在工具内部
        )
        
        # 运行agent
        result = agent.invoke(state, config)
        return result
    
    # 使用StateGraph包装，保持与原有接口的兼容性
    from langgraph.graph import StateGraph
    builder = StateGraph(DiagnosticState, config_schema=Configuration)
    builder.add_node("agent", create_agent_with_config)
    builder.set_entry_point("agent")
    builder.set_finish_point("agent")
    
    return builder

# 编译主图
def compile_main_graph():
    """编译主图"""
    builder = create_main_graph()
    checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
    return compile_graph_with_checkpointer(builder, checkpointer_type)

# 导出编译后的图
graph = compile_main_graph()

# 导出builder用于PostgreSQL模式
builder = create_main_graph()