"""
User数据访问对象
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_

from .base_dao import BaseDAO
from src.apps.user.models import User, UserThread


class UserDAO(BaseDAO[User]):
    """用户数据访问对象"""
    
    def __init__(self):
        super().__init__(User)
    
    # ==================== 专用查询方法 ====================
    
    async def get_by_username(self, session: AsyncSession, username: str) -> Optional[User]:
        """根据用户名查询用户"""
        return await self.get_by_field(session, 'user_name', username)
    
    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱查询用户"""
        return await self.get_by_field(session, 'email', email)
    
    async def get_active_users(
        self, 
        session: AsyncSession,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """查询活跃用户"""
        filters = {'is_active': True}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def get_by_user_type(
        self, 
        session: AsyncSession, 
        user_type: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """根据用户类型查询用户"""
        filters = {'user_type': user_type}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def search_by_name(
        self, 
        session: AsyncSession, 
        name_keyword: str,
        active_only: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """根据名称关键词搜索用户"""
        query = select(self.model).where(
            or_(
                self.model.user_name.contains(name_keyword),
                self.model.display_name.contains(name_keyword)
            )
        )
        
        if active_only:
            query = query.where(self.model.is_active == True)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def update_last_login(
        self, 
        session: AsyncSession, 
        username: str
    ) -> Optional[User]:
        """更新最后登录时间"""
        from ..models import now_shanghai
        
        update_data = {'last_login': now_shanghai()}
        return await self.update_by_field(session, 'user_name', username, update_data)
    
    async def deactivate_user(
        self, 
        session: AsyncSession, 
        username: str
    ) -> Optional[User]:
        """停用用户"""
        update_data = {'is_active': False}
        return await self.update_by_field(session, 'user_name', username, update_data)
    
    async def count_active_users(self, session: AsyncSession) -> int:
        """统计活跃用户数量"""
        filters = {'is_active': True}
        return await self.count(session, filters=filters)
    
    async def count_by_user_type(self, session: AsyncSession, user_type: str) -> int:
        """统计指定类型的用户数量"""
        filters = {'user_type': user_type}
        return await self.count(session, filters=filters)
    
    # ==================== 同步方法（兼容） ====================
    
    def sync_get_by_username(self, session: Session, username: str) -> Optional[User]:
        """同步根据用户名查询用户"""
        return session.query(self.model).filter(self.model.user_name == username).first()
    
    def sync_get_active_users(
        self, 
        session: Session,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """同步查询活跃用户"""
        query = session.query(self.model).filter(self.model.is_active == True)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()


class UserThreadDAO(BaseDAO[UserThread]):
    """用户会话数据访问对象"""
    
    def __init__(self):
        super().__init__(UserThread)
    
    # ==================== 专用查询方法 ====================
    
    async def get_by_user_and_thread(
        self, 
        session: AsyncSession, 
        username: str, 
        thread_id: str
    ) -> Optional[UserThread]:
        """根据用户名和线程ID查询会话"""
        filters = {'user_name': username, 'thread_id': thread_id}
        result = await self.get_list(session, filters=filters, limit=1)
        return result[0] if result else None
    
    async def get_user_threads(
        self, 
        session: AsyncSession, 
        username: str,
        include_archived: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UserThread]:
        """获取用户的所有会话"""
        filters = {'user_name': username}
        if not include_archived:
            filters['is_archived'] = False
        
        return await self.get_list(
            session, 
            filters=filters, 
            order_by='update_at',
            limit=limit, 
            offset=offset
        )
    
    async def get_by_agent(
        self, 
        session: AsyncSession, 
        agent_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UserThread]:
        """根据智能体ID查询会话"""
        filters = {'agent_id': agent_id}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def archive_thread(
        self, 
        session: AsyncSession, 
        username: str, 
        thread_id: str
    ) -> Optional[UserThread]:
        """归档会话"""
        filters = {'user_name': username, 'thread_id': thread_id}
        threads = await self.get_list(session, filters=filters, limit=1)
        
        if threads:
            thread = threads[0]
            update_data = {'is_archived': True}
            return await self.update_by_id(session, thread.id, update_data)
        
        return None
    
    async def update_message_count(
        self, 
        session: AsyncSession, 
        username: str, 
        thread_id: str,
        count: int
    ) -> Optional[UserThread]:
        """更新消息数量"""
        from ..models import now_shanghai
        
        filters = {'user_name': username, 'thread_id': thread_id}
        threads = await self.get_list(session, filters=filters, limit=1)
        
        if threads:
            thread = threads[0]
            update_data = {
                'message_count': count,
                'last_message_time': now_shanghai()
            }
            return await self.update_by_id(session, thread.id, update_data)
        
        return None
    
    async def count_user_threads(
        self, 
        session: AsyncSession, 
        username: str,
        include_archived: bool = False
    ) -> int:
        """统计用户会话数量"""
        filters = {'user_name': username}
        if not include_archived:
            filters['is_archived'] = False
        
        return await self.count(session, filters=filters)
    
    # ==================== 同步方法（兼容） ====================
    
    def sync_get_user_threads(
        self, 
        session: Session, 
        username: str,
        include_archived: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UserThread]:
        """同步获取用户的所有会话"""
        query = session.query(self.model).filter(self.model.user_name == username)
        
        if not include_archived:
            query = query.filter(self.model.is_archived == False)
        
        query = query.order_by(self.model.update_at.desc())
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()