"""MCP Server管理路由 - 使用统一响应格式"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import aiohttp
import logging

from src.shared.db.config import get_async_db
from src.apps.mcp.schema.mcp import (
    MCPServerCreate, MCPServerUpdate, MCPQueryParams,
    MCPTestRequest, MCPTestResponse, MCPStatusUpdate, MCPEnableUpdate
)
from src.apps.mcp.service.mcp_service import mcp_service
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException
from src.shared.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["MCP Server Management"])


async def _test_mcp_connection(server_uri: str, timeout: int = 10) -> List[dict]:
    """测试MCP服务器连接并发现工具"""
    try:
        # 处理MCP服务器URI格式
        if server_uri.startswith('http://') or server_uri.startswith('https://'):
            if server_uri.endswith('/sse') or server_uri.endswith('/stdio'):
                http_url = server_uri + '/'
            elif server_uri.endswith('/sse/') or server_uri.endswith('/stdio/'):
                http_url = server_uri
            else:
                http_url = server_uri.rstrip('/') + '/sse/'
        else:
            http_url = f"http://{server_uri}/sse/"
        
        logger.info(f"测试MCP连接: {server_uri} -> {http_url}")
        
        # 使用FastMCP客户端连接
        try:
            from fastmcp import Client
            
            async with Client(http_url) as client:
                tools_info = await client.list_tools()
                
                tools = []
                if tools_info:
                    if hasattr(tools_info, 'tools'):
                        tool_list = tools_info.tools
                    elif isinstance(tools_info, list):
                        tool_list = tools_info
                    elif hasattr(tools_info, 'result') and hasattr(tools_info.result, 'tools'):
                        tool_list = tools_info.result.tools
                    else:
                        logger.warning(f"无法识别工具信息格式: {tools_info}")
                        tool_list = []
                    
                    for tool in tool_list:
                        tool_dict = {
                            "name": getattr(tool, 'name', str(tool)),
                            "description": getattr(tool, 'description', f"Tool: {getattr(tool, 'name', str(tool))}"),
                        }
                        if hasattr(tool, 'inputSchema'):
                            tool_dict["inputSchema"] = tool.inputSchema
                        tools.append(tool_dict)
                
                logger.info(f"成功连接MCP服务器 {server_uri}，发现 {len(tools)} 个工具")
                return tools
            
        except ImportError:
            logger.warning("fastmcp不可用，使用HTTP方式测试连接")
            return await _test_mcp_http_connection(http_url, timeout)
            
    except Exception as e:
        logger.error(f"MCP连接测试失败: {e}")
        raise Exception(f"无法连接到MCP服务器 {server_uri}: {str(e)}")


async def _test_mcp_http_connection(http_url: str, timeout: int = 10) -> List[dict]:
    """使用HTTP方式测试MCP连接（降级方案）"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            test_urls = [
                http_url + "health", 
                http_url + "tools/list",
                http_url.rstrip('/'),
            ]
            
            for url in test_urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            if "tools" in url:
                                data = await response.json()
                                if isinstance(data, list):
                                    return [{"name": tool.get("name", "unknown"), 
                                            "description": tool.get("description", "MCP Tool")} 
                                           for tool in data]
                            
                            logger.info(f"HTTP连接成功: {url}")
                            return [{"name": "mcp_tool", "description": "MCP Server Tool"}]
                except Exception as e:
                    logger.debug(f"尝试URL {url} 失败: {e}")
                    continue
            
            raise Exception("所有HTTP端点都无法访问")
            
    except Exception as e:
        raise Exception(f"HTTP连接测试失败: {str(e)}")


@router.post("/v1/mcp/servers", response_model=UnifiedResponse)
async def create_mcp_server(
    server_data: MCPServerCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建MCP服务器"""
    server = await mcp_service.create_server(db, server_data)
    return success_response(
        data=server,
        msg="MCP服务器创建成功",
        code=ResponseCode.CREATED
    )


@router.get("/v1/mcp/servers/{server_id}", response_model=UnifiedResponse)
async def get_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定MCP服务器"""
    server = await mcp_service.get_server_by_id(db, server_id)
    if not server:
        raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=server,
        msg="获取MCP服务器成功"
    )


@router.get("/v1/mcp/servers", response_model=UnifiedResponse)
async def list_mcp_servers(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    is_enabled: Optional[str] = Query(None, description="启用状态过滤"),
    connection_status: Optional[str] = Query(None, description="连接状态过滤"),
    team_name: Optional[str] = Query(None, max_length=100, description="团队过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """查询MCP服务器列表"""
    params = MCPQueryParams(
        search=search,
        is_enabled=is_enabled,
        connection_status=connection_status,
        team_name=team_name,
        limit=size,
        offset=(page - 1) * size
    )
    
    servers, total = await mcp_service.list_servers(db, params)
    
    return paginated_response(
        items=servers,
        total=total,
        page=page,
        size=size,
        msg="查询MCP服务器列表成功"
    )


@router.put("/v1/mcp/servers/{server_id}", response_model=UnifiedResponse)
async def update_mcp_server(
    server_id: str,
    server_data: MCPServerUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新MCP服务器"""
    updated_server = await mcp_service.update_server(db, server_id, server_data)
    if not updated_server:
        raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_server,
        msg="MCP服务器更新成功"
    )


@router.delete("/v1/mcp/servers/{server_id}", response_model=UnifiedResponse)
async def delete_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """删除MCP服务器"""
    success = await mcp_service.delete_server(db, server_id)
    if not success:
        raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_id": server_id},
        msg="MCP服务器删除成功"
    )


@router.post("/v1/mcp/servers/{server_id}/test", response_model=UnifiedResponse)
async def test_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """测试MCP服务器连接"""
    server = await mcp_service.get_server_by_id(db, server_id)
    if not server:
        raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
    
    try:
        timeout = server.read_timeout_seconds if server.read_timeout_seconds else 5
        tools = await _test_mcp_connection(server.server_uri, timeout)
        
        # 更新连接状态和工具列表
        await mcp_service.update_connection_status(db, server_id, "connected")
        if tools:
            await mcp_service.update_server_tools(db, server_id, [tool["name"] for tool in tools])
        
        return success_response(
            data={
                "healthy": True,
                "tools": tools,
                "error": None
            },
            msg="MCP服务器连接测试成功"
        )
    except Exception as e:
        # 更新连接状态为错误
        await mcp_service.update_connection_status(db, server_id, "error")
        
        return success_response(
            data={
                "healthy": False,
                "tools": [],
                "error": str(e)
            },
            msg="MCP服务器连接测试失败"
        )


@router.patch("/v1/mcp/servers/{server_id}/status", response_model=UnifiedResponse)
async def update_server_status(
    server_id: str,
    status_data: MCPStatusUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新MCP服务器状态"""
    updated_server = await mcp_service.update_connection_status(db, server_id, status_data.status)
    if not updated_server:
        raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_server,
        msg=f"服务器状态已更新为 {status_data.status}"
    )


@router.patch("/v1/mcp/servers/{server_id}/enable", response_model=UnifiedResponse)
async def toggle_server_enable(
    server_id: str,
    enable_data: MCPEnableUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """启用/禁用MCP服务器"""
    update_data = MCPServerUpdate(is_enabled=enable_data.enabled)
    updated_server = await mcp_service.update_server(db, server_id, update_data)
    if not updated_server:
        raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
    
    action = "启用" if enable_data.enabled == "on" else "禁用"
    return success_response(
        data=updated_server,
        msg=f"服务器已{action}成功"
    )


@router.get("/v1/mcp/servers/meta/teams", response_model=UnifiedResponse)
async def get_mcp_teams(
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有MCP团队"""
    teams = await mcp_service.get_teams(db)
    return success_response(
        data=teams,
        msg="获取MCP团队成功"
    )


@router.get("/v1/mcp/servers/meta/statistics", response_model=UnifiedResponse)
async def get_mcp_statistics(
    db: AsyncSession = Depends(get_async_db)
):
    """获取MCP统计信息"""
    statistics = await mcp_service.get_status_statistics(db)
    return success_response(
        data=statistics,
        msg="获取MCP统计信息成功"
    )


@router.post("/v1/mcp/test", response_model=UnifiedResponse)
async def test_server_connection(
    test_request: MCPTestRequest
):
    """通用MCP服务器连接测试接口"""
    try:
        tools = await _test_mcp_connection(test_request.server_uri, test_request.timeout)
        
        return success_response(
            data={
                "healthy": True,
                "tools": tools,
                "error": None
            },
            msg="MCP连接测试成功"
        )
    except Exception as e:
        logger.error(f"MCP连接测试失败 {test_request.server_uri}: {e}")
        return success_response(
            data={
                "healthy": False,
                "tools": [],
                "error": str(e)
            },
            msg="MCP连接测试失败"
        )