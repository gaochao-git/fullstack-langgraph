"""
自定义状态模式定义
扩展 LangGraph 的基础状态以支持额外功能
"""

from typing import List, Dict, Any, Annotated, NotRequired, TypedDict
from langgraph.graph import MessagesState, add_messages
from langchain_core.messages import AnyMessage


class Todo(TypedDict):
    """任务项定义"""
    content: str
    status: str  # pending, in_progress, completed
    priority: str  # high, medium, low
    created_at: str
    updated_at: str
    findings: NotRequired[str]


# 自定义 reducer 函数
def todos_reducer(current: List[Todo], new: List[Todo]) -> List[Todo]:
    """
    Todos reducer - 直接替换整个列表
    """
    return new


def files_reducer(current: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
    """
    Files reducer - 合并文件字典
    """
    if not current:
        return new
    merged = current.copy()
    merged.update(new)
    return merged


class ExtendedAgentState(MessagesState):
    """
    扩展的Agent状态，支持任务管理和文件系统
    """
    # 继承自 MessagesState，已包含 messages 字段
    # messages: Annotated[list[AnyMessage], add_messages]
    
    # create_react_agent 需要的字段
    remaining_steps: int = 10
    
    # 任务列表
    todos: Annotated[List[Todo], todos_reducer] = []
    
    # 文件系统（文件名 -> 内容）
    files: Annotated[Dict[str, str], files_reducer] = {}
    
    # 当前工作目录
    current_dir: str = "/"
    
    # 其他可扩展的状态字段
    context: Dict[str, Any] = {}


class DiagnosticAgentState(ExtendedAgentState):
    """
    诊断Agent专用状态，在扩展状态基础上添加诊断特有字段
    """
    # 诊断结果
    diagnosis_results: List[Dict[str, Any]] = []
    
    # 系统指标
    system_metrics: Dict[str, Any] = {}
    
    # 故障根因
    root_causes: List[str] = []


# 使用示例
"""
from langgraph.prebuilt import create_react_agent
from .state_schemas import DiagnosticAgentState

# 创建使用自定义状态的agent
agent = create_react_agent(
    model=model,
    tools=tools,
    state_schema=DiagnosticAgentState,  # 使用自定义状态
    prompt=system_prompt
)

# 工具返回Command更新状态
from langgraph.types import Command
from langchain_core.messages import ToolMessage

@tool
def my_tool() -> Command:
    return Command(
        update={
            "todos": [...],  # 更新任务列表
            "system_metrics": {...}  # 更新系统指标
        },
        messages=[ToolMessage(...)]  # 消息
    )
"""