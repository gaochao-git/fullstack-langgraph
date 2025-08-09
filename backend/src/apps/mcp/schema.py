"""MCP Server schemas - 增强验证"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator,validator
import json


class MCPServerCreate(BaseModel):
    """创建MCP服务器的schema"""
    server_id: str = Field(..., description="服务器唯一标识", min_length=1, max_length=100, 
                          pattern=r'^[a-zA-Z0-9_-]+$')
    server_name: str = Field(..., description="服务器名称", min_length=1, max_length=200)
    server_uri: str = Field(..., description="服务器URI", min_length=1, max_length=500)
    transport_type: Optional[str] = Field("streamable-http", description="传输类型", max_length=50)
    server_description: Optional[str] = Field(None, description="服务器描述", max_length=1000)
    is_enabled: Optional[Literal["on", "off"]] = Field("on", description="是否启用")
    connection_status: Optional[Literal["connected", "disconnected", "error"]] = Field(
        "disconnected", description="连接状态")
    auth_type: Optional[str] = Field(None, description="认证类型", max_length=20)
    auth_token: Optional[str] = Field(None, description="认证令牌", max_length=500)
    api_key_header: Optional[str] = Field(None, description="API密钥头", max_length=100)
    read_timeout_seconds: Optional[int] = Field(5, description="读取超时秒数", ge=1, le=300)
    server_tools: Optional[List[Dict[str, Any]]] = Field(None, description="服务器工具列表", max_items=100)
    server_config: Optional[Dict[str, Any]] = Field(None, description="服务器配置")
    team_name: str = Field(..., description="团队名称", min_length=1, max_length=100)
    
    @field_validator('server_uri')
    def validate_server_uri(cls, v):
        """验证服务器URI格式"""
        if not (v.startswith('http://') or v.startswith('https://') or ':' in v):
            raise ValueError('服务器URI必须是有效的HTTP/HTTPS URL或host:port格式')
        if not (v.endswith('/sse') or v.endswith('/mcp')):
            raise ValueError('结尾类型必须是/sse或/mcp')
        return v


class MCPServerUpdate(BaseModel):
    """更新MCP服务器的schema"""
    server_name: Optional[str] = Field(None, description="服务器名称", min_length=1, max_length=200)
    server_uri: Optional[str] = Field(None, description="服务器URI", min_length=1, max_length=500)
    transport_type: Optional[str] = Field(None, description="传输类型", max_length=50)
    server_description: Optional[str] = Field(None, description="服务器描述", max_length=1000)
    is_enabled: Optional[Literal["on", "off"]] = Field(None, description="是否启用")
    connection_status: Optional[Literal["connected", "disconnected", "error"]] = Field(
        None, description="连接状态")
    auth_type: Optional[str] = Field(None, description="认证类型", max_length=20)
    auth_token: Optional[str] = Field(None, description="认证令牌", max_length=500)
    api_key_header: Optional[str] = Field(None, description="API密钥头", max_length=100)
    read_timeout_seconds: Optional[int] = Field(None, description="读取超时秒数", ge=1, le=300)
    server_tools: Optional[List[Dict[str, Any]]] = Field(None, description="服务器工具列表", max_items=100)
    server_config: Optional[Dict[str, Any]] = Field(None, description="服务器配置")
    team_name: Optional[str] = Field(None, description="团队名称", min_length=1, max_length=100)
    
    @field_validator('server_uri')
    def validate_server_uri(cls, v):
        """验证服务器URI格式"""
        if not (v.startswith('http://') or v.startswith('https://') or ':' in v):
            raise ValueError('服务器URI必须是有效的HTTP/HTTPS URL或host:port格式')
        if not (v.endswith('/sse') or v.endswith('/mcp')):
            raise ValueError('结尾类型必须是/sse或/mcp')
        return v


class MCPServerResponse(BaseModel):
    """MCP服务器响应schema"""
    id: int
    server_id: str
    server_name: str
    server_uri: str
    transport_type: str
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
    server_uri: str = Field(..., alias="url", description="服务器URI", min_length=1, max_length=500)
    timeout: int = Field(10, description="超时时间", ge=1, le=60)
    
    @field_validator('server_uri')
    def validate_server_uri(cls, v):
        """验证服务器URI格式"""
        if not (v.startswith('http://') or v.startswith('https://') or ':' in v):
            raise ValueError('服务器URI必须是有效的HTTP/HTTPS URL或host:port格式')
        if not (v.endswith('/sse') or v.endswith('/mcp')):
            raise ValueError('结尾类型必须是/sse或/mcp')
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


class SimpleAPIExample(BaseModel):
    """简单API案例"""
    http_url: str = Field(..., description="完整HTTP请求地址", min_length=1, max_length=1000)
    method: str = Field("GET", description="HTTP方法", pattern=r'^(GET|POST|PUT|DELETE|PATCH)$')
    description: Optional[str] = Field(None, description="API描述", max_length=500)
    request_params: Optional[str] = Field(None, description="请求参数案例(JSON字符串)", max_length=5000)
    request_body: Optional[str] = Field(None, description="请求体案例(JSON字符串)", max_length=5000)
    response_example: Optional[str] = Field(None, description="返回结果案例(JSON字符串)", max_length=10000)
    
    @field_validator('http_url')
    def validate_http_url(cls, v):
        """验证HTTP URL格式"""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('HTTP URL必须以http://或https://开头')
        return v
    
    @field_validator('request_params', 'request_body', 'response_example')
    def validate_json_strings(cls, v):
        """验证JSON字符串格式"""
        if v:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('必须是有效的JSON格式')
        return v


class AIGenerateOpenAPIRequest(BaseModel):
    """AI生成OpenAPI规范请求schema"""
    api_name: str = Field(..., description="API服务名称", min_length=1, max_length=100)
    api_description: Optional[str] = Field(None, description="API服务描述", max_length=1000)
    examples: List[SimpleAPIExample] = Field(..., description="API使用案例列表", min_items=1, max_items=20)
    template_type: Optional[str] = Field("standard", description="生成模板类型", pattern=r'^(standard|restful|minimal)$')
    
    @field_validator('examples')
    def validate_examples(cls, v):
        """验证案例列表"""
        if not v:
            raise ValueError('至少需要提供一个API使用案例')
        return v


class AIGenerateOpenAPIResponse(BaseModel):
    """AI生成OpenAPI规范响应schema"""
    openapi_spec: Dict[str, Any] = Field(..., description="生成的OpenAPI规范")
    generated_endpoints: int = Field(..., description="生成的端点数量")
    api_summary: str = Field(..., description="API功能总结")


# MCP Gateway 配置相关Schema
class MCPGatewayConfigCreate(BaseModel):
    """创建MCP Gateway配置"""
    name: str = Field(..., description="配置名称", min_length=1, max_length=50)
    tenant: str = Field("default", description="租户名称", min_length=1, max_length=50)
    routers: Optional[List[Dict[str, Any]]] = Field([], description="路由配置")
    servers: Optional[List[Dict[str, Any]]] = Field([], description="服务器配置")
    tools: Optional[List[Dict[str, Any]]] = Field([], description="工具配置")
    prompts: Optional[List[Dict[str, Any]]] = Field([], description="提示词配置")
    mcp_servers: Optional[List[Dict[str, Any]]] = Field([], description="MCP服务器配置")
    create_by: str = Field(..., description="创建者", min_length=1, max_length=100)

    @field_validator('name')
    def validate_name(cls, v):
        """验证配置名称"""
        if not v or not v.strip():
            raise ValueError("配置名称不能为空")
        # 只允许字母、数字、下划线、连字符
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("配置名称只能包含字母、数字、下划线和连字符")
        return v.strip()

    @field_validator('tenant')
    def validate_tenant(cls, v):
        """验证租户名称"""
        if not v or not v.strip():
            raise ValueError("租户名称不能为空")
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("租户名称只能包含字母、数字、下划线和连字符")
        return v.strip()


class MCPGatewayConfigUpdate(BaseModel):
    """更新MCP Gateway配置"""
    name: Optional[str] = Field(None, description="配置名称", min_length=1, max_length=50)
    tenant: Optional[str] = Field(None, description="租户名称", min_length=1, max_length=50)
    routers: Optional[List[Dict[str, Any]]] = Field(None, description="路由配置")
    servers: Optional[List[Dict[str, Any]]] = Field(None, description="服务器配置")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="工具配置")
    prompts: Optional[List[Dict[str, Any]]] = Field(None, description="提示词配置")
    mcp_servers: Optional[List[Dict[str, Any]]] = Field(None, description="MCP服务器配置")
    update_by: Optional[str] = Field(None, description="更新者", min_length=1, max_length=100)

    @field_validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("配置名称不能为空")
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("配置名称只能包含字母、数字、下划线和连字符")
            return v.strip()
        return v

    @field_validator('tenant')
    def validate_tenant(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("租户名称不能为空")
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("租户名称只能包含字母、数字、下划线和连字符")
            return v.strip()
        return v


class MCPGatewayConfigResponse(BaseModel):
    """MCP Gateway配置响应"""
    id: int
    config_id: str
    name: str
    tenant: str
    routers: List[Dict[str, Any]]
    servers: List[Dict[str, Any]]
    tools: List[Dict[str, Any]]
    prompts: List[Dict[str, Any]]
    mcp_servers: List[Dict[str, Any]]
    is_deleted: int
    create_by: str
    update_by: Optional[str]
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class MCPGatewayConfigQueryParams(BaseModel):
    """MCP Gateway配置查询参数"""
    name: Optional[str] = Field(None, description="配置名称过滤", max_length=50)
    tenant: Optional[str] = Field(None, description="租户名称过滤", max_length=50)
    create_by: Optional[str] = Field(None, description="创建者过滤", max_length=100)
    limit: Optional[int] = Field(10, description="返回数量", ge=1, le=100)
    offset: Optional[int] = Field(0, description="偏移量", ge=0)


class MCPGatewayConfigExport(BaseModel):
    """MCP Gateway配置导出格式"""
    name: str
    tenant: str
    createdAt: str
    updatedAt: str
    routers: List[Dict[str, Any]]
    servers: List[Dict[str, Any]]
    tools: List[Dict[str, Any]]
    prompts: List[Dict[str, Any]]
    mcpServers: List[Dict[str, Any]]