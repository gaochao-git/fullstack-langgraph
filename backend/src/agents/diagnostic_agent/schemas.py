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
    """诊断反思输出的结构化模式 - 智能决策下一步行动"""
    action: str = Field(description="下一步行动：continue/generate_report/answer_question")
    is_complete: bool = Field(description="诊断是否完成")
    should_generate_report: bool = Field(description="是否需要生成报告")
    root_cause_found: bool = Field(description="是否找到根因")
    response_content: str = Field(description="具体回复内容（如果是answer_question）", default="")
    termination_reason: str = Field(description="continue/sop_completed/root_cause_found")