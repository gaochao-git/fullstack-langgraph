"""
Agent Schema - 数据验证和序列化
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class LLMModelConfig(BaseModel):
    """单个LLM模型配置"""
    model_name: str = Field(..., description="模型名称")
    model_args: Dict[str, Any] = Field(default_factory=dict, description="模型参数配置")
    
    @field_validator('model_args')
    @classmethod
    def validate_model_args(cls, v):
        """验证模型参数"""
        allowed_keys = {'temperature', 'max_tokens', 'top_p'}
        for key in v.keys():
            if key not in allowed_keys:
                raise ValueError(f"不支持的参数: {key}")
        
        # 验证参数值范围
        if 'temperature' in v:
            if not (0 <= v['temperature'] <= 2):
                raise ValueError("temperature必须在0到2之间")
        
        if 'max_tokens' in v:
            if not (1 <= v['max_tokens'] <= 100000):
                raise ValueError("max_tokens必须在1到100000之间")
                
        if 'top_p' in v:
            if not (0 <= v['top_p'] <= 1):
                raise ValueError("top_p必须在0到1之间")
                
        return v


class AgentBase(BaseModel):
    """Agent基础模型"""
    agent_name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    agent_type: Optional[str] = Field(default="故障诊断", max_length=32, description="智能体分类")
    agent_description: Optional[str] = Field(None, max_length=500, description="智能体描述")
    agent_capabilities: Optional[List[str]] = Field(default_factory=list, description="智能体能力列表")
    agent_enabled: Optional[str] = Field(default="yes", pattern=r'^(yes|no)$', description="是否启用")
    agent_icon: Optional[str] = Field(default="Bot", max_length=50, description="智能体图标")
    
    class Config:
        str_strip_whitespace = True


class AgentCreate(AgentBase):
    """创建Agent请求模型"""
    agent_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_-]+$', max_length=50, description="智能体ID")
    tools_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="工具配置信息")
    llm_info: Optional[List[LLMModelConfig]] = Field(default_factory=list, description="LLM配置信息列表")
    prompt_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="提示词配置信息")
    # 权限相关字段
    visibility_type: Optional[str] = Field(default="private", pattern=r'^(private|team|department|public)$', description="可见权限级别")
    visibility_additional_users: Optional[List[str]] = Field(default_factory=list, description="额外授权用户列表")
    
    @field_validator('agent_capabilities')
    @classmethod
    def validate_capabilities(cls, v):
        if v and len(v) > 20:
            raise ValueError("能力列表不能超过20个")
        return v
    
    @field_validator('visibility_additional_users')
    @classmethod
    def validate_additional_users(cls, v):
        if v and len(v) > 50:
            raise ValueError("额外授权用户不能超过50个")
        return v


class AgentUpdate(BaseModel):
    """更新Agent请求模型"""
    agent_name: Optional[str] = Field(None, min_length=1, max_length=100, description="智能体名称")
    agent_type: Optional[str] = Field(None, max_length=32, description="智能体分类")
    agent_description: Optional[str] = Field(None, max_length=500, description="智能体描述")
    agent_capabilities: Optional[List[str]] = Field(None, description="智能体能力列表")
    agent_enabled: Optional[str] = Field(None, pattern=r'^(yes|no)$', description="是否启用")
    agent_icon: Optional[str] = Field(None, max_length=50, description="智能体图标")
    tools_info: Optional[Dict[str, Any]] = Field(None, description="工具配置信息")
    llm_info: Optional[List[LLMModelConfig]] = Field(None, description="LLM配置信息列表")
    prompt_info: Optional[Dict[str, Any]] = Field(None, description="提示词配置信息")
    # 权限相关字段
    visibility_type: Optional[str] = Field(None, pattern=r'^(private|team|department|public)$', description="可见权限级别")
    visibility_additional_users: Optional[List[str]] = Field(None, description="额外授权用户列表")
    
    class Config:
        str_strip_whitespace = True
    
    @field_validator('agent_capabilities')
    @classmethod
    def validate_capabilities(cls, v):
        if v and len(v) > 20:
            raise ValueError("能力列表不能超过20个")
        return v
    
    @field_validator('visibility_additional_users')
    @classmethod
    def validate_additional_users(cls, v):
        if v and len(v) > 50:
            raise ValueError("额外授权用户不能超过50个")
        return v


class AgentQueryParams(BaseModel):
    """Agent查询参数模型"""
    search: Optional[str] = Field(None, max_length=200, description="搜索关键词")
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



class AgentStatisticsUpdate(BaseModel):
    """Agent统计信息更新模型"""
    total_runs: int = Field(..., ge=0, description="总运行次数")
    success_rate: float = Field(..., ge=0.0, le=100.0, description="成功率")
    avg_response_time: float = Field(..., ge=0.0, description="平均响应时间(秒)")


class AgentOwnerTransfer(BaseModel):
    """Agent所有权转移模型"""
    new_owner: str = Field(..., min_length=1, max_length=100, description="新所有者用户名")
    reason: Optional[str] = Field(None, max_length=200, description="转移原因")


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
    llm_info: Optional[List[LLMModelConfig]] = Field(None, description="LLM信息列表")
    prompt_info: Optional[Dict[str, Any]] = Field(None, description="提示词信息")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")


class AgentStatistics(BaseModel):
    """Agent统计信息模型"""
    total: int = Field(..., description="总数量")
    enabled: int = Field(..., description="启用数量")
    running: int = Field(..., description="运行中数量")
    builtin: int = Field(..., description="内置智能体数量")


# ============= 文档上传相关 Schema =============

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    file_name: str
    file_size: int
    file_type: str
    upload_time: str
    status: str = "uploaded"  # uploaded, processing, ready, failed
    message: Optional[str] = None


class DocumentContent(BaseModel):
    """文档内容"""
    file_id: str
    file_name: str
    content: str  # 提取的文本内容
    metadata: Optional[Dict[str, Any]] = None  # 页数、作者等元信息
    chunks: Optional[List[Dict[str, Any]]] = None  # 分块内容（用于大文档）


class FileProcessStatus(BaseModel):
    """文件处理状态"""
    file_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    processed_at: Optional[str] = None


class MessageFeedbackCreate(BaseModel):
    """创建消息反馈的请求模型"""
    feedback_type: Literal["thumbs_up", "thumbs_down"] = Field(..., description="反馈类型")
    feedback_content: Optional[str] = Field(None, description="反馈内容(预留)")


class MessageFeedbackResponse(BaseModel):
    """消息反馈响应模型"""
    id: int
    thread_id: str
    message_id: str
    agent_id: str
    user_name: str
    feedback_type: str
    feedback_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # 智能体最新统计数据
    agent_stats: Optional[Dict[str, Any]] = None