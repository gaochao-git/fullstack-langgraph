from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from datetime import datetime
from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class SOPStep(BaseModel):
    """SOP步骤 - 使用Pydantic模型管理"""
    title: str = ""
    description: str = ""
    action: str = ""
    requires_approval: bool = False
    status: Literal["pending", "in_progress", "completed"] = "pending"


class SOPDetail(BaseModel):
    """SOP详细信息"""
    sop_id: str = ""
    title: str = ""
    description: str = ""
    steps: List[SOPStep] = Field(default_factory=list)
    total_steps: int = 0


class QuestionAnalysis(BaseModel):
    """问题四要素分析"""
    fault_ip: Optional[str] = None
    fault_time: Optional[str] = None
    fault_info: Optional[str] = None
    sop_id: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    info_sufficient: bool = False


class DiagnosisProgress(BaseModel):
    """诊断进度跟踪"""
    current_step: int = 0
    max_steps: int = 50
    is_complete: bool = False
    root_cause_found: bool = False
    root_cause_analysis: str = ""
    termination_reason: Literal["continue", "root_cause_found", "sop_completed", "max_steps_reached", "no_sop_fallback", "user_cancelled"] = "continue"


class DiagnosticState(TypedDict):
    """
    诊断代理的主状态
    """
    messages: Annotated[list[AnyMessage], add_messages]
    # 基础信息
    user_question: str = ""
    question_analysis: QuestionAnalysis = Field(default_factory=QuestionAnalysis)
    
    # SOP管理
    sop_detail: SOPDetail = Field(default_factory=SOPDetail)
    sop_loaded: bool = False
    
    # 诊断进度
    diagnosis_progress: DiagnosisProgress = Field(default_factory=DiagnosisProgress)
    
    # 诊断结果 - 现在从messages中提取，不再需要单独存储
    tools_used: List[str] = Field(default_factory=list)
    
    # 审批状态
    approved_steps: List[str] = Field(default_factory=list)  # 已审批的步骤列表
    
    # 最终报告
    final_diagnosis: str = ""
    report_generated: bool = False


class DiagnosticOutput(BaseModel):
    """诊断输出结果"""
    final_diagnosis: str = ""
    sop_used: str = ""
    tools_executed: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    execution_time: str = ""
    step_count: int = 0
