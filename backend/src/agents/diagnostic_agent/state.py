from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, Optional, List
from datetime import datetime

from langgraph.graph import add_messages
from typing_extensions import Annotated
import operator


class DiagnosticOverallState(TypedDict):
    """诊断代理的总体状态"""
    messages: Annotated[list, add_messages]  # 消息历史
    sop_state: str  # SOP状态: "none", "selected", "validated", "loaded", "completed"
    tools_used: Annotated[list, operator.add]  # 已使用的工具列表
    diagnosis_results: Annotated[list, operator.add]  # 诊断结果累积
    current_step: str  # 当前诊断步骤
    max_diagnosis_steps: int  # 最大诊断步骤数
    diagnosis_step_count: Annotated[list, operator.add]  # 诊断步骤计数累积
    reasoning_model: str  # 推理模型名称
    confidence_score: float  # 诊断置信度
    info_sufficient: bool  # 信息是否充足

class QuestionInfoState(TypedDict):
    user_question: str
    fault_ip: Optional[str]
    fault_time: Optional[str]
    fault_info: Optional[str]
    sop_id: Optional[str]
    info_sufficient: bool
    missing_fields: List[str]

class ToolExecutionState(TypedDict):
    """工具执行状态"""
    tool_name: str  # 工具名称
    tool_input: dict  # 工具输入参数
    tool_output: str  # 工具输出结果
    execution_time: str  # 执行时间
    execution_status: str  # 执行状态 (success/failed)
    error_message: Optional[str]  # 错误信息

class DiagnosisReflectionState(TypedDict):
    """诊断反思状态"""
    is_complete: bool  # 诊断是否完成
    next_steps: Annotated[list, operator.add]  # 下一步操作列表
    confidence_score: float  # 当前置信度
    diagnosis_step_count: Annotated[list, operator.add]  # 诊断步骤计数
    knowledge_gaps: Annotated[list, operator.add]  # 知识缺口
    recommendations: Annotated[list, operator.add]  # 建议列表

@dataclass(kw_only=True)
class DiagnosticStateOutput:
    """诊断状态输出"""
    final_diagnosis: str = field(default=None)  # 最终诊断结果
    sop_used: str = field(default=None)  # 使用的SOP
    tools_executed: list = field(default_factory=list)  # 执行的工具列表
    confidence_score: float = field(default=0.0)  # 最终置信度
    recommendations: list = field(default_factory=list)  # 建议列表
    execution_time: str = field(default=None)  # 总执行时间
    step_count: int = field(default=0)  # 总步骤数
