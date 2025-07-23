"""MCP Server Pydantic schemas."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class MCPServerBase(BaseModel):
    """MCP服务器基础模型"""
    server_name: str
    server_uri: str
    server_description: Optional[str] = None
    is_enabled: str = "on"
    connection_status: str = "disconnected"
    auth_type: Optional[str] = ""
    auth_token: Optional[str] = None
    api_key_header: Optional[str] = None
    server_tools: Optional[List[Dict[str, Any]]] = None
    server_config: Optional[Dict[str, Any]] = None
    team_name: str
    create_by: str


class MCPServerCreate(MCPServerBase):
    """创建MCP服务器模型"""
    server_id: str


class MCPServerUpdate(BaseModel):
    """更新MCP服务器模型"""
    server_name: Optional[str] = None
    server_uri: Optional[str] = None
    server_description: Optional[str] = None
    is_enabled: Optional[str] = None
    connection_status: Optional[str] = None
    auth_type: Optional[str] = None
    auth_token: Optional[str] = None
    api_key_header: Optional[str] = None
    server_tools: Optional[List[Dict[str, Any]]] = None
    server_config: Optional[Dict[str, Any]] = None
    update_by: Optional[str] = None


class MCPServerResponse(MCPServerBase):
    """MCP服务器响应模型"""
    id: int
    server_id: str
    update_by: Optional[str] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None

    class Config:
        from_attributes = True


class MCPTestRequest(BaseModel):
    """MCP服务器测试请求模型"""
    url: str
    auth_type: Optional[str] = ""
    auth_token: Optional[str] = None
    api_key_header: Optional[str] = None


class MCPTestResponse(BaseModel):
    """MCP服务器测试响应模型"""
    healthy: bool
    tools: List[Dict[str, Any]]
    error: Optional[str] = None