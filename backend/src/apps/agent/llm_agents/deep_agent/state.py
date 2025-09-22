"""
Deep Agent 状态定义 - 直接复用 DeepAgents 的设计
"""
from langgraph.graph.message import MessagesState
from typing import NotRequired, Annotated, Literal
from typing_extensions import TypedDict


class Todo(TypedDict):
    """Todo to track - 与 DeepAgents 完全一致"""
    content: str
    status: Literal["pending", "in_progress", "completed"]
    priority: NotRequired[Literal["high", "medium", "low"]]  # 扩展：添加优先级


def file_reducer(l, r):
    """文件合并器 - 复用 DeepAgents 的逻辑"""
    if l is None:
        return r
    elif r is None:
        return l
    else:
        return {**l, **r}


class DeepAgentState(MessagesState):
    """Deep Agent 状态 - 基于 DeepAgents 的 DeepAgentState"""
    # 任务管理（与 DeepAgents 一致）
    todos: NotRequired[list[Todo]]
    
    # 虚拟文件系统（与 DeepAgents 一致）
    files: Annotated[NotRequired[dict[str, str]], file_reducer]
    
    # 扩展字段：支持更多场景
    context: NotRequired[dict[str, any]]  # 上下文信息
    metadata: NotRequired[dict[str, any]]  # 元数据