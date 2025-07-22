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
    print(f"测试连接到 {req.url}")
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
    
    try:
        print(f"实际连接到: {test_url}")
        async with Client(test_url) as client:
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
        return MCPTestResponse(healthy=False, tools=[], error=str(e))
