from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, Optional, List
from datetime import datetime

from langgraph.graph import add_messages
from typing_extensions import Annotated
import operator


class DiagnosticOverallState(TypedDict):
    """诊断代理的主状态 - 类似调研agent的OverallState"""
    messages: Annotated[list, add_messages]  # 消息历史
    
    # 核心诊断信息
    fault_ip: Optional[str]
    fault_time: Optional[str]
    fault_info: Optional[str]
    sop_id: Optional[str]
    
    # 诊断执行状态
    diagnosis_results: Annotated[list, operator.add]  # 诊断结果累积
    tools_used: Annotated[list, operator.add]  # 已使用的工具列表
    diagnosis_step_count: int  # 当前诊断步骤数
    max_diagnosis_steps: int  # 最大诊断步骤数
    
    # SOP相关状态
    sop_state: str  # SOP状态: "none", "selected", "validated", "loaded", "completed"
    sop_detail: Optional[dict]  # SOP详细信息
    
    # 配置信息
    reasoning_model: str  # 推理模型名称


class QuestionAnalysisState(TypedDict):
    """问题分析状态 - 类似调研agent的QueryGenerationState"""
    fault_ip: Optional[str]
    fault_time: Optional[str]
    fault_info: Optional[str]
    sop_id: Optional[str]
    info_sufficient: bool
    missing_fields: List[str]


class DiagnosisReflectionState(TypedDict):
    """诊断反思状态 - 类似调研agent的ReflectionState"""
    is_complete: bool  # 诊断是否完成
    confidence_score: float  # 当前置信度
    next_steps: List[str]  # 下一步操作列表
    knowledge_gaps: List[str]  # 知识缺口
    recommendations: List[str]  # 建议列表
    diagnosis_step_count: int  # 当前步骤数


class ToolPlanningState(TypedDict):
    """工具规划状态 - 专门用于工具选择和规划"""
    planned_tools: List[str]  # 计划使用的工具
    tool_sequence: List[dict]  # 工具执行序列
    sop_loaded: bool  # SOP是否已加载


@dataclass(kw_only=True)
class DiagnosticStateOutput:
    """诊断状态输出 - 类似调研agent的SearchStateOutput"""
    final_diagnosis: str = field(default="")  # 最终诊断结果
    sop_used: str = field(default="")  # 使用的SOP
    tools_executed: list = field(default_factory=list)  # 执行的工具列表
    confidence_score: float = field(default=0.0)  # 最终置信度
    recommendations: list = field(default_factory=list)  # 建议列表
    execution_time: str = field(default="")  # 总执行时间
    step_count: int = field(default=0)  # 总步骤数
