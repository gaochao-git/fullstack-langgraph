from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Any

# fastmcp 需提前 pip install
try:
    from fastmcp import Client
except ImportError:
    Client = None

router = APIRouter(prefix="/api/mcp", tags=["MCP"])

class MCPTestRequest(BaseModel):
    url: str
    authType: str = "none"
    authToken: Optional[str] = None
    apiKeyHeader: Optional[str] = None

class MCPToolInfo(BaseModel):
    name: str
    description: Optional[str] = None
    inputSchema: Optional[Any] = None

class MCPTestResponse(BaseModel):
    healthy: bool
    tools: List[MCPToolInfo] = []
    error: Optional[str] = None

@router.post("/test_server", response_model=MCPTestResponse)
async def test_mcp_server(req: MCPTestRequest):
    print(f"测试连接到 {req.url}，认证方式: {req.authType}")
    if Client is None:
        return MCPTestResponse(healthy=False, tools=[], error="fastmcp 未安装，请先 pip install fastmcp")
    
    # 处理 URL 格式，确保 HTTP 类型的 URL 有正确的 SSE 端点
    test_url = req.url
    if test_url.startswith("http://") or test_url.startswith("https://"):
        # 如果是 HTTP URL，确保末尾有 /sse/
        if not test_url.endswith("/sse/") and not test_url.endswith("/sse"):
            if test_url.endswith("/"):
                test_url += "sse/"
            else:
                test_url += "/sse/"
    
    # 构建认证头
    headers = {}
    if req.authType == "bearer" and req.authToken:
        headers["Authorization"] = f"Bearer {req.authToken}"
    elif req.authType == "basic" and req.authToken:
        headers["Authorization"] = f"Basic {req.authToken}"
    elif req.authType == "api_key" and req.authToken and req.apiKeyHeader:
        headers[req.apiKeyHeader] = req.authToken
    
    try:
        print(f"实际连接到: {test_url}")
        print(f"使用认证头: {list(headers.keys()) if headers else 'None'}")
        
        # 创建客户端时传入认证头
        client_kwargs = {"headers": headers} if headers else {}
        async with Client(test_url, **client_kwargs) as client:
            tools = await client.list_tools()
            tool_list = [
                MCPToolInfo(
                    name=getattr(tool, "name", None),
                    description=getattr(tool, "description", None),
                    inputSchema=getattr(tool, "inputSchema", None)
                )
                for tool in tools
            ]
            return MCPTestResponse(healthy=True, tools=tool_list)
    except Exception as e:
        error_msg = str(e)
        print(f"连接错误: {error_msg}")
        return MCPTestResponse(healthy=False, tools=[], error=error_msg)
