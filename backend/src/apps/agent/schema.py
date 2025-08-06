"""
Agent Schema - 数据验证和序列化
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class AgentBase(BaseModel):
    """Agent基础模型"""
    agent_name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    agent_type: Optional[str] = Field(default="故障诊断", max_length=32, description="智能体分类")
    description: Optional[str] = Field(None, max_length=500, description="智能体描述")
    agent_capabilities: Optional[List[str]] = Field(default_factory=list, description="智能体能力列表")
    agent_status: Optional[str] = Field(default="stopped", pattern=r'^(running|stopped|error)$', description="智能体状态")
    agent_enabled: Optional[str] = Field(default="yes", pattern=r'^(yes|no)$', description="是否启用")
    agent_icon: Optional[str] = Field(default="Bot", max_length=50, description="智能体图标")
    
    class Config:
        str_strip_whitespace = True


class AgentCreate(AgentBase):
    """创建Agent请求模型"""
    agent_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_-]+$', max_length=50, description="智能体ID")
    tools_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="工具配置信息")
    llm_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="LLM配置信息")
    prompt_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="提示词配置信息")
    
    @field_validator('agent_capabilities')
    @classmethod
    def validate_capabilities(cls, v):
        if v and len(v) > 20:
            raise ValueError("能力列表不能超过20个")
        return v


class AgentUpdate(BaseModel):
    """更新Agent请求模型"""
    agent_name: Optional[str] = Field(None, min_length=1, max_length=100, description="智能体名称")
    agent_type: Optional[str] = Field(None, max_length=32, description="智能体分类")
    description: Optional[str] = Field(None, max_length=500, description="智能体描述")
    agent_capabilities: Optional[List[str]] = Field(None, description="智能体能力列表")
    agent_status: Optional[str] = Field(None, pattern=r'^(running|stopped|error)$', description="智能体状态")
    agent_enabled: Optional[str] = Field(None, pattern=r'^(yes|no)$', description="是否启用")
    agent_icon: Optional[str] = Field(None, max_length=50, description="智能体图标")
    tools_info: Optional[Dict[str, Any]] = Field(None, description="工具配置信息")
    llm_info: Optional[Dict[str, Any]] = Field(None, description="LLM配置信息")
    prompt_info: Optional[Dict[str, Any]] = Field(None, description="提示词配置信息")
    
    class Config:
        str_strip_whitespace = True
    
    @field_validator('agent_capabilities')
    @classmethod
    def validate_capabilities(cls, v):
        if v and len(v) > 20:
            raise ValueError("能力列表不能超过20个")
        return v


class AgentQueryParams(BaseModel):
    """Agent查询参数模型"""
    search: Optional[str] = Field(None, max_length=200, description="搜索关键词")
    status: Optional[str] = Field(None, pattern=r'^(running|stopped|error)$', description="状态过滤")
    enabled_only: Optional[bool] = Field(False, description="仅显示启用的智能体")
    include_builtin: Optional[bool] = Field(True, description="包含内置智能体")
    limit: Optional[int] = Field(10, ge=1, le=100, description="限制数量")
    offset: Optional[int] = Field(0, ge=0, description="偏移量")
    
    class Config:
        str_strip_whitespace = True


class MCPConfigUpdate(BaseModel):
    """MCP配置更新模型"""
    enabled_servers: List[str] = Field(..., description="启用的服务器列表")
    selected_tools: List[str] = Field(..., description="选择的工具列表")
    
    @field_validator('enabled_servers')
    @classmethod
    def validate_servers(cls, v):
        if len(v) > 10:
            raise ValueError("启用的服务器不能超过10个")
        return v
    
    @field_validator('selected_tools')
    @classmethod
    def validate_tools(cls, v):
        if len(v) > 50:
            raise ValueError("选择的工具不能超过50个")
        return v


class AgentStatusUpdate(BaseModel):
    """Agent状态更新模型"""
    status: str = Field(..., pattern=r'^(running|stopped|error)$', description="新状态")


class AgentStatisticsUpdate(BaseModel):
    """Agent统计信息更新模型"""
    total_runs: int = Field(..., ge=0, description="总运行次数")
    success_rate: float = Field(..., ge=0.0, le=100.0, description="成功率")
    avg_response_time: float = Field(..., ge=0.0, description="平均响应时间(秒)")


class MCPTool(BaseModel):
    """MCP工具模型"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    enabled: bool = Field(..., description="是否启用")
    category: str = Field(..., description="工具类别")
    server_id: str = Field(..., description="服务器ID")
    server_name: str = Field(..., description="服务器名称")


class MCPServerInfo(BaseModel):
    """MCP服务器信息模型"""
    id: str = Field(..., description="服务器ID")
    name: str = Field(..., description="服务器名称")
    status: str = Field(..., description="服务器状态")
    tools: List[MCPTool] = Field(default_factory=list, description="工具列表")


class AgentMCPConfig(BaseModel):
    """Agent MCP配置模型"""
    enabled_servers: List[str] = Field(default_factory=list, description="启用的服务器列表")
    selected_tools: List[str] = Field(default_factory=list, description="选择的工具列表")
    total_tools: int = Field(0, description="总工具数量")


class AgentResponse(BaseModel):
    """Agent响应模型"""
    id: str = Field(..., description="智能体ID")
    name: str = Field(..., description="智能体名称")
    agent_type: Optional[str] = Field(default="故障诊断", description="智能体分类")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    status: str = Field(..., description="状态")
    enabled: str = Field(..., description="是否启用")
    agent_icon: Optional[str] = Field(default="Bot", description="智能体图标")
    version: Optional[str] = Field(None, description="版本")
    last_used: Optional[datetime] = Field(None, description="最后使用时间")
    total_runs: int = Field(0, description="总运行次数")
    success_rate: float = Field(0.0, description="成功率")
    avg_response_time: float = Field(0.0, description="平均响应时间")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    mcp_config: AgentMCPConfig = Field(default_factory=AgentMCPConfig, description="MCP配置")
    is_builtin: str = Field("no", description="是否为内置智能体")
    tools_info: Optional[Dict[str, Any]] = Field(None, description="工具信息")
    llm_info: Optional[Dict[str, Any]] = Field(None, description="LLM信息")
    prompt_info: Optional[Dict[str, Any]] = Field(None, description="提示词信息")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")


class AgentStatistics(BaseModel):
    """Agent统计信息模型"""
    total: int = Field(..., description="总数量")
    enabled: int = Field(..., description="启用数量")
    running: int = Field(..., description="运行中数量")
    builtin: int = Field(..., description="内置智能体数量")
    custom: int = Field(..., description="自定义智能体数量")