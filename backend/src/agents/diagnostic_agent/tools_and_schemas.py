from typing import List
from pydantic import BaseModel, Field


class QuestionInfoExtraction(BaseModel):
    """诊断问题信息提取 - 用于结构化提取用户输入中的四要素"""
    fault_ip: str = Field(description="故障IP地址")
    fault_time: str = Field(description="故障发生时间")
    fault_info: str = Field(description="故障现象描述")
    sop_id: str = Field(description="排查SOP编号")
