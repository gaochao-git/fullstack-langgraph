"""
IDC运维报告模块请求响应Schema
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .models import ReportStatus, ReportType


class IDCReportBase(BaseModel):
    """IDC报告基础Schema"""
    report_name: str = Field(..., description="报告名称", max_length=200)
    idc_location: str = Field(..., description="IDC位置/名称", max_length=100)
    report_type: ReportType = Field(..., description="报告类型")
    start_date: datetime = Field(..., description="报告开始时间")
    end_date: datetime = Field(..., description="报告结束时间")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('结束时间必须晚于开始时间')
        return v


class IDCReportCreate(IDCReportBase):
    """创建IDC报告请求Schema"""
    pass


class IDCReportUpdate(BaseModel):
    """更新IDC报告请求Schema"""
    report_name: Optional[str] = Field(None, description="报告名称", max_length=200)
    status: Optional[ReportStatus] = Field(None, description="报告状态")
    content: Optional[str] = Field(None, description="报告内容")
    file_path: Optional[str] = Field(None, description="报告文件路径")
    file_name: Optional[str] = Field(None, description="报告文件名")
    file_size: Optional[int] = Field(None, description="文件大小")
    total_servers: Optional[int] = Field(None, description="服务器总数")
    avg_cpu_usage: Optional[float] = Field(None, description="平均CPU使用率")
    avg_memory_usage: Optional[float] = Field(None, description="平均内存使用率")
    total_power_consumption: Optional[float] = Field(None, description="总耗电量")
    pue_value: Optional[float] = Field(None, description="PUE值")
    availability_rate: Optional[float] = Field(None, description="可用性率")
    incident_count: Optional[int] = Field(None, description="事故数量")
    error_message: Optional[str] = Field(None, description="错误信息")


class IDCReportResponse(IDCReportBase):
    """IDC报告响应Schema"""
    report_id: UUID = Field(..., description="报告ID")
    status: ReportStatus = Field(..., description="报告状态")

    # 可选的统计数据
    total_servers: Optional[int] = Field(None, description="服务器总数")
    avg_cpu_usage: Optional[float] = Field(None, description="平均CPU使用率")
    avg_memory_usage: Optional[float] = Field(None, description="平均内存使用率")
    total_power_consumption: Optional[float] = Field(None, description="总耗电量(kWh)")
    pue_value: Optional[float] = Field(None, description="PUE值")
    availability_rate: Optional[float] = Field(None, description="可用性率(%)")
    incident_count: Optional[int] = Field(None, description="事故数量")

    # 文件信息
    file_name: Optional[str] = Field(None, description="报告文件名")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")

    # 生成信息
    generated_by: Optional[str] = Field(None, description="生成人员")
    generation_time: Optional[datetime] = Field(None, description="生成完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")

    # 基础信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[str] = Field(None, description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")

    class Config:
        from_attributes = True


class IDCReportListParams(BaseModel):
    """IDC报告列表查询参数Schema"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    idc_location: Optional[str] = Field(None, description="IDC位置筛选")
    report_type: Optional[ReportType] = Field(None, description="报告类型筛选")
    status: Optional[ReportStatus] = Field(None, description="状态筛选")
    start_date: Optional[datetime] = Field(None, description="筛选开始时间")
    end_date: Optional[datetime] = Field(None, description="筛选结束时间")


class IDCLocationBase(BaseModel):
    """IDC位置基础Schema"""
    location_name: str = Field(..., description="位置名称", max_length=100)
    location_code: str = Field(..., description="位置代码", max_length=20)
    description: Optional[str] = Field(None, description="位置描述", max_length=500)
    address: Optional[str] = Field(None, description="详细地址", max_length=500)
    is_active: int = Field(1, description="是否活跃")


class IDCLocationResponse(IDCLocationBase):
    """IDC位置响应Schema"""
    location_id: UUID = Field(..., description="位置ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class IDCReportStats(BaseModel):
    """IDC报告统计信息Schema"""
    total_reports: int = Field(..., description="总报告数")
    pending_reports: int = Field(..., description="待生成报告数")
    generating_reports: int = Field(..., description="生成中报告数")
    completed_reports: int = Field(..., description="已完成报告数")
    failed_reports: int = Field(..., description="失败报告数")
    this_month_reports: int = Field(..., description="本月报告数")
    total_locations: int = Field(..., description="IDC位置总数")
    recent_reports: List[IDCReportResponse] = Field(..., description="最近的报告")


class GenerateReportResponse(BaseModel):
    """生成报告响应Schema"""
    report_id: UUID = Field(..., description="报告ID")
    message: str = Field(..., description="响应消息")
    status: ReportStatus = Field(..., description="当前状态")
    estimated_time: Optional[int] = Field(None, description="预计完成时间(分钟)")