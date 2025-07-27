"""
用户服务类
专门处理用户相关的业务逻辑
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .base_service import BaseService
from ..models import User, UserThread


class UserService(BaseService[User]):
    """用户服务"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_username(self, session: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.get_by_field(session, 'user_name', username)
    
    async def get_active_users(self, session: AsyncSession) -> List[User]:
        """获取活跃用户"""
        return await self.get_list(
            session,
            filters={'is_active': True},
            order_by='last_login'
        )
    
    async def get_by_user_type(self, session: AsyncSession, user_type: str) -> List[User]:
        """根据用户类型获取用户"""
        return await self.get_list(
            session,
            filters={'user_type': user_type},
            order_by='create_time'
        )
    
    async def update_last_login(
        self,
        session: AsyncSession,
        username: str
    ) -> Optional[User]:
        """更新最后登录时间"""
        from ..models import now_shanghai
        
        return await self.update_by_field(
            session,
            'user_name',
            username,
            last_login=now_shanghai()
        )


class UserThreadService(BaseService[UserThread]):
    """用户线程服务"""
    
    def __init__(self):
        super().__init__(UserThread)
    
    async def get_user_threads(
        self,
        session: AsyncSession,
        username: str,
        limit: Optional[int] = 10
    ) -> List[UserThread]:
        """获取用户的线程列表"""
        return await self.get_list(
            session,
            filters={'user_name': username, 'is_archived': False},
            order_by='last_message_time',
            limit=limit
        )
    
    async def get_by_thread_id(
        self,
        session: AsyncSession,
        username: str,
        thread_id: str
    ) -> Optional[UserThread]:
        """获取特定用户的线程"""
        from sqlalchemy import select, and_
        
        result = await session.execute(
            select(UserThread).where(
                and_(
                    UserThread.user_name == username,
                    UserThread.thread_id == thread_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def archive_thread(
        self,
        session: AsyncSession,
        username: str,
        thread_id: str
    ) -> Optional[UserThread]:
        """归档线程"""
        thread = await self.get_by_thread_id(session, username, thread_id)
        if thread:
            return await self.update(
                session,
                thread.id,
                is_archived=True
            )
        return None
    
    async def update_message_count(
        self,
        session: AsyncSession,
        username: str,
        thread_id: str,
        message_count: int
    ) -> Optional[UserThread]:
        """更新消息数量"""
        from ..models import now_shanghai
        
        thread = await self.get_by_thread_id(session, username, thread_id)
        if thread:
            return await self.update(
                session,
                thread.id,
                message_count=message_count,
                last_message_time=now_shanghai()
            )
        return None