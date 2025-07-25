from __future__ import annotations

from typing import TypedDict
from langgraph.graph import add_messages
from typing_extensions import Annotated


class AgentState(TypedDict):
    """通用Agent状态定义
    
    使用简化的状态结构，兼容create_react_agent
    """
    
    # === 核心消息状态 ===
    messages: Annotated[list, add_messages]


class ToolExecutionState(TypedDict):
    """工具执行子状态"""
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[Any]
    execution_time: Optional[float]
    success: bool
    error_message: Optional[str]
    requires_approval: bool
    approval_status: Optional[str]


class ReflectionState(TypedDict):
    """自我反思状态（实验性功能）"""
    current_progress: str
    identified_issues: List[str]
    suggested_improvements: List[str]
    confidence_score: float
    should_continue: bool


class ParallelExecutionState(TypedDict):
    """并行执行状态（实验性功能）"""
    parallel_tasks: List[Dict[str, Any]]
    completed_tasks: Annotated[List[Dict[str, Any]], operator.add]
    failed_tasks: Annotated[List[Dict[str, Any]], operator.add]
    execution_plan: Optional[Dict[str, Any]]


def create_initial_state(
    agent_config: Dict[str, Any],
    model_config: Dict[str, Any],
    user_message: str = "",
    user_context: Optional[Dict[str, Any]] = None
) -> AgentState:
    """创建初始的Agent状态"""
    
    initial_messages = []
    if user_message:
        initial_messages.append({"role": "user", "content": user_message})
    
    return AgentState(
        messages=initial_messages,
        iteration_count=0,
        max_iterations=agent_config.get("max_iterations", 10),
        tool_calls_count=0,
        max_tool_calls=agent_config.get("max_tool_calls_per_turn", 5),
        used_tools=[],
        pending_approvals=[],
        agent_config=agent_config,
        model_config=model_config,
        user_context=user_context or {},
        session_data={},
        final_result=None,
        execution_summary=None,
        errors=[],
        warnings=[]
    )


def is_execution_complete(state: AgentState) -> bool:
    """检查执行是否完成"""
    
    # 检查是否达到最大迭代次数
    if state["iteration_count"] >= state["max_iterations"]:
        return True
    
    # 检查是否达到最大工具调用次数
    if state["tool_calls_count"] >= state["max_tool_calls"]:
        return True
    
    # 检查是否有待审批的工具调用
    if state["pending_approvals"]:
        return False
    
    # 检查是否有最终结果
    if state["final_result"]:
        return True
    
    # 检查消息中是否包含结束标志
    if state["messages"]:
        last_message = state["messages"][-1]
        if isinstance(last_message, dict) and last_message.get("role") == "assistant":
            content = last_message.get("content", "")
            if any(keyword in content.lower() for keyword in ["任务完成", "已完成", "结束", "final answer"]):
                return True
    
    return False


def update_execution_summary(state: AgentState) -> Dict[str, Any]:
    """更新执行摘要"""
    
    summary = {
        "total_iterations": state["iteration_count"],
        "total_tool_calls": state["tool_calls_count"],
        "used_tools": list(set(state["used_tools"])),
        "has_errors": len(state["errors"]) > 0,
        "has_warnings": len(state["warnings"]) > 0,
        "execution_status": "completed" if is_execution_complete(state) else "in_progress",
        "final_result_available": state["final_result"] is not None
    }
    
    return summary