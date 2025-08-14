"""通用Agent工具函数 - 精简版"""

from typing import Any
from langgraph.graph import StateGraph
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


def compile_graph_with_checkpointer(builder: StateGraph, checkpointer_type=None) -> Any:
    """
    编译状态图 - 与diagnostic_agent保持一致
    
    Args:
        builder: 状态图工作流
        checkpointer_type: 保留参数但不再使用（检查点在streaming.py中设置）
        
    Returns:
        编译后的图
    """
    # 与diagnostic_agent保持一致，不在这里设置checkpointer
    # checkpointer会在streaming.py中根据环境配置自动设置
    graph = builder.compile(name="generic-agent")
    return graph