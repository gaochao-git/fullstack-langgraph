from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from datetime import datetime

from langgraph.graph import MessagesState
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
    confidence_score: float = 0.0
    root_cause_found: bool = False
    root_cause_analysis: str = ""
    termination_reason: Literal["continue", "root_cause_found", "sop_completed", "max_steps_reached"] = "continue"


class DiagnosticState(MessagesState):
    """诊断代理的主状态 - 简化版本，参考优化实现"""
    # 基础信息
    user_question: str = ""
    question_analysis: QuestionAnalysis = Field(default_factory=QuestionAnalysis)
    
    # SOP管理
    sop_detail: SOPDetail = Field(default_factory=SOPDetail)
    sop_loaded: bool = False
    
    # 诊断进度
    diagnosis_progress: DiagnosisProgress = Field(default_factory=DiagnosisProgress)
    
    # 诊断结果
    diagnosis_results: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    
    # 最终报告
    final_diagnosis: str = ""


class DiagnosticOutput(BaseModel):
    """诊断输出结果"""
    final_diagnosis: str = ""
    sop_used: str = ""
    tools_executed: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    recommendations: List[str] = Field(default_factory=list)
    execution_time: str = ""
    step_count: int = 0
