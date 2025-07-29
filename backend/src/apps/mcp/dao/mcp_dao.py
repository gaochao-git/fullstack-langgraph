"""MCP Server数据访问对象 - 纯异步实现"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from src.shared.db.dao.base_dao import BaseDAO
from src.apps.mcp.models import MCPServer


class MCPDAO(BaseDAO[MCPServer]):
    """MCP服务器数据访问对象 - 纯异步实现"""
    
    def __init__(self):
        super().__init__(MCPServer)
    
    async def get_by_server_id(self, session: AsyncSession, server_id: str) -> Optional[MCPServer]:
        """根据Server ID查询服务器"""
        return await self.get_by_field(session, 'server_id', server_id)
    
    async def search_by_name(
        self, 
        session: AsyncSession, 
        name_keyword: str,
        enabled_only: bool = True,
        team_name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCPServer]:
        """根据名称关键词搜索MCP服务器"""
        query = select(self.model).where(
            self.model.server_name.contains(name_keyword)
        )
        
        if enabled_only:
            query = query.where(self.model.is_enabled == 'on')
        
        if team_name:
            query = query.where(self.model.team_name == team_name)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_all_teams(self, session: AsyncSession) -> List[str]:
        """获取所有团队"""
        result = await session.execute(
            select(distinct(self.model.team_name))
            .where(self.model.team_name.isnot(None))
            .order_by(self.model.team_name)
        )
        return [team for team in result.scalars().all() if team]
    
    async def get_status_statistics(self, session: AsyncSession):
        """获取状态统计 - 返回原始查询结果"""
        result = await session.execute(
            select(
                self.model.connection_status.label('status'),
                func.count(self.model.id).label('count')
            )
            .where(self.model.is_enabled == 'on')
            .group_by(self.model.connection_status)
            .order_by(func.count(self.model.id).desc())
        )
        return result
    
    async def get_enabled_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取启用的服务器"""
        filters = {'is_enabled': 'on'}
        return await self.get_list(session, filters=filters, order_by='create_time')
    
    async def get_connected_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取已连接的服务器"""
        filters = {'is_enabled': 'on', 'connection_status': 'connected'}
        return await self.get_list(session, filters=filters, order_by='create_time')
    
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
        update_data = {'server_tools': json.dumps(tools)}
        return await self.update_by_field(session, 'server_id', server_id, update_data)