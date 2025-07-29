"""
Agent服务层 - 纯异步实现
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import json
import uuid
from datetime import datetime

from src.apps.agent.dao import AgentDAO
from src.apps.agent.models import AgentConfig
from src.shared.db.transaction import transactional
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode

logger = get_logger(__name__)

# 内置智能体配置
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


class AgentService:
    """Agent服务层 - 纯异步实现"""
    
    def __init__(self):
        self._dao = AgentDAO()
    
    # ==================== 核心业务方法 ====================
    
    @transactional()
    async def create_agent(
        self, 
        session: AsyncSession,
        agent_data: Dict[str, Any]
    ) -> AgentConfig:
        """创建智能体配置"""
        # 生成agent_id（如果未提供）
        if not agent_data.get('agent_id'):
            agent_data['agent_id'] = f"custom_{uuid.uuid4().hex[:8]}"
        
        # 检查是否已存在
        existing = await self._dao.get_by_agent_id(session, agent_data['agent_id'])
        if existing:
            raise BusinessException(
                f"智能体ID {agent_data['agent_id']} 已存在", 
                ResponseCode.DUPLICATE_RESOURCE
            )
        
        # 检查是否为保留的内置智能体ID
        if agent_data['agent_id'] in BUILTIN_AGENTS and agent_data.get('is_builtin') != 'yes':
            raise BusinessException(
                f"智能体ID {agent_data['agent_id']} 为系统保留ID", 
                ResponseCode.INVALID_PARAMETER
            )
        
        # 设置默认值
        agent_data.setdefault('agent_status', 'stopped')
        agent_data.setdefault('agent_enabled', 'yes')
        agent_data.setdefault('is_builtin', 'no')
        agent_data.setdefault('create_by', 'system')
        agent_data.setdefault('total_runs', 0)
        agent_data.setdefault('success_rate', 0.0)
        agent_data.setdefault('avg_response_time', 0.0)
        agent_data.setdefault('create_time', datetime.utcnow())
        agent_data.setdefault('update_time', datetime.utcnow())
        
        # 处理capabilities字段映射
        if 'capabilities' in agent_data and isinstance(agent_data['capabilities'], list):
            agent_data['agent_capabilities'] = agent_data.pop('capabilities')
        
        logger.info(f"Creating agent: {agent_data['agent_id']}")
        return await self._dao.create(session, agent_data)
    
    async def get_agent_by_id(
        self, 
        session: AsyncSession, 
        agent_id: str,
        include_builtin: bool = True
    ) -> Optional[Dict[str, Any]]:
        """根据ID获取智能体配置"""
        # 先检查是否是内置智能体
        if include_builtin and agent_id in BUILTIN_AGENTS:
            # 尝试从数据库获取配置
            db_agent = await self._dao.get_by_agent_id(session, agent_id)
            if db_agent:
                agent_dict = db_agent.to_dict()
                agent_dict['is_builtin'] = 'yes'
                # 确保有mcp_config字段
                if 'mcp_config' not in agent_dict:
                    agent_dict['mcp_config'] = {
                        'enabled_servers': [],
                        'selected_tools': [],
                        'total_tools': 0
                    }
                return agent_dict
            else:
                # 返回默认内置配置
                builtin_config = BUILTIN_AGENTS[agent_id].copy()
                builtin_config['mcp_config'] = {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'total_tools': 0
                }
                return builtin_config
        
        # 从数据库获取用户自定义智能体
        db_agent = await self._dao.get_by_agent_id(session, agent_id)
        if db_agent:
            agent_dict = db_agent.to_dict()
            # 确保有mcp_config字段
            if 'mcp_config' not in agent_dict:
                agent_dict['mcp_config'] = {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'total_tools': 0
                }
            return agent_dict
        
        return None
    
    async def list_agents(
        self, 
        session: AsyncSession,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
        enabled_only: bool = False,
        include_builtin: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取智能体列表"""
        offset = (page - 1) * size
        
        # 构建过滤条件
        filters = {}
        if enabled_only:
            filters['agent_enabled'] = 'yes'
            filters['is_active'] = True
        if status:
            filters['agent_status'] = status
        
        # 获取数据库中的智能体
        if search:
            db_agents = await self._dao.search_by_name(
                session, search, enabled_only, size, offset
            )
            total_db = len(db_agents)  # 简化计数，实际应该有专门的计数方法
        else:
            db_agents = await self._dao.get_list(
                session, 
                filters=filters if filters else None,
                limit=size, 
                offset=offset,
                order_by='create_time'
            )
            total_db = await self._dao.count(session, filters=filters if filters else None)
        
        # 转换为字典格式
        db_agents_dict = {}
        for agent in db_agents:
            agent_dict = agent.to_dict()
            # 确保有mcp_config字段
            if 'mcp_config' not in agent_dict:
                agent_dict['mcp_config'] = {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'total_tools': 0
                }
            db_agents_dict[agent.agent_id] = agent_dict
        
        all_agents = []
        total = total_db
        
        # 如果包含内置智能体
        if include_builtin:
            # 先添加内置智能体
            for builtin_id, builtin_config in BUILTIN_AGENTS.items():
                # 应用过滤条件
                if enabled_only and builtin_config.get('enabled') != 'yes':
                    continue
                if status and builtin_config.get('status') != status:
                    continue
                if search and search.lower() not in builtin_config.get('display_name', '').lower():
                    continue
                
                if builtin_id in db_agents_dict:
                    # 如果数据库中有，使用数据库配置，但保留内置标识
                    agent_config = db_agents_dict[builtin_id].copy()
                    agent_config['is_builtin'] = 'yes'
                    all_agents.append(agent_config)
                else:
                    # 使用默认内置配置
                    builtin_config_copy = builtin_config.copy()
                    builtin_config_copy['mcp_config'] = {
                        'enabled_servers': [],
                        'selected_tools': [],
                        'total_tools': 0
                    }
                    all_agents.append(builtin_config_copy)
            
            total += len(BUILTIN_AGENTS)
        
        # 添加用户自定义智能体
        for agent_id, agent_config in db_agents_dict.items():
            if not include_builtin or agent_id not in BUILTIN_AGENTS:
                all_agents.append(agent_config)
        
        return all_agents, total
    
    @transactional()
    async def update_agent(
        self, 
        session: AsyncSession,
        agent_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[AgentConfig]:
        """更新智能体配置"""
        # 检查是否存在
        existing = await self._dao.get_by_agent_id(session, agent_id)
        if not existing:
            # 如果是内置智能体且不存在，则创建
            if agent_id in BUILTIN_AGENTS:
                builtin_config = BUILTIN_AGENTS[agent_id].copy()
                builtin_config.update(update_data)
                builtin_config['agent_id'] = agent_id
                builtin_config['is_builtin'] = 'yes'
                
                # 处理字段名映射
                if 'capabilities' in builtin_config:
                    builtin_config['agent_capabilities'] = builtin_config.pop('capabilities')
                if 'name' in builtin_config:
                    builtin_config['agent_name'] = builtin_config.pop('name')
                if 'display_name' in builtin_config:
                    builtin_config['agent_name'] = builtin_config.pop('display_name')
                
                return await self._dao.create(session, builtin_config)
            else:
                raise BusinessException(
                    f"智能体 {agent_id} 不存在", 
                    ResponseCode.NOT_FOUND
                )
        
        # 移除不可更新的字段
        update_data.pop('agent_id', None)
        update_data.pop('create_time', None)
        update_data.pop('create_by', None)
        
        # 设置更新时间
        update_data['update_time'] = datetime.utcnow()
        
        # 处理capabilities字段映射
        if 'capabilities' in update_data and isinstance(update_data['capabilities'], list):
            update_data['agent_capabilities'] = update_data.pop('capabilities')
        
        logger.info(f"Updating agent: {agent_id}")
        return await self._dao.update_by_field(session, 'agent_id', agent_id, update_data)
    
    @transactional()
    async def delete_agent(
        self, 
        session: AsyncSession,
        agent_id: str
    ) -> bool:
        """删除智能体配置"""
        # 检查是否存在
        existing = await self._dao.get_by_agent_id(session, agent_id)
        if not existing:
            raise BusinessException(
                f"智能体 {agent_id} 不存在", 
                ResponseCode.NOT_FOUND
            )
        
        # 检查是否为内置智能体
        if existing.is_builtin == 'yes':
            raise BusinessException(
                f"不能删除内置智能体: {agent_id}", 
                ResponseCode.FORBIDDEN
            )
        
        logger.info(f"Deleting agent: {agent_id}")
        result = await self._dao.delete_by_field(session, 'agent_id', agent_id)
        return result > 0
    
    @transactional()
    async def update_mcp_config(
        self,
        session: AsyncSession,
        agent_id: str,
        enabled_servers: List[str],
        selected_tools: List[str]
    ) -> Optional[AgentConfig]:
        """更新智能体MCP配置"""
        # 构建MCP工具配置
        mcp_tools_config = []
        for server_id in enabled_servers:
            # 获取该服务器的工具
            server_tools = [tool for tool in selected_tools if tool.startswith(f"{server_id}:")]
            if server_tools:
                mcp_tools_config.append({
                    'server_id': server_id,
                    'tools': [tool.split(':', 1)[1] for tool in server_tools]  # 移除server_id前缀
                })
        
        # 构建完整工具配置
        tools_info = {
            'system_tools': [],  # 系统工具列表
            'mcp_tools': mcp_tools_config
        }
        
        update_data = {
            'tools_info': tools_info
        }
        
        return await self.update_agent(session, agent_id, update_data)
    
    @transactional()
    async def update_agent_status(
        self,
        session: AsyncSession,
        agent_id: str,
        status: str
    ) -> Optional[AgentConfig]:
        """更新智能体状态"""
        return await self._dao.update_agent_status(session, agent_id, status)
    
    @transactional()
    async def update_statistics(
        self,
        session: AsyncSession,
        agent_id: str,
        total_runs: int,
        success_rate: float,
        avg_response_time: float
    ) -> Optional[AgentConfig]:
        """更新运行统计信息"""
        return await self._dao.update_statistics(
            session, agent_id, total_runs, success_rate, avg_response_time
        )
    
    async def get_statistics(
        self, 
        session: AsyncSession
    ):
        """获取智能体统计信息 - 返回原始查询结果让响应层处理"""
        result = await self._dao.get_agent_statistics(session)
        
        # 从原始结果中获取第一行数据
        stats_row = result.first()
        if stats_row:
            stats_dict = dict(stats_row)
            # 添加业务逻辑计算
            stats_dict['custom'] = stats_dict['total'] - stats_dict['builtin']
            # 包含内置智能体的统计
            stats_dict['total'] += len(BUILTIN_AGENTS)
            stats_dict['builtin'] += len(BUILTIN_AGENTS)
            return stats_dict
        
        # 如果没有数据，返回默认统计
        return {
            'total': len(BUILTIN_AGENTS),
            'enabled': 0,
            'running': 0,
            'builtin': len(BUILTIN_AGENTS),
            'custom': 0
        }
    
    async def search_agents(
        self,
        session: AsyncSession,
        keyword: str,
        page: int = 1,
        size: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """搜索智能体"""
        offset = (page - 1) * size
        
        # 搜索数据库中的智能体
        db_agents = await self._dao.search_by_name(session, keyword, True, size, offset)
        
        # 搜索内置智能体
        builtin_matches = []
        for builtin_id, builtin_config in BUILTIN_AGENTS.items():
            if (keyword.lower() in builtin_config.get('display_name', '').lower() or
                keyword.lower() in builtin_config.get('description', '').lower()):
                builtin_config_copy = builtin_config.copy()
                builtin_config_copy['mcp_config'] = {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'total_tools': 0
                }
                builtin_matches.append(builtin_config_copy)
        
        # 合并结果
        all_matches = []
        
        # 转换数据库结果
        for agent in db_agents:
            agent_dict = agent.to_dict()
            if 'mcp_config' not in agent_dict:
                agent_dict['mcp_config'] = {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'total_tools': 0
                }
            all_matches.append(agent_dict)
        
        # 添加内置智能体匹配
        all_matches.extend(builtin_matches)
        
        return all_matches, len(all_matches)


# 创建全局实例
agent_service = AgentService()