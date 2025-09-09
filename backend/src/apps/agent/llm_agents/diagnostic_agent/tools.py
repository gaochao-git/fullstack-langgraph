"""
MCP工具整合模块
从数据库获取工具配置并加载
"""

import asyncio
from typing import List
from src.shared.core.logging import get_logger
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.apps.agent.tools import general_tool
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
        
        # 导入文档工具
        from ..tools.document_tools import get_documents_content
        
        system_tools_map = {
            'get_current_time': general_tool.get_current_time,
            'get_documents_content': get_documents_content,
        }
        
        # 按需加载
        for tool_name in system_tools_config:
            if tool_name in system_tools_map:
                all_tools.append(system_tools_map[tool_name])
                
        # 默认添加文档工具（即使配置中没有）
        if 'get_documents_content' not in system_tools_config:
            all_tools.append(get_documents_content)
        
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
                                server_config[server_id] = {
                                    "url": server.server_uri,
                                    "transport": server.transport_type.replace('-','_'),        # langgraph要求'streamable_http'
                                    "timeout": server.read_timeout_seconds,                     # HTTP超时时间
                                    "sse_read_timeout": server.read_timeout_seconds * 10       # SSE读取超时设置为10倍
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