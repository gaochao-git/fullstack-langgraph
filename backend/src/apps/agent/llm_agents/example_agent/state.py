"""
Example Agent 状态定义
展示如何定义自定义状态结构（LangGraph 0.6.6）
"""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class ExampleAgentState(TypedDict):
    """Example Agent 的自定义状态
    
    展示如何定义状态来支持自定义工作流
    """
    # 消息列表（使用 add_messages reducer 自动合并）
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 当前任务类型
    task_type: Optional[str]
    
    # 文本处理的中间结果
    processing_results: Dict[str, Any]
    
    # 是否需要人工确认
    need_human_confirmation: bool
    
    # 工作流步骤记录
    workflow_steps: List[str]
    
    # 错误信息
    error: Optional[str]
    
    # 重试次数
    retry_count: int
    
    # 是否需要后续处理
    needs_followup: bool