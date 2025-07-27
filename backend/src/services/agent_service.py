"""
Agent业务服务层
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..db.dao import AgentDAO
from ..db.models import AgentConfig
from ..db.transaction import transactional, sync_transactional
from ..core.logging import get_logger

logger = get_logger(__name__)


class AgentService:
    """智能体配置业务服务"""
    
    def __init__(self):
        self.dao = AgentDAO()
    
    # ==================== 异步业务方法 ====================
    
    @transactional()
    async def create_agent(
        self, 
        session: AsyncSession,
        agent_data: Dict[str, Any]
    ) -> AgentConfig:
        """创建智能体配置"""
        # 业务验证
        if not agent_data.get('agent_id'):
            raise ValueError("Agent ID is required")
        
        # 检查是否已存在
        existing = await self.dao.get_by_agent_id(session, agent_data['agent_id'])
        if existing:
            raise ValueError(f"Agent with ID {agent_data['agent_id']} already exists")
        
        # 设置默认值
        agent_data.setdefault('agent_status', 'stopped')
        agent_data.setdefault('agent_enabled', 'yes')
        agent_data.setdefault('is_builtin', 'no')
        agent_data.setdefault('create_by', 'system')
        
        logger.info(f"Creating agent: {agent_data['agent_id']}")
        return await self.dao.create(session, agent_data)
    
    async def get_agent_by_id(
        self, 
        session: AsyncSession, 
        agent_id: str
    ) -> Optional[AgentConfig]:
        """根据ID获取智能体配置"""
        return await self.dao.get_by_agent_id(session, agent_id)
    
    async def get_agent_list(
        self, 
        session: AsyncSession,
        enabled_only: bool = True,
        status: Optional[str] = None,
        builtin_only: Optional[bool] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取智能体列表"""
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
        agents = await self.dao.get_list(
            session, 
            filters=filters if filters else None,
            limit=size, 
            offset=offset
        )
        
        total = await self.dao.count(session, filters=filters if filters else None)
        
        return {
            'items': [agent.to_dict() for agent in agents],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    @transactional()
    async def update_agent_status(
        self, 
        session: AsyncSession,
        agent_id: str,
        status: str
    ) -> Optional[AgentConfig]:
        """更新智能体状态"""
        logger.info(f"Updating agent status: {agent_id} -> {status}")
        return await self.dao.update_agent_status(session, agent_id, status)
    
    @transactional()
    async def update_agent_statistics(
        self, 
        session: AsyncSession,
        agent_id: str,
        total_runs: int,
        success_rate: float,
        avg_response_time: float
    ) -> Optional[AgentConfig]:
        """更新智能体运行统计"""
        logger.info(f"Updating agent statistics: {agent_id}")
        return await self.dao.update_statistics(
            session, agent_id, total_runs, success_rate, avg_response_time
        )
    
    # ==================== 向后兼容方法 ====================
    
    async def get_by_agent_id(self, session: AsyncSession, agent_id: str) -> Optional[AgentConfig]:
        """根据智能体ID获取配置（向后兼容）"""
        return await self.get_agent_by_id(session, agent_id)
    
    async def get_enabled_agents(self, session: AsyncSession) -> List[AgentConfig]:
        """获取所有启用的智能体（向后兼容）"""
        return await self.dao.get_enabled_agents(session)
    
    async def get_builtin_agents(self, session: AsyncSession) -> List[AgentConfig]:
        """获取所有内置智能体（向后兼容）"""
        return await self.dao.get_builtin_agents(session)
    
    async def get_running_agents(self, session: AsyncSession) -> List[AgentConfig]:
        """获取正在运行的智能体（向后兼容）"""
        return await self.dao.get_by_status(session, 'running')
    
    async def update_run_statistics(
        self,
        session: AsyncSession,
        agent_id: str,
        total_runs: int,
        success_rate: float,
        avg_response_time: float
    ) -> Optional[AgentConfig]:
        """更新运行统计信息（向后兼容）"""
        return await self.update_agent_statistics(
            session, agent_id, total_runs, success_rate, avg_response_time
        )