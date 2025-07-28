"""
Agent数据访问对象 - 纯异步实现
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update as sql_update
from datetime import datetime

from src.shared.db.dao.base_dao import BaseDAO
from src.apps.agent.models import AgentConfig


class AgentDAO(BaseDAO[AgentConfig]):
    """智能体配置数据访问对象 - 纯异步实现"""
    
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
        return list(result.scalars().all())
    
    async def search_by_keyword(
        self,
        session: AsyncSession,
        keyword: str,
        enabled_only: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AgentConfig]:
        """根据关键词搜索智能体（支持名称和描述）"""
        query = select(self.model).where(
            and_(
                self.model.agent_name.contains(keyword),
                self.model.description.contains(keyword)
            )
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
        return list(result.scalars().all())
    
    async def get_by_capabilities(
        self,
        session: AsyncSession,
        capability: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AgentConfig]:
        """根据能力搜索智能体"""
        query = select(self.model).where(
            self.model.agent_capabilities.contains([capability])
        )
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def update_agent_status(
        self, 
        session: AsyncSession, 
        agent_id: str, 
        status: str
    ) -> Optional[AgentConfig]:
        """更新智能体状态"""
        update_data = {
            'agent_status': status,
            'update_time': datetime.utcnow()
        }
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
        update_data = {
            'total_runs': total_runs,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'last_used': datetime.utcnow(),
            'update_time': datetime.utcnow()
        }
        return await self.update_by_field(session, 'agent_id', agent_id, update_data)
    
    async def batch_update_status(
        self,
        session: AsyncSession,
        agent_ids: List[str],
        status: str
    ) -> int:
        """批量更新智能体状态"""
        stmt = sql_update(self.model).where(
            self.model.agent_id.in_(agent_ids)
        ).values(
            agent_status=status,
            update_time=datetime.utcnow()
        )
        result = await session.execute(stmt)
        return result.rowcount
    
    async def count_enabled_agents(self, session: AsyncSession) -> int:
        """统计启用的智能体数量"""
        filters = {'agent_enabled': 'yes', 'is_active': True}
        return await self.count(session, filters=filters)
    
    async def count_builtin_agents(self, session: AsyncSession) -> int:
        """统计内置智能体数量"""
        filters = {'is_builtin': 'yes'}
        return await self.count(session, filters=filters)
    
    async def count_by_status(self, session: AsyncSession, status: str) -> int:
        """按状态统计智能体数量"""
        query = select(func.count(self.model.id)).where(
            self.model.agent_status == status
        )
        result = await session.execute(query)
        return result.scalar() or 0
    
    async def get_agent_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """获取智能体统计信息"""
        # 总数
        total_query = select(func.count(self.model.id))
        total_result = await session.execute(total_query)
        total = total_result.scalar() or 0
        
        # 启用数量
        enabled_query = select(func.count(self.model.id)).where(
            and_(
                self.model.agent_enabled == 'yes',
                self.model.is_active == True
            )
        )
        enabled_result = await session.execute(enabled_query)
        enabled = enabled_result.scalar() or 0
        
        # 运行中数量
        running_query = select(func.count(self.model.id)).where(
            self.model.agent_status == 'running'
        )
        running_result = await session.execute(running_query)
        running = running_result.scalar() or 0
        
        # 内置智能体数量
        builtin_query = select(func.count(self.model.id)).where(
            self.model.is_builtin == 'yes'
        )
        builtin_result = await session.execute(builtin_query)
        builtin = builtin_result.scalar() or 0
        
        return {
            'total': total,
            'enabled': enabled,
            'running': running,
            'builtin': builtin,
            'custom': total - builtin
        }