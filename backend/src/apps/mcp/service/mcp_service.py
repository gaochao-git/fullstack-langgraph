"""
MCP统一服务层
同时支持静态方法（兼容现有API）和实例方法（新架构）
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..dao import MCPDAO
from src.shared.db.models import MCPServer
from src.shared.db.transaction import transactional, sync_transactional
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class MCPService:
    """MCP服务器服务 - 支持新旧两种调用方式"""
    
    _instance = None
    _dao = None
    
    def __init__(self):
        if not self._dao:
            self._dao = MCPDAO()
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    # ==================== 静态方法（兼容现有API） ====================
    
    @staticmethod
    async def get_enabled_servers(session: AsyncSession) -> List[MCPServer]:
        """获取启用的MCP服务器（静态方法）"""
        service = MCPService.get_instance()
        return await service._dao.get_enabled_servers(session)
    
    @staticmethod
    async def get_server_by_id(session: AsyncSession, server_id: str) -> Optional[MCPServer]:
        """根据ID获取MCP服务器（静态方法）"""
        service = MCPService.get_instance()
        return await service._dao.get_by_server_id(session, server_id)
    
    @staticmethod
    async def update_server_status(
        session: AsyncSession, 
        server_id: str, 
        status: str
    ) -> Optional[MCPServer]:
        """更新服务器状态（静态方法）"""
        service = MCPService.get_instance()
        return await service._dao.update_connection_status(session, server_id, status)
    
    @staticmethod
    async def update_server_tools(
        session: AsyncSession, 
        server_id: str, 
        tools: List[str]
    ) -> Optional[MCPServer]:
        """更新服务器工具列表（静态方法）"""
        service = MCPService.get_instance()
        return await service._dao.update_server_tools(session, server_id, tools)
    
    # ==================== 实例方法（新架构） ====================
    
    @transactional()
    async def create_mcp_server(
        self, 
        session: AsyncSession,
        server_data: Dict[str, Any]
    ) -> MCPServer:
        """创建MCP服务器（实例方法）"""
        # 业务验证
        if not server_data.get('server_id'):
            raise ValueError("Server ID is required")
        
        # 检查是否已存在
        existing = await self._dao.get_by_server_id(session, server_data['server_id'])
        if existing:
            raise ValueError(f"MCP server with ID {server_data['server_id']} already exists")
        
        # 设置默认值
        server_data.setdefault('is_enabled', 'on')
        server_data.setdefault('connection_status', 'disconnected')
        server_data.setdefault('team_name', 'default')
        
        logger.info(f"Creating MCP server: {server_data['server_id']}")
        return await self._dao.create(session, server_data)
    
    async def get_server_by_id(
        self, 
        session: AsyncSession, 
        server_id: str
    ) -> Optional[MCPServer]:
        """根据ID获取MCP服务器（实例方法）"""
        return await self._dao.get_by_server_id(session, server_id)
    
    async def get_server_list(
        self, 
        session: AsyncSession,
        enabled_only: bool = True,
        status: Optional[str] = None,
        team_name: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取MCP服务器列表（实例方法）"""
        offset = (page - 1) * size
        
        # 构建过滤条件
        filters = {}
        if enabled_only:
            filters['is_enabled'] = 'on'
        if status:
            filters['connection_status'] = status
        if team_name:
            filters['team_name'] = team_name
        
        # 获取数据和总数
        servers = await self._dao.get_list(
            session, 
            filters=filters if filters else None,
            limit=size, 
            offset=offset,
            order_by='create_time'
        )
        
        total = await self._dao.count(session, filters=filters if filters else None)
        
        return {
            'items': [server.to_dict() for server in servers],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    @transactional()
    async def update_mcp_server(
        self, 
        session: AsyncSession,
        server_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[MCPServer]:
        """更新MCP服务器（实例方法）"""
        # 检查是否存在
        existing = await self._dao.get_by_server_id(session, server_id)
        if not existing:
            raise ValueError(f"MCP server with ID {server_id} not found")
        
        # 移除不可更新的字段
        update_data.pop('server_id', None)
        update_data.pop('create_time', None)
        update_data.pop('create_by', None)
        
        logger.info(f"Updating MCP server: {server_id}")
        return await self._dao.update_by_field(session, 'server_id', server_id, update_data)
    
    @transactional()
    async def delete_mcp_server(
        self, 
        session: AsyncSession,
        server_id: str
    ) -> bool:
        """删除MCP服务器（实例方法）"""
        # 检查是否存在
        existing = await self._dao.get_by_server_id(session, server_id)
        if not existing:
            return False
        
        logger.info(f"Deleting MCP server: {server_id}")
        return await self._dao.delete_by_field(session, 'server_id', server_id) > 0
    
    async def get_server_statistics(
        self, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """获取MCP服务器统计信息（实例方法）"""
        total_servers = await self._dao.count(session)
        enabled_servers = await self._dao.count_enabled_servers(session)
        connected_servers = await self._dao.count_connected_servers(session)
        
        return {
            'total': total_servers,
            'enabled': enabled_servers,
            'connected': connected_servers,
            'disconnected': enabled_servers - connected_servers
        }
    
    # ==================== 向后兼容方法 ====================
    
    async def get_enabled_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取启用的MCP服务器（向后兼容）"""
        return await self._dao.get_enabled_servers(session)
    
    async def get_connected_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取已连接的MCP服务器（向后兼容）"""
        return await self._dao.get_connected_servers(session)


# 创建全局实例以支持导入使用
mcp_service = MCPService()