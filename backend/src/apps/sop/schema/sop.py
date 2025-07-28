"""Pydantic schemas for SOP API."""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SOPStep(BaseModel):
    """SOP execution step schema."""
    step: int = Field(..., description="Step number", ge=1)
    description: str = Field(..., description="Step description", min_length=1, max_length=1000)
    ai_generated: bool = Field(False, description="Whether this step is AI generated")
    tool: str = Field(..., description="Tool to execute", min_length=1, max_length=100)
    args: str = Field(..., description="Tool arguments", max_length=2000)
    requires_approval: bool = Field(False, description="Whether this step requires approval")
    timeout: Optional[int] = Field(None, description="Step timeout in seconds", ge=1, le=3600)
    retry_count: Optional[int] = Field(None, description="Number of retries", ge=0, le=10)
    on_failure: Optional[Literal["continue", "stop", "branch"]] = Field(None, description="Action on failure")


class SOPTemplateCreate(BaseModel):
    """Schema for creating SOP template."""
    sop_id: str = Field(..., description="Unique SOP identifier", min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    sop_title: str = Field(..., description="SOP title", min_length=1, max_length=500)
    sop_category: str = Field(..., description="SOP category", min_length=1, max_length=100)
    sop_description: Optional[str] = Field(None, description="SOP description", max_length=2000)
    sop_severity: Literal["low", "medium", "high", "critical"] = Field(..., description="SOP severity level")
    steps: List[SOPStep] = Field(..., description="List of execution steps", min_items=1, max_items=50)
    tools_required: Optional[List[str]] = Field(None, description="List of required tools", max_items=20)
    sop_recommendations: Optional[str] = Field(None, description="SOP recommendations", max_length=2000)
    team_name: str = Field(..., description="Responsible team name", min_length=1, max_length=100)


class SOPTemplateUpdate(BaseModel):
    """Schema for updating SOP template."""
    sop_title: Optional[str] = Field(None, description="SOP title", min_length=1, max_length=500)
    sop_category: Optional[str] = Field(None, description="SOP category", min_length=1, max_length=100)
    sop_description: Optional[str] = Field(None, description="SOP description", max_length=2000)
    sop_severity: Optional[Literal["low", "medium", "high", "critical"]] = Field(None, description="SOP severity level")
    steps: Optional[List[SOPStep]] = Field(None, description="List of execution steps", min_items=1, max_items=50)
    tools_required: Optional[List[str]] = Field(None, description="List of required tools", max_items=20)
    sop_recommendations: Optional[str] = Field(None, description="SOP recommendations", max_length=2000)
    team_name: Optional[str] = Field(None, description="Responsible team name", min_length=1, max_length=100)


class SOPTemplateResponse(BaseModel):
    """Schema for SOP template response."""
    id: int
    sop_id: str
    sop_title: str
    sop_category: str
    sop_description: Optional[str]
    sop_severity: str
    sop_steps: str  # JSON string
    tools_required: Optional[str]  # JSON string
    sop_recommendations: Optional[str]
    team_name: str
    create_by: str
    update_by: Optional[str]
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class SOPQueryParams(BaseModel):
    """Schema for SOP query parameters."""
    search: Optional[str] = Field(None, description="Search term for title, description, or ID", max_length=200)
    category: Optional[str] = Field(None, description="Filter by category", max_length=100)
    severity: Optional[Literal["low", "medium", "high", "critical"]] = Field(None, description="Filter by severity")
    team_name: Optional[str] = Field(None, description="Filter by team name", max_length=100)
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