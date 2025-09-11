"""MCP服务层 - 简化的纯异步实现"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, func, case, distinct, or_

from src.apps.mcp.models import MCPServer, MCPServerPermission
from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.apps.mcp.schema import MCPServerCreate, MCPServerUpdate, MCPQueryParams, MCPServerPermissionCreate, MCPServerPermissionUpdate

logger = get_logger(__name__)


class MCPService:
    """MCP服务 - 清晰的单一职责实现"""
    
    async def create_server(
        self, 
        db: AsyncSession, 
        server_data: MCPServerCreate,
        current_user: dict
    ) -> MCPServer:
        """创建MCP服务器"""
        async with db.begin():
            # 业务验证
            result = await db.execute(
                select(MCPServer).where(MCPServer.server_id == server_data.server_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise BusinessException(f"MCP服务器ID {server_data.server_id} 已存在", ResponseCode.CONFLICT)
            
            # 转换数据
            data = server_data.dict()
            
            # 处理server_tools字段 - 转换为JSON字符串
            if 'server_tools' in data and data['server_tools'] is not None:
                import json
                data['server_tools'] = json.dumps(data['server_tools'])
            
            # 处理server_config字段 - 转换为JSON字符串
            if 'server_config' in data and data['server_config'] is not None:
                import json
                data['server_config'] = json.dumps(data['server_config'])
            
            # 设置默认值
            data.setdefault('is_enabled', 'on')
            data.setdefault('connection_status', 'disconnected')
            data.setdefault('team_name', 'default')
            
            # 从当前用户获取username
            username = current_user.get('username') or current_user.get('sub', 'system')
            data['create_by'] = username
            data['update_by'] = username
            data['create_time'] = now_shanghai()
            data['update_time'] = now_shanghai()
            
            logger.info(f"Creating MCP server: {server_data.server_id} by user: {username}")
            instance = MCPServer(**data)
            db.add(instance)
            await db.flush()
            await db.refresh(instance)
            return instance
    
    async def get_server_by_id(
        self, 
        db: AsyncSession, 
        server_id: str
    ) -> Optional[MCPServer]:
        """根据ID获取MCP服务器"""
        result = await db.execute(
            select(MCPServer).where(MCPServer.server_id == server_id)
        )
        return result.scalar_one_or_none()
    
    def get_server_by_id_sync(
        self, 
        session: Session, 
        server_id: str
    ) -> Optional[MCPServer]:
        """根据ID获取MCP服务器（同步版本）"""
        result = session.execute(
            select(MCPServer).where(MCPServer.server_id == server_id)
        )
        return result.scalar_one_or_none()
    
    async def list_servers(
        self, 
        db: AsyncSession, 
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
            result = await db.execute(query)
            servers = list(result.scalars().all())
            
            # 获取搜索总数
            count_query = select(func.count(MCPServer.id)).where(
                MCPServer.server_name.contains(params.search)
            )
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await db.execute(count_query)
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
            result = await db.execute(query)
            servers = list(result.scalars().all())
            
            # 计算总数
            count_query = select(func.count(MCPServer.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await db.execute(count_query)
            total = count_result.scalar()
        
        return servers, total
    
    async def update_server(
        self, 
        db: AsyncSession, 
        server_id: str, 
        server_data: MCPServerUpdate,
        current_user: dict
    ) -> Optional[MCPServer]:
        """更新MCP服务器"""
        async with db.begin():
            # 检查是否存在
            result = await db.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 检查当前用户是否是服务器创建者
            username = current_user.get('username') or current_user.get('sub', 'system')
            if existing.create_by != username:
                raise BusinessException("只有服务器创建者才能更新服务器配置", ResponseCode.FORBIDDEN)
            
            # 转换数据
            data = server_data.dict(exclude_unset=True)
            
            # 处理server_tools字段 - 转换为JSON字符串
            if 'server_tools' in data and data['server_tools'] is not None:
                import json
                data['server_tools'] = json.dumps(data['server_tools'])
            
            # 处理server_config字段 - 转换为JSON字符串
            if 'server_config' in data and data['server_config'] is not None:
                import json
                data['server_config'] = json.dumps(data['server_config'])
            
            # 移除不可更新字段
            data.pop('server_id', None)
            data.pop('create_by', None)  # 不更新创建者
            data.pop('create_time', None)
            
            # 从当前用户获取username并设置update_by
            username = current_user.get('username') or current_user.get('sub', 'system')
            data['update_by'] = username
            data['update_time'] = now_shanghai()
            
            logger.info(f"Updating MCP server: {server_id} by user: {username}")
            await db.execute(
                update(MCPServer).where(MCPServer.server_id == server_id).values(**data)
            )
            
            # 返回更新后的数据
            result = await db.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            return result.scalar_one_or_none()
    
    async def delete_server(
        self, 
        db: AsyncSession, 
        server_id: str,
        current_user: dict
    ) -> bool:
        """删除MCP服务器"""
        async with db.begin():
            # 检查是否存在
            result = await db.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                return False
            
            # 检查当前用户是否是服务器创建者
            username = current_user.get('username') or current_user.get('sub', 'system')
            if existing.create_by != username:
                raise BusinessException("只有服务器创建者才能删除服务器", ResponseCode.FORBIDDEN)
            
            logger.info(f"Deleting MCP server: {server_id} by user: {username}")
            result = await db.execute(
                delete(MCPServer).where(MCPServer.server_id == server_id)
            )
            return result.rowcount > 0
    
    async def get_teams(self, db: AsyncSession) -> List[str]:
        """获取所有团队"""
        result = await db.execute(
            select(distinct(MCPServer.team_name)).where(
                MCPServer.team_name.isnot(None)
            )
        )
        return [row[0] for row in result.fetchall()]
    
    async def get_status_statistics(
        self, 
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取状态统计"""
        result = await db.execute(
            select(
                MCPServer.connection_status.label('status'),
                func.count(MCPServer.id).label('count')
            ).group_by(MCPServer.connection_status)
        )
        return [{'status': row.status, 'count': row.count} for row in result.fetchall()]
    
    async def get_enabled_servers(self, db: AsyncSession) -> List[MCPServer]:
        """获取启用的服务器（兼容性方法）"""
        result = await db.execute(
            select(MCPServer).where(MCPServer.is_enabled == 'on')
        )
        return list(result.scalars().all())
    
    async def get_connected_servers(self, db: AsyncSession) -> List[MCPServer]:
        """获取已连接的服务器（兼容性方法）"""
        result = await db.execute(
            select(MCPServer).where(MCPServer.connection_status == 'connected')
        )
        return list(result.scalars().all())
    
    async def update_connection_status(
        self,
        db: AsyncSession,
        server_id: str,
        status: str
    ) -> Optional[MCPServer]:
        """更新连接状态"""
        async with db.begin():
            update_data = {
                'connection_status': status,
                'update_time': now_shanghai()
            }
            await db.execute(
                update(MCPServer).where(MCPServer.server_id == server_id).values(**update_data)
            )
            
            result = await db.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            return result.scalar_one_or_none()
    
    async def update_server_tools(
        self,
        db: AsyncSession,
        server_id: str,
        tools: List[str]
    ) -> Optional[MCPServer]:
        """更新服务器工具列表"""
        async with db.begin():
            # 转换工具列表为JSON字符串或直接使用列表（根据数据库字段类型）
            import json
            update_data = {
                'available_tools': json.dumps(tools) if tools else None,
                'update_time': now_shanghai()
            }
            await db.execute(
                update(MCPServer).where(MCPServer.server_id == server_id).values(**update_data)
            )
            
            result = await db.execute(
                select(MCPServer).where(MCPServer.server_id == server_id)
            )
            return result.scalar_one_or_none()
    
    # ==================== 权限管理相关方法 ====================
    
    async def create_server_permission(
        self,
        db: AsyncSession,
        server_id: str,
        permission_data: MCPServerPermissionCreate,
        current_user: dict
    ) -> MCPServerPermission:
        """创建服务器权限"""
        async with db.begin():
            # 检查服务器是否存在
            server = await self.get_server_by_id(db, server_id)
            if not server:
                raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 检查当前用户是否是服务器创建者
            username = current_user.get('username') or current_user.get('sub', 'system')
            if server.create_by != username:
                raise BusinessException("只有服务器创建者才能管理权限", ResponseCode.FORBIDDEN)
            
            # 检查权限是否已存在
            result = await db.execute(
                select(MCPServerPermission).where(
                    and_(
                        MCPServerPermission.server_id == server_id,
                        MCPServerPermission.user_name == permission_data.user_name
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise BusinessException(f"用户 {permission_data.user_name} 的权限已存在", ResponseCode.CONFLICT)
            
            # 创建权限记录
            data = permission_data.dict()
            data['server_id'] = server_id
            data['create_by'] = username
            data['update_by'] = username
            data['create_time'] = now_shanghai()
            data['update_time'] = now_shanghai()
            
            # 如果没有提供server_key，自动生成一个
            if not data.get('server_key'):
                import secrets
                data['server_key'] = f"sk_{secrets.token_urlsafe(32)}"
            
            instance = MCPServerPermission(**data)
            db.add(instance)
            await db.flush()
            await db.refresh(instance)
            return instance
    
    async def get_server_permissions(
        self,
        db: AsyncSession,
        server_id: str,
        current_user: dict
    ) -> List[MCPServerPermission]:
        """获取服务器的所有权限"""
        # 检查服务器是否存在
        server = await self.get_server_by_id(db, server_id)
        if not server:
            raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
        
        # 检查当前用户是否是服务器创建者
        username = current_user.get('username') or current_user.get('sub', 'system')
        if server.create_by != username:
            raise BusinessException("只有服务器创建者才能查看权限", ResponseCode.FORBIDDEN)
        
        result = await db.execute(
            select(MCPServerPermission).where(
                MCPServerPermission.server_id == server_id
            ).order_by(MCPServerPermission.create_time.desc())
        )
        permissions = list(result.scalars().all())
        return permissions
    
    async def update_server_permission(
        self,
        db: AsyncSession,
        server_id: str,
        permission_id: int,
        permission_data: MCPServerPermissionUpdate,
        current_user: dict
    ) -> Optional[MCPServerPermission]:
        """更新服务器权限"""
        async with db.begin():
            # 检查服务器是否存在
            server = await self.get_server_by_id(db, server_id)
            if not server:
                raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 检查当前用户是否是服务器创建者
            username = current_user.get('username') or current_user.get('sub', 'system')
            if server.create_by != username:
                raise BusinessException("只有服务器创建者才能管理权限", ResponseCode.FORBIDDEN)
            
            # 检查权限是否存在
            result = await db.execute(
                select(MCPServerPermission).where(
                    and_(
                        MCPServerPermission.id == permission_id,
                        MCPServerPermission.server_id == server_id
                    )
                )
            )
            permission = result.scalar_one_or_none()
            if not permission:
                return None
            
            # 更新权限
            update_data = permission_data.dict(exclude_unset=True)
            if update_data:
                update_data['update_by'] = username
                update_data['update_time'] = now_shanghai()
                
                await db.execute(
                    update(MCPServerPermission).where(
                        MCPServerPermission.id == permission_id
                    ).values(**update_data)
                )
                
                result = await db.execute(
                    select(MCPServerPermission).where(MCPServerPermission.id == permission_id)
                )
                permission = result.scalar_one_or_none()
            
            return permission
    
    async def delete_server_permission(
        self,
        db: AsyncSession,
        server_id: str,
        permission_id: int,
        current_user: dict
    ) -> bool:
        """删除服务器权限"""
        async with db.begin():
            # 检查服务器是否存在
            server = await self.get_server_by_id(db, server_id)
            if not server:
                raise BusinessException(f"MCP服务器 {server_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 检查当前用户是否是服务器创建者
            username = current_user.get('username') or current_user.get('sub', 'system')
            if server.create_by != username:
                raise BusinessException("只有服务器创建者才能管理权限", ResponseCode.FORBIDDEN)
            
            # 删除权限
            result = await db.execute(
                delete(MCPServerPermission).where(
                    and_(
                        MCPServerPermission.id == permission_id,
                        MCPServerPermission.server_id == server_id
                    )
                )
            )
            return result.rowcount > 0
    
    async def get_user_accessible_servers(
        self,
        db: AsyncSession,
        username: str
    ) -> List[MCPServer]:
        """获取用户有权限访问的服务器列表"""
        # 查询用户创建的服务器或有权限的服务器
        result = await db.execute(
            select(MCPServer).where(
                or_(
                    MCPServer.create_by == username,
                    MCPServer.server_id.in_(
                        select(MCPServerPermission.server_id).where(
                            and_(
                                MCPServerPermission.user_name == username,
                                MCPServerPermission.is_active == 1
                            )
                        )
                    )
                )
            ).where(MCPServer.is_enabled == 'on')
        )
        return list(result.scalars().all())


# 全局实例
mcp_service = MCPService()