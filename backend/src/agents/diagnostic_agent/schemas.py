"""
故障诊断代理数据模型定义模块
包含所有Pydantic模型和数据结构
"""
from typing import List
# 注意：使用 langchain_core.pydantic_v1 而不是 pydantic
# 原因：DeepSeek API 不支持 OpenAI 标准的 response_format，当使用 pydantic v2 时
# with_structured_output 会尝试使用 response_format 导致 422 错误
# 使用 pydantic_v1 可以让 LangChain 降级使用提示词方式获取结构化输出
# 虽然会有 deprecation 警告，但功能稳定可用
# 如需升级到 v2，需要确保 LLM 提供商完全支持 OpenAI 兼容的 response_format
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
    sop_steps_completed: List[str] = Field(description="已完成的SOP步骤")
    sop_steps_remaining: List[str] = Field(description="还需执行的SOP步骤")
    root_cause_found: bool = Field(description="是否找到了明确的根因")
    root_cause_analysis: str = Field(description="根因分析结果")
    next_steps: List[str] = Field(description="下一个需要执行的SOP步骤")
    user_recommendations: List[str] = Field(description="基于当前结果给用户的建议")
    termination_reason: str = Field(description="结束原因：root_cause_found（找到根因）或 sop_completed（完成所有SOP）或 continue（继续诊断）")