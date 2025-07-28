"""MCP Server schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class MCPServerCreate(BaseModel):
    """创建MCP服务器的schema"""
    server_name: str
    server_uri: str
    server_description: Optional[str] = None


class MCPServerUpdate(BaseModel):
    """更新MCP服务器的schema"""
    server_name: Optional[str] = None
    server_uri: Optional[str] = None
    server_description: Optional[str] = None
    is_enabled: Optional[str] = None


class MCPServerResponse(BaseModel):
    """MCP服务器响应schema"""
    id: int
    server_id: str
    server_name: str
    server_uri: str
    server_description: Optional[str]
    server_tools: str  # JSON string
    connection_status: str
    is_enabled: str
    create_by: str
    update_by: Optional[str]
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class MCPTestRequest(BaseModel):
    """测试MCP服务器连接的请求schema"""
    server_uri: str
    timeout: int = 10


class MCPTestResponse(BaseModel):
    """测试MCP服务器连接的响应schema"""
    success: bool
    message: str
    tools: List[Dict[str, Any]]
    server_uri: str