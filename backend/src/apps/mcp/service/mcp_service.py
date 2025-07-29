"""MCP服务层 - 简化的纯异步实现"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func, case, distinct

from src.apps.mcp.models import MCPServer
from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.apps.mcp.schema import MCPServerCreate, MCPServerUpdate, MCPQueryParams

logger = get_logger(__name__)


class MCPService:
    """MCP服务 - 清晰的单一职责实现"""
    
    async def create_server(
        self, 
        session: AsyncSession, 
        server_data: MCPServerCreate
    ) -> MCPServer:
        """创建MCP服务器"""
        async with session.begin():
            # 业务验证
            result = await session.execute(
                select(MCPServer).where(MCPServer.server_id == server_data.server_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError(f"MCP server with ID {server_data.server_id} already exists")
            
            # 转换数据
            data = server_data.dict()
            
            # 设置默认值
            data.setdefault('is_enabled', 'on')
            data.setdefault('connection_status', 'disconnected')
            data.setdefault('team_name', 'default')
            data.setdefault('create_by', 'system')
            data.setdefault('create_time', now_shanghai())
            data.setdefault('update_time', now_shanghai())
            
            logger.info(f"Creating MCP server: {server_data.server_id}")
            instance = MCPServer(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance
    
    async def get_server_by_id(
        self, 
        session: AsyncSession, 
        server_id: str
    ) -> Optional[MCPServer]:
        """根据ID获取MCP服务器"""
        result = await session.execute(
            select(MCPServer).where(MCPServer.server_id == server_id)
        )
        return result.scalar_one_or_none()
    
    async def list_servers(
        self, 
        session: AsyncSession, 
        params: MCPQueryParams
    ) -> Tuple[List[MCPServer], int]:
        """列出MCP服务器"""
        # 搜索功能
        if params.search:
            query = select(MCPServer).where(
                MCPServer.server_name.contains(params.search)
            )
            conditions = []
            if params.is_enabled:
                conditions.append(MCPServer.is_enabled == params.is_enabled)
            if params.connection_status:
                conditions.append(MCPServer.connection_status == params.connection_status)
            if params.team_name:
                conditions.append(MCPServer.team_name == params.team_name)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.offset(params.offset).limit(params.limit)
            result = await session.execute(query)
            servers = list(result.scalars().all())
            
            # 获取搜索总数
            count_query = select(func.count(MCPServer.id)).where(
                MCPServer.server_name.contains(params.search)
            )
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar()
        else:
            # 普通查询
            query = select(MCPServer)
            conditions = []
            if params.is_enabled:
                conditions.append(MCPServer.is_enabled == params.is_enabled)
            if params.connection_status:
                conditions.append(MCPServer.connection_status == params.connection_status)
            if params.team_name:
                conditions.append(MCPServer.team_name == params.team_name)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(MCPServer.create_time.desc())
            query = query.offset(params.offset).limit(params.limit)
            result = await session.execute(query)
            servers = list(result.scalars().all())
            
            # 计算总数
            count_query = select(func.count(MCPServer.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar()
        
        return servers, total
    
    async def update_server(
        self, 
        session: AsyncSession, 
        server_id: str, 
        server_data: MCPServerUpdate
    ) -> Optional[MCPServer]:
        """更新MCP服务器"""
        async with session.begin():
            # 检查是否存在
            result = await session.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                raise ValueError(f"MCP server with ID {server_id} not found")
            
            # 转换数据
            data = server_data.dict(exclude_unset=True)
            
            # 移除不可更新字段
            data.pop('server_id', None)
            data.pop('create_time', None)
            data.pop('create_by', None)
            data['update_by'] = 'system'
            data['update_time'] = now_shanghai()
            
            logger.info(f"Updating MCP server: {server_id}")
            await session.execute(
                update(MCPServer).where(MCPServer.server_id == server_id).values(**data)
            )
            
            # 返回更新后的数据
            result = await session.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            return result.scalar_one_or_none()
    
    async def delete_server(
        self, 
        session: AsyncSession, 
        server_id: str
    ) -> bool:
        """删除MCP服务器"""
        async with session.begin():
            # 检查是否存在
            result = await session.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                return False
            
            logger.info(f"Deleting MCP server: {server_id}")
            result = await session.execute(
                delete(MCPServer).where(MCPServer.server_id == server_id)
            )
            return result.rowcount > 0
    
    async def get_teams(self, session: AsyncSession) -> List[str]:
        """获取所有团队"""
        result = await session.execute(
            select(distinct(MCPServer.team_name)).where(
                MCPServer.team_name.isnot(None)
            )
        )
        return [row[0] for row in result.fetchall()]
    
    async def get_status_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取状态统计"""
        result = await session.execute(
            select(
                MCPServer.connection_status.label('status'),
                func.count(MCPServer.id).label('count')
            ).group_by(MCPServer.connection_status)
        )
        return [{'status': row.status, 'count': row.count} for row in result.fetchall()]
    
    async def get_enabled_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取启用的服务器（兼容性方法）"""
        result = await session.execute(
            select(MCPServer).where(MCPServer.is_enabled == 'on')
        )
        return list(result.scalars().all())
    
    async def get_connected_servers(self, session: AsyncSession) -> List[MCPServer]:
        """获取已连接的服务器（兼容性方法）"""
        result = await session.execute(
            select(MCPServer).where(MCPServer.connection_status == 'connected')
        )
        return list(result.scalars().all())
    
    async def update_connection_status(
        self,
        session: AsyncSession,
        server_id: str,
        status: str
    ) -> Optional[MCPServer]:
        """更新连接状态"""
        async with session.begin():
            update_data = {
                'connection_status': status,
                'update_time': now_shanghai()
            }
            await session.execute(
                update(MCPServer).where(MCPServer.server_id == server_id).values(**update_data)
            )
            
            result = await session.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            return result.scalar_one_or_none()
    
    async def update_server_tools(
        self,
        session: AsyncSession,
        server_id: str,
        tools: List[str]
    ) -> Optional[MCPServer]:
        """更新服务器工具列表"""
        async with session.begin():
            # 转换工具列表为JSON字符串或直接使用列表（根据数据库字段类型）
            import json
            update_data = {
                'available_tools': json.dumps(tools) if tools else None,
                'update_time': now_shanghai()
            }
            await session.execute(
                update(MCPServer).where(MCPServer.server_id == server_id).values(**update_data)
            )
            
            result = await session.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            return result.scalar_one_or_none()


# 全局实例
mcp_service = MCPService()