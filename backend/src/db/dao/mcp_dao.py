"""
MCP Server数据访问对象
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .base_dao import BaseDAO
from ..models import MCPServer


class MCPDAO(BaseDAO[MCPServer]):
    """MCP服务器数据访问对象"""
    
    def __init__(self):
        super().__init__(MCPServer)
    
    # ==================== 专用查询方法 ====================
    
    async def get_by_server_id(self, session: AsyncSession, server_id: str) -> Optional[MCPServer]:
        """根据Server ID查询服务器"""
        return await self.get_by_field(session, 'server_id', server_id)
    
    async def get_enabled_servers(
        self, 
        session: AsyncSession,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCPServer]:
        """查询启用的MCP服务器"""
        filters = {'is_enabled': 'on'}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def get_by_status(
        self, 
        session: AsyncSession, 
        status: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCPServer]:
        """根据连接状态查询服务器"""
        filters = {'connection_status': status}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def get_by_team(
        self, 
        session: AsyncSession, 
        team_name: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCPServer]:
        """根据团队查询MCP服务器"""
        filters = {'team_name': team_name}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def search_by_name(
        self, 
        session: AsyncSession, 
        name_keyword: str,
        enabled_only: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCPServer]:
        """根据名称关键词搜索MCP服务器"""
        from sqlalchemy import select, and_
        
        query = select(self.model).where(
            self.model.server_name.contains(name_keyword)
        )
        
        if enabled_only:
            query = query.where(self.model.is_enabled == 'on')
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def update_connection_status(
        self, 
        session: AsyncSession, 
        server_id: str, 
        status: str
    ) -> Optional[MCPServer]:
        """更新服务器连接状态"""
        update_data = {'connection_status': status}
        return await self.update_by_field(session, 'server_id', server_id, update_data)
    
    async def update_server_tools(
        self, 
        session: AsyncSession, 
        server_id: str, 
        tools: List[str]
    ) -> Optional[MCPServer]:
        """更新服务器工具列表"""
        import json
        update_data = {'server_tools': json.dumps(tools)}
        return await self.update_by_field(session, 'server_id', server_id, update_data)
    
    async def get_connected_servers(
        self, 
        session: AsyncSession,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCPServer]:
        """查询已连接的MCP服务器"""
        filters = {'is_enabled': 'on', 'connection_status': 'connected'}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def count_enabled_servers(self, session: AsyncSession) -> int:
        """统计启用的服务器数量"""
        filters = {'is_enabled': 'on'}
        return await self.count(session, filters=filters)
    
    async def count_connected_servers(self, session: AsyncSession) -> int:
        """统计已连接的服务器数量"""
        filters = {'is_enabled': 'on', 'connection_status': 'connected'}
        return await self.count(session, filters=filters)
    
    # ==================== 同步方法（兼容） ====================
    
    def sync_get_by_server_id(self, session: Session, server_id: str) -> Optional[MCPServer]:
        """同步根据Server ID查询服务器"""
        return session.query(self.model).filter(self.model.server_id == server_id).first()
    
    def sync_get_enabled_servers(
        self, 
        session: Session,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCPServer]:
        """同步查询启用的MCP服务器"""
        query = session.query(self.model).filter(self.model.is_enabled == 'on')
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()