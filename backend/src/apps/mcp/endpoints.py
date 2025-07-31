"""MCP Server管理路由 - 使用统一响应格式"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import aiohttp
import logging

from src.shared.db.config import get_async_db
from src.apps.mcp.schema import (
    MCPServerCreate, MCPServerUpdate, MCPQueryParams,
    MCPTestRequest, MCPTestResponse, MCPStatusUpdate, MCPEnableUpdate,
    OpenAPIMCPConfigCreate, OpenAPIMCPConfigUpdate
)
from src.apps.mcp.service.mcp_service import mcp_service
from src.apps.mcp.service.openapi_mcp_service import OpenAPIMCPConfigService
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException
from src.shared.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["MCP Server Management"])

# 服务实例
openapi_mcp_service = OpenAPIMCPConfigService()


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
        
        # 更新连接状态和工具列表 - 使用单一事务
        async with db.begin():
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
        async with db.begin():
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


# OpenAPI MCP 配置管理端点
@router.post("/v1/mcp/openapi/configs", response_model=UnifiedResponse)
async def create_openapi_config(
    config_data: OpenAPIMCPConfigCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建 OpenAPI MCP 配置"""
    try:
        config_record = await openapi_mcp_service.create_config(db, config_data)
        
        return success_response(
            data=config_record.to_dict(),
            msg="OpenAPI MCP 配置创建成功",
            code=ResponseCode.CREATED
        )
    except ValueError as e:
        raise BusinessException(str(e), ResponseCode.BAD_REQUEST)
    except Exception as e:
        logger.error(f"创建OpenAPI MCP配置失败: {str(e)}")
        raise BusinessException("创建配置失败", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/mcp/openapi/configs", response_model=UnifiedResponse)
async def list_openapi_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    mcp_server_prefix: Optional[str] = Query(None, description="服务器前缀过滤"),
    mcp_tool_enabled: Optional[int] = Query(None, description="工具启用状态过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取 OpenAPI MCP 配置列表"""
    try:
        configs, total = await openapi_mcp_service.list_configs(
            db, 
            offset=(page - 1) * size,
            limit=size,
            mcp_server_prefix=mcp_server_prefix,
            mcp_tool_enabled=mcp_tool_enabled
        )
        config_list = [config.to_dict() for config in configs]
        
        return paginated_response(
            items=config_list,
            total=total,
            page=page,
            size=size,
            msg="获取配置列表成功"
        )
    except Exception as e:
        logger.error(f"获取OpenAPI配置列表失败: {str(e)}")
        raise BusinessException("获取配置列表失败", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/mcp/openapi/configs/{config_id}", response_model=UnifiedResponse)
async def get_openapi_config(
    config_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定的 OpenAPI MCP 配置"""
    try:
        config = await openapi_mcp_service.get_config(db, config_id)
        if not config:
            raise BusinessException(f"配置 {config_id} 不存在", ResponseCode.NOT_FOUND)
        
        return success_response(
            data=config.to_dict(),
            msg="获取配置成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取OpenAPI配置失败: {str(e)}")
        raise BusinessException("获取配置失败", ResponseCode.INTERNAL_ERROR)


@router.put("/v1/mcp/openapi/configs/{config_id}", response_model=UnifiedResponse)
async def update_openapi_config(
    config_id: int,
    config_data: OpenAPIMCPConfigUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新 OpenAPI MCP 配置"""
    try:
        updated_config = await openapi_mcp_service.update_config(db, config_id, config_data)
        if not updated_config:
            raise BusinessException(f"配置 {config_id} 不存在", ResponseCode.NOT_FOUND)
        
        return success_response(
            data=updated_config.to_dict(),
            msg="配置更新成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"更新OpenAPI配置失败: {str(e)}")
        raise BusinessException("更新配置失败", ResponseCode.INTERNAL_ERROR)


@router.delete("/v1/mcp/openapi/configs/{config_id}", response_model=UnifiedResponse)
async def delete_openapi_config(
    config_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """删除 OpenAPI MCP 配置（软删除）"""
    try:
        success = await openapi_mcp_service.delete_config(db, config_id)
        if not success:
            raise BusinessException(f"配置 {config_id} 不存在", ResponseCode.NOT_FOUND)
        
        return success_response(
            data={"deleted": True},
            msg="配置删除成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"删除OpenAPI配置失败: {str(e)}")
        raise BusinessException("删除配置失败", ResponseCode.INTERNAL_ERROR)


@router.patch("/v1/mcp/openapi/configs/{config_id}/enable", response_model=UnifiedResponse)
async def toggle_config_enable(
    config_id: int,
    enabled: bool,
    db: AsyncSession = Depends(get_async_db)
):
    """启用/禁用 OpenAPI MCP 配置"""
    try:
        updated_config = await openapi_mcp_service.toggle_enable(db, config_id, enabled)
        if not updated_config:
            raise BusinessException(f"配置 {config_id} 不存在", ResponseCode.NOT_FOUND)
        
        action = "启用" if enabled else "禁用"
        return success_response(
            data=updated_config.to_dict(),
            msg=f"配置已{action}成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"切换配置状态失败: {str(e)}")
        raise BusinessException("切换配置状态失败", ResponseCode.INTERNAL_ERROR)


# =============================================================================
# MCP 工具接口 - 实际的业务逻辑接口
# =============================================================================
import platform
import psutil
import os
from datetime import datetime
from typing import Dict, Any, List as TypingList


@router.post("/v1/mcp/tools/system_info", response_model=UnifiedResponse)
async def get_system_info():
    """获取系统信息 - MCP工具接口"""
    try:
        # 获取系统基础信息
        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            
            # 内存信息
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used,
                "free": psutil.virtual_memory().free
            },
            
            # CPU信息
            "cpu": {
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
                "percent": psutil.cpu_percent(interval=1),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            
            # 磁盘信息
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            
            "timestamp": datetime.now().isoformat()
        }
        
        return success_response(
            data=system_info,
            msg="获取系统信息成功"
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        raise BusinessException("获取系统信息失败", ResponseCode.INTERNAL_ERROR)


@router.post("/v1/mcp/tools/execute_command", response_model=UnifiedResponse)
async def execute_safe_command(
    command: str = Query(..., description="要执行的命令"),
    timeout: int = Query(10, description="超时时间（秒）")
):
    """执行安全的系统命令 - MCP工具接口"""
    try:
        # 安全命令白名单
        safe_commands = [
            "ls", "pwd", "whoami", "date", "uptime", "df", "free", 
            "ps", "top", "uname", "id", "echo", "cat", "head", "tail"
        ]
        
        # 提取命令名（第一个参数）
        cmd_name = command.split()[0] if command.split() else ""
        
        if cmd_name not in safe_commands:
            raise BusinessException(f"命令 '{cmd_name}' 不在安全列表中", ResponseCode.BAD_REQUEST)
        
        # 执行命令
        import subprocess
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return success_response(
            data={
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            },
            msg="命令执行成功"
        )
    except subprocess.TimeoutExpired:
        raise BusinessException("命令执行超时", ResponseCode.BAD_REQUEST)
    except Exception as e:
        logger.error(f"命令执行失败: {str(e)}")
        raise BusinessException(f"命令执行失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/mcp/tools/list_files", response_model=UnifiedResponse)
async def list_files(
    path: str = Query(".", description="目录路径"),
    show_hidden: bool = Query(False, description="显示隐藏文件")
):
    """列出目录文件 - MCP工具接口"""
    try:
        if not os.path.exists(path):
            raise BusinessException(f"路径不存在: {path}", ResponseCode.NOT_FOUND)
        
        if not os.path.isdir(path):
            raise BusinessException(f"不是目录: {path}", ResponseCode.BAD_REQUEST)
        
        files = []
        for item in os.listdir(path):
            if not show_hidden and item.startswith('.'):
                continue
                
            item_path = os.path.join(path, item)
            stat = os.stat(item_path)
            
            files.append({
                "name": item,
                "path": item_path,
                "is_dir": os.path.isdir(item_path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            })
        
        return success_response(
            data={
                "path": path,
                "files": sorted(files, key=lambda x: (not x["is_dir"], x["name"])),
                "total": len(files)
            },
            msg="文件列表获取成功"
        )
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise BusinessException(f"获取文件列表失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


# =============================================================================
# MCP Gateway 配置端点 - 为 MCP Gateway 提供配置数据
# =============================================================================


@router.get("/v1/mcp/gateway/configs", response_model=UnifiedResponse)
async def get_gateway_configs(
    since: Optional[str] = Query(None, description="增量更新时间戳 (ISO 8601)"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    为MCP Gateway提供配置数据
    支持全量和增量拉取
    """
    try:
        # 解析since参数
        since_datetime = None
        if since:
            try:
                since_datetime = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise BusinessException("时间格式错误，请使用ISO 8601格式", ResponseCode.BAD_REQUEST)
        
        # 获取MCP服务器列表
        params = MCPQueryParams(
            is_enabled="on",  # 只返回启用的服务器
            limit=1000,      # 大量限制
            offset=0
        )
        
        servers, total = await mcp_service.list_servers(db, params)
        
        # 过滤增量更新
        if since_datetime:
            servers = [s for s in servers if s.update_time > since_datetime]
            logger.info(f"增量更新: 找到 {len(servers)} 个更新的MCP服务器 (since: {since_datetime})")
        else:
            logger.info(f"全量拉取: 返回 {len(servers)} 个MCP服务器")
        
        # 构建MCP Gateway配置格式
        configs = []
        for server in servers:
            config = _build_gateway_config(server)
            configs.append(config)
        
        return success_response(
            data={"configs": configs},
            msg=f"获取MCP Gateway配置成功 (共{len(configs)}个)"
        )
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取MCP Gateway配置失败: {str(e)}")
        raise BusinessException("获取配置失败", ResponseCode.INTERNAL_ERROR)


def _build_gateway_config(server) -> Dict[str, Any]:
    """
    将数据库中的MCP服务器转换为MCP Gateway需要的配置格式
    """
    import json
    
    # 解析服务器工具
    server_tools = []
    if server.server_tools:
        try:
            if isinstance(server.server_tools, str):
                server_tools = json.loads(server.server_tools)
            elif isinstance(server.server_tools, list):
                server_tools = server.server_tools
        except:
            server_tools = []
    
    # 解析服务器配置
    server_config = {}
    if server.server_config:
        try:
            if isinstance(server.server_config, str):
                server_config = json.loads(server.server_config)
            elif isinstance(server.server_config, dict):
                server_config = server.server_config
        except:
            server_config = {}
    
    # 构建配置
    config = {
        "name": f"config-{server.server_id}",
        "tenant": server.team_name or "default", 
        "createdAt": server.create_time.isoformat() if server.create_time else datetime.now().isoformat(),
        "updatedAt": server.update_time.isoformat() if server.update_time else datetime.now().isoformat(),
        
        # 路由配置 - 定义HTTP路径映射
        "routers": [{
            "server": f"server-{server.server_id}",
            "prefix": f"/{server.server_id}",
            "ssePrefix": f"/{server.server_id}",
            "cors": {
                "allowOrigins": ["*"],
                "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allowHeaders": ["Content-Type", "Authorization", "Mcp-Session-Id"],
                "exposeHeaders": ["Mcp-Session-Id"],
                "allowCredentials": True
            }
        }],
        
        # 服务器配置 - 基本信息
        "servers": [{
            "name": f"server-{server.server_id}",
            "description": server.server_description or f"MCP Server: {server.server_name}",
            "allowedTools": server_tools,
            "config": server_config
        }],
        
        # MCP服务器配置 - 核心配置
        "mcpServers": [{
            "type": _detect_transport_type(server.server_uri),
            "name": f"server-{server.server_id}",
            "policy": "onStart",
            "preinstalled": True,
            **_build_transport_config(server)
        }],
        
        # 工具配置 - 如果有自定义工具
        "tools": _build_tools_config(server, server_tools),
        
        # 提示词配置 - 暂时为空
        "prompts": []
    }
    
    return config


def _detect_transport_type(server_uri: str) -> str:
    """检测传输类型"""
    if not server_uri:
        return "stdio"
    
    if server_uri.startswith(('http://', 'https://')):
        if '/sse' in server_uri:
            return "sse"
        else:
            return "streamable-http"
    else:
        return "stdio"


def _build_transport_config(server) -> Dict[str, Any]:
    """构建传输配置"""
    transport_type = _detect_transport_type(server.server_uri)
    
    if transport_type == "stdio":
        # 如果是命令行模式
        if server.server_uri and ' ' in server.server_uri:
            # 解析命令和参数 "python /path/to/server.py"
            parts = server.server_uri.split()
            return {
                "command": parts[0],
                "args": parts[1:] if len(parts) > 1 else [],
                "env": {}
            }
        else:
            return {
                "command": server.server_uri or "python",
                "args": [],
                "env": {}
            }
    else:
        # HTTP/SSE模式
        return {
            "url": server.server_uri
        }


def _build_tools_config(server, server_tools: TypingList[str]) -> TypingList[Dict[str, Any]]:
    """构建工具配置 - 为REST API转MCP工具提供配置"""
    tools = []
    
    # 为每个工具创建基本配置
    for tool_name in server_tools:
        tool_config = {
            "name": tool_name,
            "description": f"Tool from {server.server_name}: {tool_name}",
            "method": "POST",
            "endpoint": f"http://localhost:5235/{server.server_id}/mcp",
            "headers": {
                "Content-Type": "application/json",
                "Mcp-Session-Id": "{{session.id}}"
            },
            "requestBody": "{{request.body}}",
            "responseBody": "{{response.body}}",
            "args": [{
                "name": "input",
                "position": "body", 
                "required": True,
                "type": "object",
                "description": f"Input for {tool_name}"
            }]
        }
        tools.append(tool_config)
    
    return tools


@router.get("/v1/mcp/gateway/configs/mock", response_model=UnifiedResponse)
async def get_mock_gateway_configs():
    """
    返回Mock MCP Gateway配置数据 - 用于测试
    """
    mock_configs = [
        {
            "name": "database-tools",
            "tenant": "default",
            "createdAt": datetime.now().isoformat() + "Z",
            "updatedAt": datetime.now().isoformat() + "Z",
            "routers": [{
                "server": "db-server",
                "prefix": "/db",
                "ssePrefix": "",
                "cors": {
                    "allowOrigins": ["*"],
                    "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allowHeaders": ["Content-Type", "Authorization", "Mcp-Session-Id"],
                    "exposeHeaders": ["Mcp-Session-Id"],
                    "allowCredentials": True
                }
            }],
            "servers": [{
                "name": "db-server",
                "description": "Database MCP Server",
                "allowedTools": ["execute_sql"],
                "config": {
                    "database_type": "mysql",
                    "max_connections": "10"
                }
            }],
            "mcpServers": [{
                "type": "stdio",
                "name": "db-server",
                "command": "python",
                "args": ["/path/to/db_mcp_server.py"],
                "env": {
                    "DB_HOST": "localhost",
                    "DB_PORT": "3306"
                },
                "policy": "onDemand",
                "preinstalled": False
            }],
            "tools": [{
                "name": "execute_sql",
                "description": "Execute SQL query on database",
                "method": "POST",
                "endpoint": "http://localhost:5235/db/mcp",
                "headers": {
                    "Content-Type": "application/json"
                },
                "requestBody": '{"method": "tools/call", "params": {"name": "execute_sql", "arguments": {{args}}}}',
                "responseBody": "SQL执行结果: {{response.result}}",
                "args": [{
                    "name": "query",
                    "position": "body",
                    "required": True,
                    "type": "string",
                    "description": "SQL query to execute"
                }]
            }],
            "prompts": []
        },
        {
            "name": "system-tools", 
            "tenant": "default",
            "createdAt": datetime.now().isoformat() + "Z",
            "updatedAt": datetime.now().isoformat() + "Z",
            "routers": [{
                "server": "system-server",
                "prefix": "/system",
                "ssePrefix": "",
                "cors": {
                    "allowOrigins": ["*"],
                    "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allowHeaders": ["Content-Type", "Authorization", "Mcp-Session-Id"],
                    "exposeHeaders": ["Mcp-Session-Id"],
                    "allowCredentials": True
                }
            }],
            "servers": [{
                "name": "system-server",
                "description": "System Operations MCP Server - Real Backend APIs",
                "allowedTools": ["system_info", "execute_command", "list_files"],
                "config": {
                    "backend_base_url": "http://localhost:8000",
                    "timeout": "30"
                }
            }],
            "mcpServers": [{
                "type": "streamable-http",
                "name": "system-server", 
                "url": "http://localhost:8000/api",
                "policy": "onDemand",
                "preinstalled": False
            }],
            "tools": [
                {
                    "name": "system_info",
                    "description": "获取系统信息，包括CPU、内存、磁盘使用情况",
                    "method": "POST",
                    "endpoint": "http://localhost:8000/api/v1/mcp/tools/system_info",
                    "headers": {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    "requestBody": "{}",
                    "responseBody": "系统信息: {{response.data}}",
                    "args": []
                },
                {
                    "name": "execute_command",
                    "description": "执行安全的系统命令",
                    "method": "POST",
                    "endpoint": "http://localhost:8000/api/v1/mcp/tools/execute_command",
                    "headers": {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    "requestBody": '{"command": "{{args.command}}", "timeout": "{{args.timeout}}"}',
                    "responseBody": "命令执行结果: {{response.data}}",
                    "args": [
                        {
                            "name": "command",
                            "position": "body",
                            "required": True,
                            "type": "string",
                            "description": "要执行的命令 (仅支持安全命令: ls, pwd, whoami, date, uptime, df, free, ps, uname, id, echo)"
                        },
                        {
                            "name": "timeout",
                            "position": "body",
                            "required": False,
                            "type": "integer",
                            "description": "超时时间（秒），默认10秒"
                        }
                    ]
                },
                {
                    "name": "list_files",
                    "description": "列出指定目录的文件和文件夹",
                    "method": "GET",
                    "endpoint": "http://localhost:8000/api/v1/mcp/tools/list_files",
                    "headers": {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    "requestBody": "",
                    "responseBody": "文件列表: {{response.data}}",
                    "args": [
                        {
                            "name": "path",
                            "position": "query",
                            "required": False,
                            "type": "string",
                            "description": "目录路径，默认为当前目录"
                        },
                        {
                            "name": "show_hidden",
                            "position": "query",
                            "required": False,
                            "type": "boolean",
                            "description": "是否显示隐藏文件，默认false"
                        }
                    ]
                }
            ],
            "prompts": []
        }
    ]
    
    return success_response(
        data={"configs": mock_configs},
        msg=f"获取Mock配置成功 (共{len(mock_configs)}个)"
    )