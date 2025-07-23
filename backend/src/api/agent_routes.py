"""
智能体管理API路由
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.config import get_async_session
from src.database.models import MCPServer
from src.agents.diagnostic_agent.tools_mcp import mcp_integrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])

# 数据模型
class MCPTool(BaseModel):
    name: str
    description: str
    enabled: bool
    category: str
    server_id: str
    server_name: str

class MCPServerInfo(BaseModel):
    id: str
    name: str
    status: str
    tools: List[MCPTool]

class AgentMCPConfig(BaseModel):
    enabled_servers: List[str]
    selected_tools: List[str]
    total_tools: int

class Agent(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    status: str
    enabled: bool
    version: str
    last_used: Optional[str]
    total_runs: int
    success_rate: float
    avg_response_time: float
    capabilities: List[str]
    mcp_config: AgentMCPConfig

class UpdateMCPConfigRequest(BaseModel):
    enabled_servers: List[str]
    selected_tools: List[str]

# 内置智能体配置
BUILTIN_AGENTS = {
    "diagnostic_agent": {
        "id": "diagnostic_agent",
        "name": "diagnostic_agent",
        "display_name": "故障诊断智能体",
        "description": "专业的系统故障诊断和问题分析智能体，能够快速定位和解决各类技术问题",
        "status": "running",
        "enabled": True,
        "version": "2.1.0",
        "total_runs": 1247,
        "success_rate": 94.5,
        "avg_response_time": 2.3,
        "capabilities": ["数据库诊断", "系统监控", "日志分析", "性能优化"]
    },
    "research_agent": {
        "id": "research_agent",
        "name": "research_agent", 
        "display_name": "研究分析智能体",
        "description": "强大的信息研究和数据分析智能体，擅长网络搜索、数据整理和深度分析",
        "status": "running",
        "enabled": True,
        "version": "1.8.2",
        "total_runs": 892,
        "success_rate": 96.2,
        "avg_response_time": 3.1,
        "capabilities": ["网络搜索", "数据分析", "信息整理", "报告生成"]
    },
    "security_agent": {
        "id": "security_agent",
        "name": "security_agent",
        "display_name": "安全防护智能体", 
        "description": "专注于网络安全和系统防护的智能体，能够检测威胁和提供安全建议",
        "status": "stopped",
        "enabled": False,
        "version": "1.5.1",
        "total_runs": 456,
        "success_rate": 91.8,
        "avg_response_time": 1.9,
        "capabilities": ["威胁检测", "漏洞扫描", "安全评估", "防护建议"]
    }
}

async def get_mcp_servers_info() -> List[MCPServerInfo]:
    """获取MCP服务器信息"""
    try:
        # 获取数据库中的MCP服务器配置
        async for session in get_async_session():
            result = await session.execute(
                select(MCPServer).where(MCPServer.is_enabled == 'on')
            )
            db_servers = result.scalars().all()
            
            # 获取实际的MCP工具信息
            try:
                actual_tools = await mcp_integrator.get_mcp_tools()
                tool_map = {tool.name: tool for tool in actual_tools}
            except Exception as e:
                logger.warning(f"获取MCP工具失败: {e}")
                tool_map = {}
            
            servers_info = []
            for server in db_servers:
                tools = []
                
                # 解析服务器工具配置
                if server.server_tools:
                    import json
                    try:
                        tools_config = json.loads(server.server_tools) if isinstance(server.server_tools, str) else server.server_tools
                        for tool_config in tools_config:
                            tool_name = tool_config.get('name', '')
                            actual_tool = tool_map.get(tool_name)
                            
                            tools.append(MCPTool(
                                name=tool_name,
                                description=tool_config.get('description', actual_tool.description if actual_tool else ''),
                                enabled=tool_config.get('enabled', True),
                                category=tool_config.get('category', 'general'),
                                server_id=server.server_id,
                                server_name=server.server_name
                            ))
                    except Exception as e:
                        logger.warning(f"解析服务器 {server.server_name} 工具配置失败: {e}")
                
                servers_info.append(MCPServerInfo(
                    id=server.server_id,
                    name=server.server_name,
                    status="connected" if server.connection_status == "connected" else "disconnected",
                    tools=tools
                ))
            
            return servers_info
            
    except Exception as e:
        logger.error(f"获取MCP服务器信息失败: {e}")
        return []

@router.get("/", response_model=List[Agent])
async def get_agents():
    """获取所有智能体"""
    try:
        # 获取MCP服务器信息
        mcp_servers = await get_mcp_servers_info()
        
        agents = []
        for agent_id, agent_config in BUILTIN_AGENTS.items():
            # 计算MCP配置信息
            total_tools = sum(len(server.tools) for server in mcp_servers)
            
            # 对于故障诊断智能体，使用实际的MCP配置
            if agent_id == "diagnostic_agent":
                try:
                    system_tools = mcp_integrator.get_system_tools()
                    mcp_tools = await mcp_integrator.get_mcp_tools()
                    
                    enabled_servers = [server.id for server in mcp_servers if server.tools]
                    selected_tools = [tool.name for tool in mcp_tools]
                    
                    mcp_config = AgentMCPConfig(
                        enabled_servers=enabled_servers,
                        selected_tools=selected_tools,
                        total_tools=len(system_tools) + len(mcp_tools)
                    )
                except Exception as e:
                    logger.warning(f"获取智能体 {agent_id} MCP配置失败: {e}")
                    mcp_config = AgentMCPConfig(
                        enabled_servers=[],
                        selected_tools=[],
                        total_tools=0
                    )
            else:
                # 其他智能体使用默认配置
                mcp_config = AgentMCPConfig(
                    enabled_servers=[],
                    selected_tools=[],
                    total_tools=total_tools
                )
            
            agents.append(Agent(
                **agent_config,
                last_used=None,  # 可以从数据库或日志中获取
                mcp_config=mcp_config
            ))
        
        return agents
        
    except Exception as e:
        logger.error(f"获取智能体列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取智能体列表失败")

@router.get("/mcp-servers", response_model=List[MCPServerInfo])
async def get_mcp_servers():
    """获取MCP服务器信息"""
    try:
        return await get_mcp_servers_info()
    except Exception as e:
        logger.error(f"获取MCP服务器信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取MCP服务器信息失败")

@router.put("/{agent_id}/mcp-config")
async def update_agent_mcp_config(
    agent_id: str,
    config: UpdateMCPConfigRequest
):
    """更新智能体MCP配置"""
    try:
        if agent_id not in BUILTIN_AGENTS:
            raise HTTPException(status_code=404, detail="智能体不存在")
        
        # 对于故障诊断智能体，实际更新MCP配置
        if agent_id == "diagnostic_agent":
            # 这里可以实现将配置保存到数据库的逻辑
            # 目前先记录日志
            logger.info(f"更新智能体 {agent_id} MCP配置:")
            logger.info(f"  启用服务器: {config.enabled_servers}")
            logger.info(f"  选中工具: {config.selected_tools}")
            
            # TODO: 将配置保存到数据库或配置文件
            # 可以考虑创建一个agent_mcp_config表来存储每个智能体的MCP配置
        
        return {"success": True, "message": "MCP配置已更新"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新智能体 {agent_id} MCP配置失败: {e}")
        raise HTTPException(status_code=500, detail="更新MCP配置失败")

@router.put("/{agent_id}/toggle")
async def toggle_agent_status(agent_id: str):
    """切换智能体启用状态"""
    try:
        if agent_id not in BUILTIN_AGENTS:
            raise HTTPException(status_code=404, detail="智能体不存在")
        
        # 这里可以实现实际的启用/禁用逻辑
        logger.info(f"切换智能体 {agent_id} 状态")
        
        return {"success": True, "message": "智能体状态已更新"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换智能体 {agent_id} 状态失败: {e}")
        raise HTTPException(status_code=500, detail="切换智能体状态失败")