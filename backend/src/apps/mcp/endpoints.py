"""MCP Server管理路由 - 使用统一响应格式"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import aiohttp
import logging
import traceback

from src.shared.db.config import get_async_db
from src.apps.auth.dependencies import get_current_user
from src.apps.mcp.schema import (
    MCPServerCreate, MCPServerUpdate, MCPQueryParams,
    MCPTestRequest, MCPTestResponse, MCPStatusUpdate, MCPEnableUpdate,
    MCPGatewayConfigCreate, MCPGatewayConfigUpdate, MCPGatewayConfigQueryParams
)
from src.apps.mcp.service.mcp_service import mcp_service
from src.apps.mcp.service.mcp_gateway_service import mcp_gateway_service
from src.apps.mcp.service.mcp_reload_service import reload_mcp_gateway
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException
from src.shared.core.logging import get_logger
from src.shared.core.config import settings

logger = get_logger(__name__)
router = APIRouter(tags=["MCP Server Management"])


async def _test_mcp_connection(server_uri: str) -> List[dict]:
    """测试MCP服务器连接并发现工具"""
    try:
        logger.info(f"测试MCP连接: {server_uri}")
        # 使用FastMCP客户端连接
        from fastmcp import Client
        async with Client(server_uri) as client:
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
    except Exception as e:
        logger.error(f"MCP连接测试失败: {e}", exc_info=True)
        raise Exception(f"无法连接到MCP服务器 {server_uri}: {str(e)}")

@router.post("/v1/mcp/servers", response_model=UnifiedResponse)
async def create_mcp_server(
    server_data: MCPServerCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """创建MCP服务器"""
    server = await mcp_service.create_server(db, server_data, current_user)
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
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """更新MCP服务器"""
    updated_server = await mcp_service.update_server(db, server_id, server_data, current_user)
    if not updated_server:
        raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_server,
        msg="MCP服务器更新成功"
    )


@router.delete("/v1/mcp/servers/{server_id}", response_model=UnifiedResponse)
async def delete_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """删除MCP服务器"""
    success = await mcp_service.delete_server(db, server_id, current_user)
    if not success:
        raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_id": server_id},
        msg="MCP服务器删除成功"
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
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """启用/禁用MCP服务器"""
    update_data = MCPServerUpdate(is_enabled=enable_data.enabled)
    updated_server = await mcp_service.update_server(db, server_id, update_data, current_user)
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
async def test_server_connection(test_request: MCPTestRequest):
    """通用MCP服务器连接测试接口"""
    tools = await _test_mcp_connection(test_request.server_uri)
    return success_response(data=tools, msg="MCP连接测试成功", code=ResponseCode.SUCCESS)


# =============================================================================
# MCP 工具接口 - 实际的业务逻辑接口
# =============================================================================
import platform
import psutil
import os
from datetime import datetime
from src.shared.db.models import now_shanghai
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
            
            "timestamp": now_shanghai().isoformat()
        }
        
        return success_response(
            data=system_info,
            msg="获取系统信息成功"
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}", exc_info=True)
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
                "timestamp": now_shanghai().isoformat()
            },
            msg="命令执行成功"
        )
    except subprocess.TimeoutExpired:
        raise BusinessException("命令执行超时", ResponseCode.BAD_REQUEST)
    except Exception as e:
        logger.error(f"命令执行失败: {str(e)}", exc_info=True)
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
        logger.error(f"获取文件列表失败: {str(e)}", exc_info=True)
        raise BusinessException(f"获取文件列表失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


# =============================================================================
# MCP Gateway 配置端点 - 为 MCP Gateway 提供配置数据
# =============================================================================


@router.get("/v1/mcp/gateway/configs/real", response_model=UnifiedResponse)
async def get_real_gateway_configs(
    since: Optional[str] = Query(None, description="增量更新时间戳 (ISO 8601)"),
    tenant: Optional[str] = Query(None, description="租户过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    为MCP Gateway提供真实配置数据 - 从数据库获取
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
        
        # 获取配置数据
        if tenant:
            configs = await mcp_gateway_service.get_configs_by_tenant(db, tenant)
        else:
            configs = await mcp_gateway_service.get_all_active_configs(db)
        
        # 过滤增量更新
        if since_datetime:
            configs = [c for c in configs if c.update_time > since_datetime]
            logger.info(f"增量更新: 找到 {len(configs)} 个更新的MCP Gateway配置 (since: {since_datetime})")
        else:
            logger.info(f"全量拉取: 返回 {len(configs)} 个MCP Gateway配置")
        
        # 转换为Gateway配置格式
        gateway_configs = []
        for config in configs:
            gateway_configs.append(config.to_gateway_config())
        
        return success_response(
            data={"configs": gateway_configs},
            msg=f"获取MCP Gateway配置成功 (共{len(gateway_configs)}个)"
        )
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取MCP Gateway配置失败: {str(e)}", exc_info=True)
        raise BusinessException("获取配置失败", ResponseCode.INTERNAL_ERROR)

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


@router.get("/v1/mcp/gateway/configs/all", response_model=UnifiedResponse)
async def get_all_gateway_configs(
    tenant: Optional[str] = Query(None, description="租户名称过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取所有MCP Gateway配置数据（用于MCP Gateway服务加载配置）
    """
    try:
        # 构建查询参数
        query_params = MCPGatewayConfigQueryParams(
            tenant=tenant,
            limit=100,  # 获取较多数据
            offset=0
        )
        
        # 从数据库获取配置
        configs, total = await mcp_gateway_service.list_configs(db, query_params)
        
        # 转换为Gateway配置格式
        gateway_configs = []
        for config in configs:
            gateway_config = config.to_gateway_config()
            gateway_configs.append(gateway_config)
        
        return success_response(
            data={"configs": gateway_configs},
            msg=f"获取MCP Gateway配置成功 (共{len(gateway_configs)}个配置)"
        )
        
    except Exception as e:
        logger.error(f"获取MCP Gateway配置失败: {str(e)}", exc_info=True)
        raise BusinessException(f"获取配置失败: {str(e)}", ResponseCode.INTERNAL_SERVER_ERROR)


# =============================================================================
# MCP Gateway 配置管理接口
# =============================================================================

@router.post("/v1/mcp/gateway/configs", response_model=UnifiedResponse)
async def create_gateway_config(
    config_data: MCPGatewayConfigCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """创建MCP Gateway配置"""
    try:
        config = await mcp_gateway_service.create_config(db, config_data, current_user)
        return success_response(
            data=config.to_dict(),
            msg="MCP Gateway配置创建成功",
            code=ResponseCode.CREATED
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"创建MCP Gateway配置失败: {str(e)}", exc_info=True)
        raise BusinessException("创建配置失败", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/mcp/gateway/configs", response_model=UnifiedResponse)
async def list_gateway_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="配置名称过滤"),
    tenant: Optional[str] = Query(None, description="租户过滤"),
    create_by: Optional[str] = Query(None, description="创建者过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取MCP Gateway配置列表"""
    try:
        params = MCPGatewayConfigQueryParams(
            name=name,
            tenant=tenant,
            create_by=create_by,
            limit=size,
            offset=(page - 1) * size
        )
        
        configs, total = await mcp_gateway_service.list_configs(db, params)
        config_list = [config.to_dict() for config in configs]
        
        return paginated_response(
            items=config_list,
            total=total,
            page=page,
            size=size,
            msg="获取MCP Gateway配置列表成功"
        )
    except Exception as e:
        logger.error(f"获取MCP Gateway配置列表失败: {str(e)}", exc_info=True)
        raise BusinessException("获取配置列表失败", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/mcp/gateway/configs/{config_id}", response_model=UnifiedResponse)
async def get_gateway_config(
    config_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定的MCP Gateway配置"""
    try:
        config = await mcp_gateway_service.get_config_by_id(db, config_id)
        if not config:
            raise BusinessException(f"配置 {config_id} 不存在", ResponseCode.NOT_FOUND)
        
        return success_response(
            data=config.to_dict(),
            msg="获取配置成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取MCP Gateway配置失败: {str(e)}", exc_info=True)
        raise BusinessException("获取配置失败", ResponseCode.INTERNAL_ERROR)


@router.put("/v1/mcp/gateway/configs/{config_id}", response_model=UnifiedResponse)
async def update_gateway_config(
    config_id: int,
    config_data: MCPGatewayConfigUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """更新MCP Gateway配置"""
    try:
        updated_config = await mcp_gateway_service.update_config(db, config_id, config_data, current_user)
        if not updated_config:
            raise BusinessException(f"配置 {config_id} 不存在", ResponseCode.NOT_FOUND)
        
        return success_response(
            data=updated_config.to_dict(),
            msg="配置更新成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"更新MCP Gateway配置失败: {str(e)}", exc_info=True)
        raise BusinessException("更新配置失败", ResponseCode.INTERNAL_ERROR)


@router.delete("/v1/mcp/gateway/configs/{config_id}", response_model=UnifiedResponse)
async def delete_gateway_config(
    config_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """删除MCP Gateway配置（软删除）"""
    try:
        success = await mcp_gateway_service.delete_config(db, config_id, current_user)
        if not success:
            raise BusinessException(f"配置 {config_id} 不存在", ResponseCode.NOT_FOUND)
        
        return success_response(
            data={"deleted": True},
            msg="配置删除成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"删除MCP Gateway配置失败: {str(e)}", exc_info=True)
        raise BusinessException("删除配置失败", ResponseCode.INTERNAL_ERROR)


@router.post("/v1/mcp/gateway/reload", response_model=UnifiedResponse)
async def reload_gateway():
    """手动触发MCP Gateway热加载配置"""
    try:
        success = await reload_mcp_gateway()
        if success:
            return success_response(
                data={"reloaded": True},
                msg="MCP Gateway配置重新加载成功"
            )
        else:
            raise BusinessException(
                "MCP Gateway配置重新加载失败，请检查Gateway服务是否正常运行",
                ResponseCode.BAD_REQUEST
            )
    except Exception as e:
        logger.error(f"触发MCP Gateway热加载失败: {str(e)}", exc_info=True)
        raise BusinessException(
            f"触发热加载失败: {str(e)}", 
            ResponseCode.INTERNAL_ERROR
        )


@router.get("/v1/mcp/config", response_model=UnifiedResponse)
async def get_mcp_config():
    """获取MCP相关配置信息"""
    try:
        config_data = {
            "gateway_url": settings.MCP_GATEWAY_URL,
            "endpoints": {
                "sse": "/sse",
                "streamable_http": "/mcp"
            }
        }
        return success_response(
            data=config_data,
            msg="获取MCP配置成功"
        )
    except Exception as e:
        logger.error(f"获取MCP配置失败: {str(e)}", exc_info=True)
        raise BusinessException(
            "获取MCP配置失败", 
            ResponseCode.INTERNAL_ERROR
        )
