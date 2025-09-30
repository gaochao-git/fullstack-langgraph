"""Pydantic schemas for SOP API."""
from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SOPTemplateCreate(BaseModel):
    """Schema for creating SOP template."""
    sop_id: str = Field(..., description="Unique SOP identifier", min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    sop_title: str = Field(..., description="SOP title", min_length=1, max_length=500)
    sop_description: str = Field(..., description="SOP description including all steps", min_length=1, max_length=10000)  # 必填字段


class SOPTemplateUpdate(BaseModel):
    """Schema for updating SOP template."""
    sop_title: Optional[str] = Field(None, description="SOP title", min_length=1, max_length=500)
    sop_description: Optional[str] = Field(None, description="SOP description including all steps", max_length=10000)


class SOPTemplateResponse(BaseModel):
    """Schema for SOP template response."""
    id: int
    sop_id: str
    sop_title: str
    sop_description: str
    create_by: str
    update_by: Optional[str]
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class SOPQueryParams(BaseModel):
    """Schema for SOP query parameters."""
    search: Optional[str] = Field(None, description="Search term for title, description, or ID", max_length=200)
    limit: Optional[int] = Field(10, description="Number of results to return", ge=1, le=100)
    offset: Optional[int] = Field(0, description="Number of results to skip", ge=0)


class SOPListResponse(BaseModel):
    """Schema for SOP list response."""
    data: List[SOPTemplateResponse]
    total: int


class ApiResponse(BaseModel):
    """Generic API response schema."""
    success: bool
    data: Optional[object] = None
    message: Optional[str] = None
    error: Optional[str] = None



# ============ SOP Problem Rule 相关模型 ============

class RuleInfo(BaseModel):
    """规则信息"""
    source_type: str = Field("zabbix", description="数据源类型")
    item_keys: List[str] = Field(..., description="监控项key列表", min_items=1)


class SOPProblemRuleBase(BaseModel):
    """SOP问题规则基础模型"""
    rule_name: str = Field(..., description="规则名称", min_length=1, max_length=200)
    sop_id: str = Field(..., description="关联的SOP ID", min_length=1, max_length=100)
    rules_info: RuleInfo = Field(..., description="规则信息")
    is_enabled: bool = Field(True, description="是否启用")


class SOPProblemRuleCreate(SOPProblemRuleBase):
    """创建SOP问题规则请求"""
    pass


class SOPProblemRuleUpdate(BaseModel):
    """更新SOP问题规则请求"""
    rule_name: Optional[str] = Field(None, description="规则名称", min_length=1, max_length=200)
    sop_id: Optional[str] = Field(None, description="关联的SOP ID", min_length=1, max_length=100)
    rules_info: Optional[RuleInfo] = Field(None, description="规则信息")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class SOPProblemRuleResponse(BaseModel):
    """SOP问题规则响应"""
    id: int
    rule_name: str
    sop_id: str
    rules_info: str  # JSON string from database
    is_enabled: bool
    created_by: str
    updated_by: Optional[str]
    create_time: str
    update_time: str
    
    # 扩展字段
    sop_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class SOPProblemRuleQuery(BaseModel):
    """SOP问题规则查询参数"""
    search: Optional[str] = Field(None, description="搜索关键词", max_length=200)
    sop_id: Optional[str] = Field(None, description="SOP ID", max_length=100)
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(10, description="每页大小", ge=1, le=100)


# ============ Zabbix 相关模型 ============

class ZabbixItemOption(BaseModel):
    """Zabbix监控项选项"""
    value: str = Field(..., description="监控项key")
    label: str = Field(..., description="监控项显示名称")