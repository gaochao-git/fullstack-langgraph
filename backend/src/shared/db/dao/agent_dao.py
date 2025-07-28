"""
Agent数据访问对象
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .base_dao import BaseDAO
from ..models import AgentConfig


class AgentDAO(BaseDAO[AgentConfig]):
    """智能体配置数据访问对象"""
    
    def __init__(self):
        super().__init__(AgentConfig)
    
    # ==================== 专用查询方法 ====================
    
    async def get_by_agent_id(self, session: AsyncSession, agent_id: str) -> Optional[AgentConfig]:
        """根据Agent ID查询配置"""
        return await self.get_by_field(session, 'agent_id', agent_id)
    
    async def get_enabled_agents(
        self, 
        session: AsyncSession,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AgentConfig]:
        """查询启用的智能体"""
        filters = {'agent_enabled': 'yes', 'is_active': True}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def get_builtin_agents(
        self, 
        session: AsyncSession,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AgentConfig]:
        """查询内置智能体"""
        filters = {'is_builtin': 'yes'}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def get_by_status(
        self, 
        session: AsyncSession, 
        status: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AgentConfig]:
        """根据状态查询智能体"""
        filters = {'agent_status': status}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def search_by_name(
        self, 
        session: AsyncSession, 
        name_keyword: str,
        enabled_only: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AgentConfig]:
        """根据名称关键词搜索智能体"""
        from sqlalchemy import select, and_
        
        query = select(self.model).where(
            self.model.agent_name.contains(name_keyword)
        )
        
        if enabled_only:
            query = query.where(
                and_(
                    self.model.agent_enabled == 'yes',
                    self.model.is_active == True
                )
            )
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def update_agent_status(
        self, 
        session: AsyncSession, 
        agent_id: str, 
        status: str
    ) -> Optional[AgentConfig]:
        """更新智能体状态"""
        update_data = {'agent_status': status}
        return await self.update_by_field(session, 'agent_id', agent_id, update_data)
    
    async def update_statistics(
        self, 
        session: AsyncSession, 
        agent_id: str,
        total_runs: int,
        success_rate: float,
        avg_response_time: float
    ) -> Optional[AgentConfig]:
        """更新智能体运行统计"""
        from ..models import now_shanghai
        
        update_data = {
            'total_runs': total_runs,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'last_used': now_shanghai()
        }
        return await self.update_by_field(session, 'agent_id', agent_id, update_data)
    
    async def count_enabled_agents(self, session: AsyncSession) -> int:
        """统计启用的智能体数量"""
        filters = {'agent_enabled': 'yes', 'is_active': True}
        return await self.count(session, filters=filters)
    
    async def count_builtin_agents(self, session: AsyncSession) -> int:
        """统计内置智能体数量"""
        filters = {'is_builtin': 'yes'}
        return await self.count(session, filters=filters)
    
    # ==================== 同步方法（兼容） ====================
    
    def sync_get_by_agent_id(self, session: Session, agent_id: str) -> Optional[AgentConfig]:
        """同步根据Agent ID查询配置"""
        return session.query(self.model).filter(self.model.agent_id == agent_id).first()
    
    def sync_get_enabled_agents(
        self, 
        session: Session,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AgentConfig]:
        """同步查询启用的智能体"""
        query = session.query(self.model).filter(
            self.model.agent_enabled == 'yes',
            self.model.is_active == True
        )
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()