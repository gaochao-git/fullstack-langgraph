from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field


class QuestionInfoExtraction(BaseModel):
    """用于问题信息提取的结构化输出"""
    fault_ip: str = Field(description="故障IP地址")
    fault_time: str = Field(description="故障时间")
    fault_info: str = Field(description="故障现象描述")
    sop_id: str = Field(description="SOP编号")


class DiagnosisReflectionOutput(BaseModel):
    """诊断反思输出的结构化模式"""
    is_complete: bool = Field(description="诊断是否完成")
    confidence_score: float = Field(description="当前诊断结果的置信度，0.0-1.0")
    next_steps: List[str] = Field(description="建议的下一步操作")
    knowledge_gaps: List[str] = Field(description="还需要收集的信息")
    recommendations: List[str] = Field(description="诊断建议")
