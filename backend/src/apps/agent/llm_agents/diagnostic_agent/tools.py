"""
MCP工具整合模块
从数据库获取工具配置并加载
"""

import asyncio
from typing import List
from datetime import timedelta
from src.shared.core.logging import get_logger
from langchain_mcp_adapters.client import MultiServerMCPClient
from ..agent_utils import get_tools_config_from_db
from src.apps.mcp.service.mcp_service import mcp_service
from src.shared.db.config import get_sync_db

logger = get_logger(__name__)

async def get_diagnostic_tools(agent_id: str):
    """获取诊断工具列表"""
    try:
        # 从数据库获取工具配置
        tools_config = get_tools_config_from_db(agent_id)
        
        all_tools = []
        
        # 1. 处理系统工具
        system_tools_config = tools_config.get('system_tools', [])
        
        # 获取所有系统工具映射
        from ..agent_utils import get_system_tools_map
        system_tools_map = get_system_tools_map()
        
        # 按需加载 - 只加载用户选择的工具
        for tool_name in system_tools_config:
            if tool_name in system_tools_map:
                all_tools.append(system_tools_map[tool_name])
                logger.debug(f"加载系统工具: {tool_name}")
        
        # 2. 处理MCP工具
        mcp_tools_config = tools_config.get('mcp_tools', [])
        allowed_mcp_tools = []
        
        # 从mcp_tools配置中提取所有允许的工具名称
        for mcp_server in mcp_tools_config:
            server_tools = mcp_server.get('tools', [])
            allowed_mcp_tools.extend(server_tools)
        
        if allowed_mcp_tools:
            # 根据server_id从mcp_servers表构建服务器配置
            server_config = {}
            db_gen = get_sync_db()
            db = next(db_gen)
            try:
                # 获取所有启用的MCP服务器
                for mcp_server_config in mcp_tools_config:
                    server_id = mcp_server_config.get('server_id')
                    if server_id:
                        try:
                            # 查询mcp_servers表获取server_uri（使用同步方法）
                            server = mcp_service.get_server_by_id_sync(db, server_id)
                            if server and server.is_enabled == 'on':
                                # 根据传输类型使用正确的超时参数类型
                                if server.transport_type == 'streamable-http':
                                    # Streamable HTTP 需要 timedelta 对象
                                    server_config[server_id] = {
                                        "url": server.server_uri,
                                        "transport": "streamable_http",
                                        "timeout": timedelta(seconds=server.read_timeout_seconds),
                                        "sse_read_timeout": timedelta(seconds=server.read_timeout_seconds * 10)
                                    }
                                else:
                                    # SSE 和其他传输类型使用 float
                                    server_config[server_id] = {
                                        "url": server.server_uri,
                                        "transport": server.transport_type.replace('-','_'),
                                        "timeout": float(server.read_timeout_seconds),
                                        "sse_read_timeout": float(server.read_timeout_seconds * 10)
                                    }
                        except Exception as e:
                            logger.error(f"获取MCP服务器配置失败 server_id={server_id}: {e}")
                            # 继续处理其他服务器，不中断整个流程
                            continue
            finally:
                db.close()
            
            if server_config:
                client = MultiServerMCPClient(server_config)
                all_mcp_tools = await client.get_tools()
                
                # 取交集：只加载数据库配置允许且MCP能发现的工具
                filtered_mcp_tools = [tool for tool in all_mcp_tools if tool.name in allowed_mcp_tools]
                all_tools.extend(filtered_mcp_tools)
                
                logger.info(f"MCP工具过滤: 数据库允许{len(allowed_mcp_tools)}个，MCP发现{len(all_mcp_tools)}个，加载{len(filtered_mcp_tools)}个")
            else:
                logger.warning("没有可用的MCP服务器，跳过MCP工具加载")
        
        logger.info(f"工具加载完成: 系统工具{len(system_tools_config)}个，MCP工具{len(allowed_mcp_tools)}个，总计{len(all_tools)}个可用工具")
        
        return all_tools
        
    except Exception as e:
        logger.error(f"❌ 获取工具失败: {e}", exc_info=True)
        return []