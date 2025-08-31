"""
简化的状态定义 - 只保留create_react_agent需要的基本状态
"""

from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    简化的通用Agent状态 - 只保留消息列表
    符合create_react_agent的标准接口要求
    """
    messages: Annotated[list[AnyMessage], add_messages]