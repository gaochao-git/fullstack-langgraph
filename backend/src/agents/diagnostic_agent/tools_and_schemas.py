from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field


class QuestionInfoExtraction(BaseModel):
    """用于问题信息提取的结构化输出"""
    fault_ip: str = Field(description="故障IP地址")
    fault_time: str = Field(description="故障时间")
    fault_info: str = Field(description="故障现象描述")
    sop_id: str = Field(description="SOP编号")


class DiagnosisReflectionOutput(BaseModel):
    """诊断反思输出的结构化模式 - 按SOP顺序执行，找到根因可提前结束"""
    is_complete: bool = Field(description="是否可以结束诊断（找到根因或完成所有SOP步骤）")
    confidence_score: float = Field(description="对当前诊断结果的置信度，0.0-1.0")
    sop_steps_completed: List[str] = Field(description="已完成的SOP步骤")
    sop_steps_remaining: List[str] = Field(description="还需执行的SOP步骤")
    root_cause_found: bool = Field(description="是否找到了明确的根因")
    root_cause_analysis: str = Field(description="根因分析结果")
    next_steps: List[str] = Field(description="下一个需要执行的SOP步骤")
    user_recommendations: List[str] = Field(description="基于当前结果给用户的建议")
    termination_reason: str = Field(description="结束原因：root_cause_found（找到根因）或 sop_completed（完成所有SOP）或 continue（继续诊断）")
