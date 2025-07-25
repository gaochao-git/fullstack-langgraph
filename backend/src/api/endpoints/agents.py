"""
智能体管理API路由
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
import json
import uuid

from ...db.config import get_async_session
from ...db.models import MCPServer, AgentConfig
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
    is_builtin: str = 'no'
    # 完整配置信息
    tools_info: Optional[Dict[str, Any]] = None
    llm_info: Optional[Dict[str, Any]] = None
    prompt_info: Optional[Dict[str, Any]] = None

class UpdateMCPConfigRequest(BaseModel):
    enabled_servers: List[str]
    selected_tools: List[str]

class CreateAgentRequest(BaseModel):
    agent_id: Optional[str] = None
    agent_name: str
    description: str
    capabilities: List[str]
    tools_info: Optional[Dict[str, Any]] = None
    llm_info: Optional[Dict[str, Any]] = None
    prompt_info: Optional[Dict[str, Any]] = None

class UpdateAgentRequest(BaseModel):
    agent_name: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    tools_info: Optional[Dict[str, Any]] = None
    llm_info: Optional[Dict[str, Any]] = None
    prompt_info: Optional[Dict[str, Any]] = None

# 内置智能体配置 - 这些是系统预定义的智能体
BUILTIN_AGENTS = {
    "diagnostic_agent": {
        "id": "diagnostic_agent",
        "name": "diagnostic_agent",
        "display_name": "故障诊断智能体",
        "description": "专业的系统故障诊断和问题分析智能体，能够快速定位和解决各类技术问题",
        "status": "running",
        "enabled": 'yes',
        "version": "2.1.0",
        "total_runs": 1247,
        "success_rate": 94.5,
        "avg_response_time": 2.3,
        "capabilities": ["数据库诊断", "系统监控", "日志分析", "性能优化"],
        "is_builtin": 'yes'
    },
    "research_agent": {
        "id": "research_agent",
        "name": "research_agent", 
        "display_name": "研究分析智能体",
        "description": "强大的信息研究和数据分析智能体，擅长网络搜索、数据整理和深度分析",
        "status": "running",
        "enabled": 'yes',
        "version": "1.8.2",
        "total_runs": 892,
        "success_rate": 96.2,
        "avg_response_time": 3.1,
        "capabilities": ["网络搜索", "数据分析", "信息整理", "报告生成"],
        "is_builtin": 'yes'
    },
    "security_agent": {
        "id": "security_agent",
        "name": "security_agent",
        "display_name": "安全防护智能体", 
        "description": "专注于网络安全和系统防护的智能体，能够检测威胁和提供安全建议",
        "status": "stopped",
        "enabled": 'no',
        "version": "1.5.1",
        "total_runs": 456,
        "success_rate": 91.8,
        "avg_response_time": 1.9,
        "capabilities": ["威胁检测", "漏洞扫描", "安全评估", "防护建议"],
        "is_builtin": 'yes'
    }
}

# 用户自定义智能体将从数据库加载

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

async def get_or_create_agent_config(agent_id: str, agent_name: str, is_builtin: bool = False) -> Dict[str, Any]:
    """获取或创建智能体MCP配置"""
    try:
        async for session in get_async_session():
            # 查询现有配置
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            )
            config = result.scalar_one_or_none()
            
            if config:
                # 返回现有配置
                tools_config = config.tools_info
                if isinstance(tools_config, str):
                    try:
                        tools_config = json.loads(tools_config)
                    except:
                        tools_config = {}
                elif tools_config is None:
                    tools_config = {}
                
                system_tools = tools_config.get('system_tools', [])
                mcp_tools_config = tools_config.get('mcp_tools', [])
                
                # 从mcp_tools_config中提取启用的服务器和工具列表
                enabled_servers = []
                all_mcp_tools = []
                
                if isinstance(mcp_tools_config, list):
                    for server in mcp_tools_config:
                        if isinstance(server, dict) and server.get('tools'):
                            enabled_servers.append(server.get('server_id', ''))
                            all_mcp_tools.extend(server.get('tools', []))
                
                return {
                    'enabled_servers': enabled_servers,
                    'selected_tools': all_mcp_tools,
                    'system_tools': system_tools
                }
            else:
                # 创建默认配置
                default_system_tools = []
                if agent_id == "diagnostic_agent":
                    default_system_tools = ["get_sop_content", "get_sop_detail", "list_sops", "search_sops", "get_current_time"]
                elif agent_id in ["research_agent", "security_agent"]:
                    default_system_tools = ["get_current_time"]
                
                # 构建默认配置
                tools_config = {
                    'system_tools': default_system_tools,
                    'mcp_tools': []
                }
                
                llm_config = {
                    'model_name': 'gpt-4',
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
                
                prompt_config = {
                    'system_prompt': f'你是一个{agent_name}，请根据用户需求提供专业的帮助。'
                }
                
                await session.execute(
                    insert(AgentConfig).values(
                        agent_id=agent_id,
                        agent_name=agent_name,
                        is_builtin='yes' if is_builtin else 'no',
                        tools_info=json.dumps(tools_config),
                        llm_info=json.dumps(llm_config),
                        prompt_info=json.dumps(prompt_config),
                        create_by='system'
                    )
                )
                await session.commit()
                
                return {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'system_tools': default_system_tools
                }
                
    except Exception as e:
        logger.error(f"获取或创建智能体 {agent_id} 配置失败: {e}")
        return {
            'enabled_servers': [],
            'selected_tools': [],
            'system_tools': []
        }

@router.get("/", response_model=List[Agent])
async def get_agents():
    """获取所有智能体（内置 + 用户自定义）"""
    try:
        agents = []
        
        # 获取用户自定义智能体（从数据库）
        async for session in get_async_session():
            result = await session.execute(select(AgentConfig))
            db_agents = result.scalars().all()
            
            # 添加数据库中的智能体
            for db_agent in db_agents:
                agent_dict = db_agent.to_dict()
                
                # 确保配置字段是字典类型，不是字符串
                tools_info = agent_dict.get('tools_info')
                if isinstance(tools_info, str):
                    try:
                        tools_info = json.loads(tools_info)
                    except:
                        tools_info = {}
                
                llm_info = agent_dict.get('llm_info')
                if isinstance(llm_info, str):
                    try:
                        llm_info = json.loads(llm_info)
                    except:
                        llm_info = {}
                
                prompt_info = agent_dict.get('prompt_info')
                if isinstance(prompt_info, str):
                    try:
                        prompt_info = json.loads(prompt_info)
                    except:
                        prompt_info = {}
                
                # 根据数据库中的 is_builtin 字段判断智能体类型
                agent_id = agent_dict['agent_id']
                is_builtin_from_db = agent_dict.get('is_builtin', 'no')  # 现在直接是字符串
                
                if is_builtin_from_db == 'yes' and agent_id in BUILTIN_AGENTS:
                    # 内置智能体：使用代码中的定义覆盖基本信息，数据库中的动态数据保留
                    builtin_config = BUILTIN_AGENTS[agent_id]
                    agents.append(Agent(
                        id=agent_id,
                        name=builtin_config['name'],
                        display_name=builtin_config['display_name'],
                        description=builtin_config['description'],
                        status=builtin_config['status'],
                        enabled=agent_dict['enabled'],  # 启用状态从数据库读取
                        version=builtin_config['version'],
                        last_used=agent_dict['last_used'],  # 使用统计从数据库读取
                        total_runs=agent_dict['total_runs'],
                        success_rate=agent_dict['success_rate'],
                        avg_response_time=agent_dict['avg_response_time'],
                        capabilities=builtin_config['capabilities'],
                        is_builtin=is_builtin_from_db,  # 使用数据库中的实际值
                        mcp_config=AgentMCPConfig(
                            enabled_servers=agent_dict['mcp_config']['enabled_servers'],
                            selected_tools=agent_dict['mcp_config']['selected_tools'],
                            total_tools=agent_dict['mcp_config']['total_tools']
                        ),
                        # 完整配置信息
                        tools_info=tools_info,
                        llm_info=llm_info,
                        prompt_info=prompt_info
                    ))
                else:
                    # 自定义智能体或数据库中标记为非内置的智能体，完全使用数据库数据
                    agents.append(Agent(
                        id=agent_dict['agent_id'],
                        name=agent_dict['name'],
                        display_name=agent_dict['display_name'],
                        description=agent_dict['description'],
                        status=agent_dict['status'],
                        enabled=agent_dict['enabled'],
                        version=agent_dict['version'],
                        last_used=agent_dict['last_used'],
                        total_runs=agent_dict['total_runs'],
                        success_rate=agent_dict['success_rate'],
                        avg_response_time=agent_dict['avg_response_time'],
                        capabilities=agent_dict['capabilities'],
                        is_builtin=agent_dict.get('is_builtin', 'no'),  # 自定义智能体
                        mcp_config=AgentMCPConfig(
                            enabled_servers=agent_dict['mcp_config']['enabled_servers'],
                            selected_tools=agent_dict['mcp_config']['selected_tools'],
                            total_tools=agent_dict['mcp_config']['total_tools']
                        ),
                        # 完整配置信息
                        tools_info=tools_info,
                        llm_info=llm_info,
                        prompt_info=prompt_info
                    ))
            
            # 如果数据库中没有内置智能体，则创建它们
            existing_agent_ids = {agent.agent_id for agent in db_agents}
            
            for agent_id, agent_config in BUILTIN_AGENTS.items():
                if agent_id not in existing_agent_ids:
                    # 创建内置智能体配置（标记为内置）
                    await get_or_create_agent_config(agent_id, agent_config['display_name'], is_builtin=True)
                    
                    # 构建内置智能体数据
                    mcp_config = AgentMCPConfig(
                        enabled_servers=[],
                        selected_tools=[],
                        total_tools=0
                    )
                    
                    agents.append(Agent(
                        **agent_config,
                        last_used=None,
                        is_builtin='yes',
                        mcp_config=mcp_config,
                        # 内置智能体的默认配置
                        tools_info=None,
                        llm_info=None,
                        prompt_info=None
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
        
        # 分离系统工具和MCP工具
        system_tool_names = ["get_sop_content", "get_sop_detail", "list_sops", "search_sops", "get_current_time"]
        
        system_tools = [tool for tool in config.selected_tools if tool in system_tool_names]
        mcp_tools = [tool for tool in config.selected_tools if tool not in system_tool_names]
        
        # 获取MCP服务器信息，构建mcp_tools配置
        mcp_servers = await get_mcp_servers_info()
        mcp_tools_config = []
        
        # 按服务器分组MCP工具
        for server in mcp_servers:
            if server.status == 'connected':
                server_tools = []
                for tool in server.tools:
                    if tool.name in mcp_tools:
                        server_tools.append(tool.name)
                
                if server_tools:  # 只有选中了工具的服务器才添加
                    mcp_tools_config.append({
                        'server_id': server.id,
                        'server_name': server.name,
                        'tools': server_tools
                    })
        
        # 构建新的工具配置结构
        tools_config = {
            'system_tools': system_tools,
            'mcp_tools': mcp_tools_config
        }
        
        # 保存到数据库
        async for session in get_async_session():
            # 查找现有配置
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            )
            existing_config = result.scalar_one_or_none()
            
            if existing_config:
                # 更新现有配置（只更新工具配置）
                await session.execute(
                    update(AgentConfig)
                    .where(AgentConfig.agent_id == agent_id)
                    .values(
                        tools_info=json.dumps(tools_config),
                        update_by='system'
                    )
                )
            else:
                # 创建新配置
                agent_name = BUILTIN_AGENTS[agent_id]['display_name']
                
                # 默认大模型配置
                default_llm_config = {
                    'model_name': 'gpt-4',
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
                
                # 默认提示词配置
                default_prompt_config = {
                    'system_prompt': f'你是一个{agent_name}，请根据用户需求提供专业的帮助。'
                }
                
                await session.execute(
                    insert(AgentConfig).values(
                        agent_id=agent_id,
                        agent_name=agent_name,
                        tools_info=json.dumps(tools_config),
                        llm_info=json.dumps(default_llm_config),
                        prompt_info=json.dumps(default_prompt_config),
                        create_by='system'
                    )
                )
            
            await session.commit()
            
        logger.info(f"智能体 {agent_id} MCP配置已更新:")
        logger.info(f"  系统工具: {system_tools}")
        logger.info(f"  MCP工具配置: {mcp_tools_config}")
        
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
        async for session in get_async_session():
            # 查全智能体（包括内置和自定义）
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                # 如果是内置智能体但数据库中没有记录，创建记录
                if agent_id in BUILTIN_AGENTS:
                    agent_config = AgentConfig(
                        agent_id=agent_id,
                        agent_name=agent_id,
                        agent_enabled='no',  # 默认禁用，然后切换为启用
                        is_builtin='yes',
                        tools_info={},
                        llm_info={},
                        prompt_info={},
                        create_by='system',
                        update_by='system'
                    )
                    session.add(agent_config)
                    await session.flush()
                    agent = agent_config
                else:
                    raise HTTPException(status_code=404, detail="智能体不存在")
            
            # 切换启用状态 - 处理字符串格式的布尔值
            current_enabled = agent.agent_enabled == 'yes' if isinstance(agent.agent_enabled, str) else agent.agent_enabled
            new_enabled_value = 'no' if current_enabled else 'yes'
            
            agent.agent_enabled = new_enabled_value
            agent.update_by = 'system'
            
            await session.commit()
            logger.info(f"智能体 {agent_id} 状态已更新为: {'启用' if new_enabled_value == 'yes' else '禁用'}")
        
        return {"success": True, "message": "智能体状态已更新"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换智能体 {agent_id} 状态失败: {e}")
        raise HTTPException(status_code=500, detail="切换智能体状态失败")

@router.post("/", response_model=Agent)
async def create_agent(agent_data: CreateAgentRequest):
    """创建新的智能体"""
    try:
        # 自动生成 agent_id（如果没传）
        agent_id = agent_data.agent_id or str(uuid.uuid4())
        # 检查agent_id是否已存在
        async for session in get_async_session():
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            )
            existing_agent = result.scalar_one_or_none()
            
            if existing_agent:
                raise HTTPException(status_code=400, detail="智能体ID已存在")
            
            # 构建默认配置
            default_tools_config = {
                'system_tools': ['get_current_time'],  # 默认给新智能体分配基础工具
                'mcp_tools': []
            }
            
            default_llm_config = {
                'model_name': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 2000
            }
            
            default_prompt_config = {
                'system_prompt': f'你是{agent_data.agent_name}，请根据用户需求提供专业的帮助。'
            }
            
            # 创建新智能体
            new_agent = AgentConfig(
                agent_id=agent_id,
                agent_name=agent_data.agent_name,
                agent_description=agent_data.description,
                agent_capabilities=agent_data.capabilities,
                agent_version='1.0.0',
                agent_status='stopped',
                agent_enabled='yes',
                is_builtin='no',
                tools_info=agent_data.tools_info or default_tools_config,
                llm_info=agent_data.llm_info or default_llm_config,
                prompt_info=agent_data.prompt_info or default_prompt_config,
                create_by='user'
            )
            
            session.add(new_agent)
            await session.commit()
            await session.refresh(new_agent)
            
            # 返回创建的智能体
            agent_dict = new_agent.to_dict()
            
            # 确保配置字段是字典类型，不是字符串
            tools_info = agent_dict.get('tools_info')
            if isinstance(tools_info, str):
                try:
                    tools_info = json.loads(tools_info)
                except:
                    tools_info = {}
            
            llm_info = agent_dict.get('llm_info')
            if isinstance(llm_info, str):
                try:
                    llm_info = json.loads(llm_info)
                except:
                    llm_info = {}
            
            prompt_info = agent_dict.get('prompt_info')
            if isinstance(prompt_info, str):
                try:
                    prompt_info = json.loads(prompt_info)
                except:
                    prompt_info = {}
            
            return Agent(
                id=agent_dict['agent_id'],
                name=agent_dict['name'],
                display_name=agent_dict['display_name'],
                description=agent_dict['description'],
                status=agent_dict['status'],
                enabled=agent_dict['enabled'],
                version=agent_dict['version'],
                last_used=agent_dict['last_used'],
                total_runs=agent_dict['total_runs'],
                success_rate=agent_dict['success_rate'],
                avg_response_time=agent_dict['avg_response_time'],
                capabilities=agent_dict['capabilities'],
                is_builtin=agent_dict.get('is_builtin', False),
                mcp_config=AgentMCPConfig(
                    enabled_servers=agent_dict['mcp_config']['enabled_servers'],
                    selected_tools=agent_dict['mcp_config']['selected_tools'],
                    total_tools=agent_dict['mcp_config']['total_tools']
                ),
                # 完整配置信息
                tools_info=tools_info,
                llm_info=llm_info,
                prompt_info=prompt_info
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建智能体失败: {e}")
        raise HTTPException(status_code=500, detail="创建智能体失败")

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, agent_data: UpdateAgentRequest):
    """更新智能体信息"""
    try:
        async for session in get_async_session():
            # 查找智能体
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在")
            
            # 更新字段
            if agent_data.agent_name is not None:
                agent.agent_name = agent_data.agent_name
            if agent_data.description is not None:
                agent.agent_description = agent_data.description
            if agent_data.capabilities is not None:
                agent.agent_capabilities = agent_data.capabilities
            if agent_data.tools_info is not None:
                agent.tools_info = agent_data.tools_info
            if agent_data.llm_info is not None:
                agent.llm_info = agent_data.llm_info
            if agent_data.prompt_info is not None:
                agent.prompt_info = agent_data.prompt_info
            
            agent.update_by = 'user'
            
            await session.commit()
            await session.refresh(agent)
            
            # 返回更新后的智能体
            agent_dict = agent.to_dict()
            
            # 确保配置字段是字典类型，不是字符串
            tools_info = agent_dict.get('tools_info')
            if isinstance(tools_info, str):
                try:
                    tools_info = json.loads(tools_info)
                except:
                    tools_info = {}
            
            llm_info = agent_dict.get('llm_info')
            if isinstance(llm_info, str):
                try:
                    llm_info = json.loads(llm_info)
                except:
                    llm_info = {}
            
            prompt_info = agent_dict.get('prompt_info')
            if isinstance(prompt_info, str):
                try:
                    prompt_info = json.loads(prompt_info)
                except:
                    prompt_info = {}
            
            return Agent(
                id=agent_dict['agent_id'],
                name=agent_dict['name'],
                display_name=agent_dict['display_name'],
                description=agent_dict['description'],
                status=agent_dict['status'],
                enabled=agent_dict['enabled'],
                version=agent_dict['version'],
                last_used=agent_dict['last_used'],
                total_runs=agent_dict['total_runs'],
                success_rate=agent_dict['success_rate'],
                avg_response_time=agent_dict['avg_response_time'],
                capabilities=agent_dict['capabilities'],
                is_builtin=agent_dict.get('is_builtin', False),
                mcp_config=AgentMCPConfig(
                    enabled_servers=agent_dict['mcp_config']['enabled_servers'],
                    selected_tools=agent_dict['mcp_config']['selected_tools'],
                    total_tools=agent_dict['mcp_config']['total_tools']
                ),
                # 完整配置信息
                tools_info=tools_info,
                llm_info=llm_info,
                prompt_info=prompt_info
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新智能体 {agent_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="更新智能体失败")

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """删除智能体"""
    try:
        async for session in get_async_session():
            # 查找智能体
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在")
            
            # 不允许删除内置智能体
            if agent.is_builtin == 'yes':
                raise HTTPException(status_code=400, detail="不能删除内置智能体")
            
            await session.delete(agent)
            await session.commit()
            
            return {"success": True, "message": "智能体已删除"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除智能体 {agent_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="删除智能体失败")


@router.get("/{agent_id}/available-models")
async def get_agent_available_models(agent_id: str):
    """获取指定智能体的可用模型列表"""
    try:
        from ...services.agent_config_service import AgentConfigService
        
        # 获取智能体的可用模型
        models = AgentConfigService.get_agent_available_models(agent_id)
        
        return {
            "code": 200,
            "data": {
                "agent_id": agent_id,
                "models": models
            },
            "message": "获取智能体可用模型成功"
        }
        
    except Exception as e:
        logger.error(f"获取智能体 {agent_id} 可用模型失败: {e}")
        raise HTTPException(status_code=500, detail="获取智能体可用模型失败")

# 对话相关请求模型
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(agent_id: str, chat_request: ChatRequest):
    """与智能体进行对话"""
    try:
        # 查找智能体
        async for session in get_async_session():
            result = await session.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            # 如果数据库中没有找到，检查是否是内置智能体
            if not agent and agent_id in BUILTIN_AGENTS:
                await get_or_create_agent_config(agent_id, BUILTIN_AGENTS[agent_id]['display_name'], is_builtin=True)
                result = await session.execute(
                    select(AgentConfig).where(AgentConfig.agent_id == agent_id)
                )
                agent = result.scalar_one_or_none()
            
            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在")
            
            # 检查智能体是否启用
            agent_enabled = agent.agent_enabled == 'yes' if isinstance(agent.agent_enabled, str) else agent.agent_enabled
            if not agent_enabled:
                raise HTTPException(status_code=400, detail="智能体未启用")
            
            # 获取智能体配置
            tools_info = agent.tools_info if isinstance(agent.tools_info, dict) else json.loads(agent.tools_info or '{}')
            llm_info = agent.llm_info if isinstance(agent.llm_info, dict) else json.loads(agent.llm_info or '{}')
            prompt_info = agent.prompt_info if isinstance(agent.prompt_info, dict) else json.loads(agent.prompt_info or '{}')
            
            # 生成会话ID（如果没有提供）
            conversation_id = chat_request.conversation_id or f"chat_{agent_id}_{uuid.uuid4().hex[:8]}"
            
            # 获取系统提示词
            system_prompt = prompt_info.get('system_prompt', f'你是{agent.agent_name}，请根据用户需求提供专业的帮助。')
            
            # 构建响应（这里是简化版本，实际实现需要根据智能体类型调用相应的处理逻辑）
            response_text = f"[{agent.agent_name}] 收到您的消息：{chat_request.message}\n\n基于我的配置和能力，我将为您提供帮助。"
            
            # 如果是内置智能体，可以添加特殊处理逻辑
            if agent_id == "diagnostic_agent":
                response_text += "\n\n作为故障诊断智能体，我可以帮助您分析系统问题、查看日志、诊断性能等。"
            elif agent_id == "research_agent":
                response_text += "\n\n作为研究分析智能体，我可以帮助您进行信息搜索、数据分析、内容整理等。"
            elif agent_id == "security_agent":
                response_text += "\n\n作为安全防护智能体，我可以帮助您进行安全评估、威胁检测、漏洞分析等。"
            else:
                # 自定义智能体
                capabilities = agent.agent_capabilities or []
                if capabilities:
                    response_text += f"\n\n我的核心能力包括：{', '.join(capabilities[:3])}等。"
            
            # 更新智能体使用统计（简化版本）
            agent.agent_total_runs = (agent.agent_total_runs or 0) + 1
            agent.agent_last_used = "刚刚"
            await session.commit()
            
            return ChatResponse(
                response=response_text,
                conversation_id=conversation_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"与智能体 {agent_id} 对话失败: {e}")
        raise HTTPException(status_code=500, detail="对话处理失败")