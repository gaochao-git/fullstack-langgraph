"""MCP服务层 - 简化的纯异步实现"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.mcp.dao import MCPDAO
from src.apps.mcp.models import MCPServer
from src.shared.db.transaction import transactional
from src.shared.core.logging import get_logger
from src.apps.mcp.schema.mcp import MCPServerCreate, MCPServerUpdate, MCPQueryParams

logger = get_logger(__name__)


class MCPService:
    """MCP服务 - 清晰的单一职责实现"""
    
    def __init__(self):
        self._dao = MCPDAO()
    
    @transactional()
    async def create_server(
        self, 
        session: AsyncSession, 
        server_data: MCPServerCreate
    ) -> MCPServer:
        """创建MCP服务器"""
        # 业务验证
        existing = await self._dao.get_by_server_id(session, server_data.server_id)
        if existing:
            raise ValueError(f"MCP server with ID {server_data.server_id} already exists")
        
        # 转换数据
        data = server_data.dict()
        
        # 设置默认值
        data.setdefault('is_enabled', 'on')
        data.setdefault('connection_status', 'disconnected')
        data.setdefault('team_name', 'default')
        data.setdefault('create_by', 'system')
        
        logger.info(f"Creating MCP server: {server_data.server_id}")
        return await self._dao.create(session, data)
    
    async def get_server_by_id(
        self, 
        session: AsyncSession, 
        server_id: str
    ) -> Optional[MCPServer]:
        """根据ID获取MCP服务器"""
        return await self._dao.get_by_server_id(session, server_id)
    
    async def list_servers(
        self, 
        session: AsyncSession, 
        params: MCPQueryParams
    ) -> Tuple[List[MCPServer], int]:
        """列出MCP服务器"""
        # 构建过滤条件
        filters = {}
        if params.is_enabled:
            filters['is_enabled'] = params.is_enabled
        if params.connection_status:
            filters['connection_status'] = params.connection_status
        if params.team_name:
            filters['team_name'] = params.team_name
        
        # 搜索功能
        if params.search:
            servers = await self._dao.search_by_name(
                session,
                params.search,
                enabled_only=params.is_enabled == 'on' if params.is_enabled else True,
                team_name=params.team_name,
                limit=params.limit,
                offset=params.offset
            )
            # 获取搜索总数
            all_results = await self._dao.search_by_name(
                session, 
                params.search,
                enabled_only=params.is_enabled == 'on' if params.is_enabled else True,
                team_name=params.team_name
            )
            total = len(all_results)
        else:
            # 普通查询
            servers = await self._dao.get_list(
                session,
                filters=filters if filters else None,
                limit=params.limit,
                offset=params.offset,
                order_by='create_time'
            )
            total = await self._dao.count(session, filters=filters if filters else None)
        
        return servers, total
    
    @transactional()
    async def update_server(
        self, 
        session: AsyncSession, 
        server_id: str, 
        server_data: MCPServerUpdate
    ) -> Optional[MCPServer]:
        """更新MCP服务器"""
        # 检查是否存在
        existing = await self._dao.get_by_server_id(session, server_id)
        if not existing:
            raise ValueError(f"MCP server with ID {server_id} not found")
        
        # 转换数据
        data = server_data.dict(exclude_unset=True)
        
        # 移除不可更新字段
        data.pop('server_id', None)
        data.pop('create_time', None)
        data.pop('create_by', None)
        data['update_by'] = 'system'
        
        logger.info(f"Updating MCP server: {server_id}")
        return await self._dao.update_by_field(session, 'server_id', server_id, data)
    
    @transactional()
    async def delete_server(
        self, 
        session: AsyncSession, 
        server_id: str
    ) -> bool:
        """删除MCP服务器"""
        existing = await self._dao.get_by_server_id(session, server_id)
        if not existing:
            return False
        
        logger.info(f"Deleting MCP server: {server_id}")
        return await self._dao.delete_by_field(session, 'server_id', server_id) > 0
    
    async def get_teams(self, session: AsyncSession) -> List[str]:
        """获取所有团队"""
        return await self._dao.get_all_teams(session)
    
    async def get_status_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取状态统计"""
        return await self._dao.get_status_statistics(session)
    
    async def get_enabled_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取启用的服务器（兼容性方法）"""
        return await self._dao.get_enabled_servers(session)
    
    async def get_connected_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取已连接的服务器（兼容性方法）"""
        return await self._dao.get_connected_servers(session)
    
    @transactional()
    async def update_connection_status(
        self,
        session: AsyncSession,
        server_id: str,
        status: str
    ) -> Optional[MCPServer]:
        """更新连接状态"""
        return await self._dao.update_connection_status(session, server_id, status)
    
    @transactional()
    async def update_server_tools(
        self,
        session: AsyncSession,
        server_id: str,
        tools: List[str]
    ) -> Optional[MCPServer]:
        """更新服务器工具列表"""
        return await self._dao.update_server_tools(session, server_id, tools)


# 全局实例
mcp_service = MCPService()