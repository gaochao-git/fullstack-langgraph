"""
MCP服务类
专门处理MCP服务器配置相关的业务逻辑
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .base_service import BaseService
from ..models import MCPServer


class MCPService(BaseService[MCPServer]):
    """MCP服务器配置服务"""
    
    def __init__(self):
        super().__init__(MCPServer)
    
    async def get_by_server_id(self, session: AsyncSession, server_id: str) -> Optional[MCPServer]:
        """根据服务器ID获取配置"""
        return await self.get_by_field(session, 'server_id', server_id)
    
    async def get_enabled_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取所有启用的MCP服务器"""
        return await self.get_list(
            session,
            filters={'is_enabled': 'on'},
            order_by='create_time'
        )
    
    async def get_connected_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取已连接的MCP服务器"""
        return await self.get_list(
            session,
            filters={'connection_status': 'connected'},
            order_by='create_time'
        )
    
    async def get_by_team(self, session: AsyncSession, team_name: str) -> List[MCPServer]:
        """根据团队获取MCP服务器"""
        return await self.get_list(
            session,
            filters={'team_name': team_name},
            order_by='create_time'
        )
    
    async def update_connection_status(
        self,
        session: AsyncSession,
        server_id: str,
        status: str,
        update_by: str
    ) -> Optional[MCPServer]:
        """更新连接状态"""
        return await self.update_by_field(
            session,
            'server_id',
            server_id,
            connection_status=status,
            update_by=update_by
        )
    
    async def enable_server(
        self,
        session: AsyncSession,
        server_id: str,
        update_by: str
    ) -> Optional[MCPServer]:
        """启用MCP服务器"""
        return await self.update_by_field(
            session,
            'server_id',
            server_id,
            is_enabled='on',
            update_by=update_by
        )
    
    async def disable_server(
        self,
        session: AsyncSession,
        server_id: str,
        update_by: str
    ) -> Optional[MCPServer]:
        """禁用MCP服务器"""
        return await self.update_by_field(
            session,
            'server_id',
            server_id,
            is_enabled='off',
            update_by=update_by
        )