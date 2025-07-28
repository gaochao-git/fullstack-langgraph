"""MCP Server schemas - 增强验证"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
import json


class MCPServerCreate(BaseModel):
    """创建MCP服务器的schema"""
    server_id: str = Field(..., description="服务器唯一标识", min_length=1, max_length=100, 
                          pattern=r'^[a-zA-Z0-9_-]+$')
    server_name: str = Field(..., description="服务器名称", min_length=1, max_length=200)
    server_uri: str = Field(..., description="服务器URI", min_length=1, max_length=500)
    server_description: Optional[str] = Field(None, description="服务器描述", max_length=1000)
    is_enabled: Optional[Literal["on", "off"]] = Field("on", description="是否启用")
    connection_status: Optional[Literal["connected", "disconnected", "error"]] = Field(
        "disconnected", description="连接状态")
    auth_type: Optional[str] = Field(None, description="认证类型", max_length=20)
    auth_token: Optional[str] = Field(None, description="认证令牌", max_length=500)
    api_key_header: Optional[str] = Field(None, description="API密钥头", max_length=100)
    read_timeout_seconds: Optional[int] = Field(5, description="读取超时秒数", ge=1, le=300)
    server_tools: Optional[List[str]] = Field(None, description="服务器工具列表", max_items=100)
    server_config: Optional[Dict[str, Any]] = Field(None, description="服务器配置")
    team_name: str = Field(..., description="团队名称", min_length=1, max_length=100)
    
    @validator('server_uri')
    def validate_server_uri(cls, v):
        """验证服务器URI格式"""
        if not (v.startswith('http://') or v.startswith('https://') or ':' in v):
            raise ValueError('服务器URI必须是有效的HTTP/HTTPS URL或host:port格式')
        return v


class MCPServerUpdate(BaseModel):
    """更新MCP服务器的schema"""
    server_name: Optional[str] = Field(None, description="服务器名称", min_length=1, max_length=200)
    server_uri: Optional[str] = Field(None, description="服务器URI", min_length=1, max_length=500)
    server_description: Optional[str] = Field(None, description="服务器描述", max_length=1000)
    is_enabled: Optional[Literal["on", "off"]] = Field(None, description="是否启用")
    connection_status: Optional[Literal["connected", "disconnected", "error"]] = Field(
        None, description="连接状态")
    auth_type: Optional[str] = Field(None, description="认证类型", max_length=20)
    auth_token: Optional[str] = Field(None, description="认证令牌", max_length=500)
    api_key_header: Optional[str] = Field(None, description="API密钥头", max_length=100)
    read_timeout_seconds: Optional[int] = Field(None, description="读取超时秒数", ge=1, le=300)
    server_tools: Optional[List[str]] = Field(None, description="服务器工具列表", max_items=100)
    server_config: Optional[Dict[str, Any]] = Field(None, description="服务器配置")
    team_name: Optional[str] = Field(None, description="团队名称", min_length=1, max_length=100)
    
    @validator('server_uri')
    def validate_server_uri(cls, v):
        """验证服务器URI格式"""
        if v and not (v.startswith('http://') or v.startswith('https://') or ':' in v):
            raise ValueError('服务器URI必须是有效的HTTP/HTTPS URL或host:port格式')
        return v


class MCPServerResponse(BaseModel):
    """MCP服务器响应schema"""
    id: int
    server_id: str
    server_name: str
    server_uri: str
    server_description: Optional[str]
    is_enabled: str
    connection_status: str
    auth_type: Optional[str]
    auth_token: Optional[str]
    api_key_header: Optional[str]
    read_timeout_seconds: int
    server_tools: Optional[str]  # JSON string
    server_config: Optional[str]  # JSON string
    team_name: str
    create_by: str
    update_by: Optional[str]
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class MCPQueryParams(BaseModel):
    """MCP查询参数schema"""
    search: Optional[str] = Field(None, description="搜索关键词", max_length=200)
    is_enabled: Optional[Literal["on", "off"]] = Field(None, description="启用状态过滤")
    connection_status: Optional[Literal["connected", "disconnected", "error"]] = Field(
        None, description="连接状态过滤")
    team_name: Optional[str] = Field(None, description="团队名称过滤", max_length=100)
    limit: Optional[int] = Field(10, description="返回数量", ge=1, le=100)
    offset: Optional[int] = Field(0, description="偏移量", ge=0)


class MCPTestRequest(BaseModel):
    """测试MCP服务器连接的请求schema"""
    server_uri: str = Field(..., description="服务器URI", min_length=1, max_length=500)
    timeout: int = Field(10, description="超时时间", ge=1, le=60)
    
    @validator('server_uri')
    def validate_server_uri(cls, v):
        """验证服务器URI格式"""
        if not (v.startswith('http://') or v.startswith('https://') or ':' in v):
            raise ValueError('服务器URI必须是有效的HTTP/HTTPS URL或host:port格式')
        return v


class MCPTestResponse(BaseModel):
    """测试MCP服务器连接的响应schema"""
    healthy: bool
    tools: List[Dict[str, Any]]
    error: Optional[str]


class MCPStatusUpdate(BaseModel):
    """更新MCP服务器状态的schema"""
    status: Literal["connected", "disconnected", "error"] = Field(..., description="连接状态")


class MCPEnableUpdate(BaseModel):
    """启用/禁用MCP服务器的schema"""
    enabled: Literal["on", "off"] = Field(..., description="启用状态")