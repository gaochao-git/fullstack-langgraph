"""
Agent统一服务层
同时支持静态方法（兼容现有API）和实例方法（新架构）
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, insert
import json
import uuid

from ....shared.db.dao import AgentDAO
from ....shared.db.models import AgentConfig
from ....shared.db.transaction import transactional, sync_transactional
from ....shared.core.logging import get_logger

logger = get_logger(__name__)

# 内置智能体配置 - 与现有API保持一致
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
    """Agent模板服务 - 支持新旧两种调用方式"""
    
    _instance = None
    _dao = None
    
    def __init__(self):
        if not self._dao:
            self._dao = AgentDAO()
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    # ==================== 静态方法（兼容现有API） ====================
    
    @staticmethod
    async def get_all_agents(session: AsyncSession) -> List[Dict[str, Any]]:
        """获取所有智能体（静态方法，兼容现有API）"""
        service = AgentService.get_instance()
        
        # 获取数据库中的智能体
        db_agents = await service._dao.get_list(session)
        db_agents_dict = {}
        for agent in db_agents:
            agent_dict = agent.to_dict()
            db_agents_dict[agent.agent_id] = agent_dict
        
        # 合并内置智能体和数据库智能体
        all_agents = []
        
        # 先添加内置智能体
        for builtin_id, builtin_config in BUILTIN_AGENTS.items():
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
        
        # 添加用户自定义智能体
        for agent_id, agent_config in db_agents_dict.items():
            if agent_id not in BUILTIN_AGENTS:
                all_agents.append(agent_config)
        
        return all_agents
    
    @staticmethod
    async def get_agent_by_id(session: AsyncSession, agent_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取智能体（静态方法）"""
        service = AgentService.get_instance()
        
        # 先检查是否是内置智能体
        if agent_id in BUILTIN_AGENTS:
            # 尝试从数据库获取配置
            db_agent = await service._dao.get_by_agent_id(session, agent_id)
            if db_agent:
                agent_dict = db_agent.to_dict()
                agent_dict['is_builtin'] = 'yes'
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
        db_agent = await service._dao.get_by_agent_id(session, agent_id)
        return db_agent.to_dict() if db_agent else None
    
    @staticmethod
    async def create_agent(session: AsyncSession, agent_data: Dict[str, Any]) -> AgentConfig:
        """创建智能体（静态方法）"""
        service = AgentService.get_instance()
        
        # 生成agent_id（如果未提供）
        if not agent_data.get('agent_id'):
            agent_data['agent_id'] = f"custom_{uuid.uuid4().hex[:8]}"
        
        # 设置默认值
        agent_data.setdefault('agent_status', 'stopped')
        agent_data.setdefault('agent_enabled', 'yes')
        agent_data.setdefault('is_builtin', 'no')
        agent_data.setdefault('create_by', 'system')
        agent_data.setdefault('total_runs', 0)
        agent_data.setdefault('success_rate', 0.0)
        agent_data.setdefault('avg_response_time', 0.0)
        
        # 处理capabilities字段
        if 'capabilities' in agent_data and isinstance(agent_data['capabilities'], list):
            agent_data['agent_capabilities'] = agent_data.pop('capabilities')
        
        return await service.create_agent_template(session, agent_data)
    
    @staticmethod
    async def update_agent(session: AsyncSession, agent_id: str, agent_data: Dict[str, Any]) -> Optional[AgentConfig]:
        """更新智能体（静态方法）"""
        service = AgentService.get_instance()
        
        # 处理capabilities字段
        if 'capabilities' in agent_data and isinstance(agent_data['capabilities'], list):
            agent_data['agent_capabilities'] = agent_data.pop('capabilities')
        
        return await service.update_agent_template(session, agent_id, agent_data)
    
    @staticmethod
    async def delete_agent(session: AsyncSession, agent_id: str) -> bool:
        """删除智能体（静态方法）"""
        service = AgentService.get_instance()
        return await service.delete_agent_template(session, agent_id)
    
    @staticmethod
    async def update_agent_mcp_config(
        session: AsyncSession,
        agent_id: str,
        enabled_servers: List[str],
        selected_tools: List[str]
    ) -> Optional[AgentConfig]:
        """更新智能体MCP配置（静态方法）"""
        service = AgentService.get_instance()
        
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
        
        return await service.update_agent_template(session, agent_id, update_data)
    
    # ==================== 实例方法（新架构） ====================
    
    @transactional()
    async def create_agent_template(
        self, 
        session: AsyncSession,
        agent_data: Dict[str, Any]
    ) -> AgentConfig:
        """创建智能体配置（实例方法）"""
        # 业务验证
        if not agent_data.get('agent_id'):
            raise ValueError("Agent ID is required")
        
        # 检查是否已存在
        existing = await self._dao.get_by_agent_id(session, agent_data['agent_id'])
        if existing:
            raise ValueError(f"Agent with ID {agent_data['agent_id']} already exists")
        
        # 检查是否为保留的内置智能体ID
        if agent_data['agent_id'] in BUILTIN_AGENTS and agent_data.get('is_builtin') != 'yes':
            raise ValueError(f"Agent ID {agent_data['agent_id']} is reserved for builtin agents")
        
        logger.info(f"Creating agent: {agent_data['agent_id']}")
        return await self._dao.create(session, agent_data)
    
    async def get_agent_by_id(
        self, 
        session: AsyncSession, 
        agent_id: str
    ) -> Optional[AgentConfig]:
        """根据ID获取智能体配置（实例方法）"""
        return await self._dao.get_by_agent_id(session, agent_id)
    
    async def get_agent_list(
        self, 
        session: AsyncSession,
        enabled_only: bool = True,
        status: Optional[str] = None,
        builtin_only: Optional[bool] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取智能体列表（实例方法）"""
        offset = (page - 1) * size
        
        # 构建过滤条件
        filters = {}
        if enabled_only:
            filters['agent_enabled'] = 'yes'
            filters['is_active'] = True
        if status:
            filters['agent_status'] = status
        if builtin_only is not None:
            filters['is_builtin'] = 'yes' if builtin_only else 'no'
        
        # 获取数据和总数
        agents = await self._dao.get_list(
            session, 
            filters=filters if filters else None,
            limit=size, 
            offset=offset,
            order_by='create_time'
        )
        
        total = await self._dao.count(session, filters=filters if filters else None)
        
        return {
            'items': [agent.to_dict() for agent in agents],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    @transactional()
    async def update_agent_template(
        self, 
        session: AsyncSession,
        agent_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[AgentConfig]:
        """更新智能体配置（实例方法）"""
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
                raise ValueError(f"Agent with ID {agent_id} not found")
        
        # 移除不可更新的字段
        update_data.pop('agent_id', None)
        update_data.pop('create_time', None)
        update_data.pop('create_by', None)
        
        logger.info(f"Updating agent: {agent_id}")
        return await self._dao.update_by_field(session, 'agent_id', agent_id, update_data)
    
    @transactional()
    async def delete_agent_template(
        self, 
        session: AsyncSession,
        agent_id: str
    ) -> bool:
        """删除智能体配置（实例方法）"""
        # 检查是否存在
        existing = await self._dao.get_by_agent_id(session, agent_id)
        if not existing:
            return False
        
        # 检查是否为内置智能体
        if existing.is_builtin == 'yes':
            raise ValueError(f"Cannot delete builtin agent: {agent_id}")
        
        logger.info(f"Deleting agent: {agent_id}")
        return await self._dao.delete_by_field(session, 'agent_id', agent_id) > 0
    
    async def get_agent_statistics(
        self, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """获取智能体统计信息（实例方法）"""
        total_agents = await self._dao.count(session)
        enabled_agents = await self._dao.count_enabled_agents(session)
        builtin_agents = await self._dao.count_builtin_agents(session)
        
        return {
            'total': total_agents + len(BUILTIN_AGENTS),  # 包含内置智能体
            'enabled': enabled_agents,
            'builtin': builtin_agents + len(BUILTIN_AGENTS),
            'custom': total_agents - builtin_agents
        }
    
    # ==================== 向后兼容方法 ====================
    
    async def get_by_agent_id(self, session: AsyncSession, agent_id: str) -> Optional[AgentConfig]:
        """根据智能体ID获取配置（向后兼容）"""
        return await self.get_agent_by_id(session, agent_id)
    
    async def get_enabled_agents(self, session: AsyncSession) -> List[AgentConfig]:
        """获取所有启用的智能体（向后兼容）"""
        return await self._dao.get_enabled_agents(session)
    
    async def get_builtin_agents(self, session: AsyncSession) -> List[AgentConfig]:
        """获取所有内置智能体（向后兼容）"""
        return await self._dao.get_builtin_agents(session)
    
    async def get_running_agents(self, session: AsyncSession) -> List[AgentConfig]:
        """获取正在运行的智能体（向后兼容）"""
        return await self._dao.get_by_status(session, 'running')
    
    async def update_run_statistics(
        self,
        session: AsyncSession,
        agent_id: str,
        total_runs: int,
        success_rate: float,
        avg_response_time: float
    ) -> Optional[AgentConfig]:
        """更新运行统计信息（向后兼容）"""
        return await self._dao.update_statistics(
            session, agent_id, total_runs, success_rate, avg_response_time
        )


# 创建全局实例以支持导入使用
agent_service = AgentService()