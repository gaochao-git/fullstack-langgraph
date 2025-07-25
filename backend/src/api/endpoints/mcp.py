"""MCP Server management routes."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json
import uuid
import logging
import aiohttp
import asyncio

from ...db.config import get_db
from ...db.models import MCPServer
from ...schemas.mcp import MCPServerCreate, MCPServerUpdate, MCPServerResponse, MCPTestRequest, MCPTestResponse

logger = logging.getLogger(__name__)

router = APIRouter()


async def _test_mcp_connection(server_uri: str, timeout: int = 10) -> List[dict]:
    """测试MCP服务器连接并发现工具"""
    try:
        # 处理MCP服务器URI格式
        # 支持的格式:
        # - http://localhost:3001/sse
        # - https://localhost:3001/stdio  
        # - http://localhost:3001 (自动添加/sse/)
        
        if server_uri.startswith('http://') or server_uri.startswith('https://'):
            # 检查是否已经有传输方式后缀
            if server_uri.endswith('/sse') or server_uri.endswith('/stdio'):
                http_url = server_uri + '/'
            elif server_uri.endswith('/sse/') or server_uri.endswith('/stdio/'):
                http_url = server_uri
            else:
                # 默认添加/sse/后缀
                http_url = server_uri.rstrip('/') + '/sse/'
        else:
            # 兼容旧格式，假设是简单的host:port格式
            http_url = f"http://{server_uri}/sse/"
        
        logger.info(f"测试MCP连接: {server_uri} -> {http_url}")
        
        # 使用FastMCP客户端连接
        try:
            from fastmcp import Client
            
            # 创建客户端并连接
            async with Client(http_url) as client:
                # 获取工具列表
                tools_info = await client.list_tools()
                
                # 转换工具信息格式
                tools = []
                if tools_info:
                    # 尝试不同的访问方式
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
                        # 添加参数信息（如果有的话）
                        if hasattr(tool, 'inputSchema'):
                            tool_dict["inputSchema"] = tool.inputSchema
                        tools.append(tool_dict)
                
                logger.info(f"成功连接MCP服务器 {server_uri}，发现 {len(tools)} 个工具")
                return tools
            
        except ImportError:
            # 如果没有fastmcp，使用HTTP请求方式
            logger.warning("fastmcp不可用，使用HTTP方式测试连接")
            return await _test_mcp_http_connection(http_url, timeout)
            
    except Exception as e:
        logger.error(f"MCP连接测试失败: {e}")
        raise Exception(f"无法连接到MCP服务器 {server_uri}: {str(e)}")


async def _test_mcp_http_connection(http_url: str, timeout: int = 10) -> List[dict]:
    """使用HTTP方式测试MCP连接（降级方案）"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # 尝试健康检查
            test_urls = [
                http_url + "health", 
                http_url + "tools/list",
                http_url.rstrip('/'),  # 根路径
            ]
            
            for url in test_urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            # 如果是工具列表URL，尝试解析
                            if "tools" in url:
                                data = await response.json()
                                if isinstance(data, list):
                                    return [{"name": tool.get("name", "unknown"), 
                                            "description": tool.get("description", "MCP Tool")} 
                                           for tool in data]
                            
                            # 连接成功，返回默认工具信息
                            logger.info(f"HTTP连接成功: {url}")
                            return [
                                {"name": "mcp_tool", "description": "MCP Server Tool"}
                            ]
                except Exception as e:
                    logger.debug(f"尝试URL {url} 失败: {e}")
                    continue
            
            raise Exception("所有HTTP端点都无法访问")
            
    except Exception as e:
        raise Exception(f"HTTP连接测试失败: {str(e)}")


@router.get("/servers", response_model=List[MCPServerResponse])
async def get_mcp_servers(
    team_name: Optional[str] = None,
    is_enabled: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取MCP服务器列表"""
    query = db.query(MCPServer)
    
    if team_name:
        query = query.filter(MCPServer.team_name == team_name)
    
    if is_enabled:
        query = query.filter(MCPServer.is_enabled == is_enabled)
    
    servers = query.order_by(MCPServer.create_time.desc()).all()
    return [server.to_dict() for server in servers]


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(server_id: str, db: Session = Depends(get_db)):
    """获取单个MCP服务器详情"""
    server = db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return server.to_dict()


@router.post("/servers", response_model=MCPServerResponse)
async def create_mcp_server(server: MCPServerCreate, db: Session = Depends(get_db)):
    """创建MCP服务器"""
    # 检查server_id是否已存在
    existing_server = db.query(MCPServer).filter(MCPServer.server_id == server.server_id).first()
    if existing_server:
        raise HTTPException(status_code=400, detail="Server ID already exists")
    
    # 创建新服务器
    db_server = MCPServer(
        server_id=server.server_id,
        server_name=server.server_name,
        server_uri=server.server_uri,
        server_description=server.server_description,
        is_enabled=server.is_enabled,
        connection_status=server.connection_status,
        auth_type=server.auth_type,
        auth_token=server.auth_token,
        api_key_header=server.api_key_header,
        read_timeout_seconds=server.read_timeout_seconds,
        server_tools=json.dumps(server.server_tools) if server.server_tools else None,
        server_config=json.dumps(server.server_config) if server.server_config else None,
        team_name=server.team_name,
        create_by=server.create_by,
        create_time=datetime.utcnow(),
        update_time=datetime.utcnow()
    )
    
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    return db_server.to_dict()


@router.put("/servers/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: str, 
    server_update: MCPServerUpdate, 
    db: Session = Depends(get_db)
):
    """更新MCP服务器"""
    db_server = db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    # 更新字段
    update_data = server_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field in ['server_tools', 'server_config'] and value is not None:
            setattr(db_server, field, json.dumps(value))
        else:
            setattr(db_server, field, value)
    
    db_server.update_time = datetime.utcnow()
    
    db.commit()
    db.refresh(db_server)
    
    return db_server.to_dict()


@router.delete("/servers/{server_id}")
async def delete_mcp_server(server_id: str, db: Session = Depends(get_db)):
    """删除MCP服务器"""
    db_server = db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    db.delete(db_server)
    db.commit()
    
    return {"message": "MCP server deleted successfully"}


@router.post("/servers/{server_id}/test")
async def test_mcp_server(server_id: str, db: Session = Depends(get_db)):
    """测试MCP服务器连接"""
    db_server = db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    try:
        # 实际的MCP服务器连接测试，使用服务器配置的超时时间
        timeout = db_server.read_timeout_seconds if db_server.read_timeout_seconds else 5
        tools = await _test_mcp_connection(db_server.server_uri, timeout)
        
        # 更新连接状态为成功
        db_server.connection_status = "connected"
        db_server.update_time = datetime.utcnow()
        
        # 更新发现的工具
        if tools:
            db_server.server_tools = json.dumps(tools)
        
        db.commit()
        
        return {
            "healthy": True,
            "tools": tools,
            "error": None
        }
    except Exception as e:
        logger.error(f"MCP服务器连接测试失败 {db_server.server_uri}: {e}")
        
        # 更新连接状态为错误
        db_server.connection_status = "error"
        db_server.update_time = datetime.utcnow()
        db.commit()
        
        return {
            "healthy": False,
            "tools": [],
            "error": str(e)
        }


@router.patch("/servers/{server_id}/status")
async def update_server_status(
    server_id: str, 
    status: str, 
    db: Session = Depends(get_db)
):
    """更新MCP服务器状态"""
    db_server = db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    if status not in ['connected', 'disconnected', 'error']:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    db_server.connection_status = status
    db_server.update_time = datetime.utcnow()
    
    db.commit()
    db.refresh(db_server)
    
    return {"message": f"Server status updated to {status}"}


@router.patch("/servers/{server_id}/enable")
async def toggle_server_enable(
    server_id: str, 
    enabled: str, 
    db: Session = Depends(get_db)
):
    """启用/禁用MCP服务器"""
    db_server = db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    if enabled not in ['on', 'off']:
        raise HTTPException(status_code=400, detail="Invalid enabled value, must be 'on' or 'off'")
    
    db_server.is_enabled = enabled
    db_server.update_time = datetime.utcnow()
    
    db.commit()
    db.refresh(db_server)
    
    return {"message": f"Server {'enabled' if enabled == 'on' else 'disabled'} successfully"}


@router.post("/test_server", response_model=MCPTestResponse)
async def test_server_connection(test_request: MCPTestRequest):
    """通用MCP服务器连接测试接口"""
    try:
        # 实际的MCP服务器连接测试，使用默认超时时间10秒
        tools = await _test_mcp_connection(test_request.url, 10)
        
        return {
            "healthy": True,
            "tools": tools,
            "error": None
        }
    except Exception as e:
        logger.error(f"MCP连接测试失败 {test_request.url}: {e}")
        return {
            "healthy": False,
            "tools": [],
            "error": str(e)
        }