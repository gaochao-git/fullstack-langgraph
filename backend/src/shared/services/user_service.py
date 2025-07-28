"""
User统一服务层
同时支持静态方法（兼容现有API）和实例方法（新架构）
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..db.dao import UserDAO, UserThreadDAO
from ..db.models import User, UserThread
from ..db.transaction import transactional, sync_transactional
from ..core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """用户服务 - 支持新旧两种调用方式"""
    
    _instance = None
    _dao = None
    
    def __init__(self):
        if not self._dao:
            self._dao = UserDAO()
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    # ==================== 静态方法（兼容现有API） ====================
    
    @staticmethod
    async def get_user_by_name(session: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户（静态方法）"""
        service = UserService.get_instance()
        return await service._dao.get_by_username(session, username)
    
    @staticmethod
    async def get_active_users(session: AsyncSession) -> List[User]:
        """获取活跃用户（静态方法）"""
        service = UserService.get_instance()
        return await service._dao.get_active_users(session)
    
    @staticmethod
    async def create_user(session: AsyncSession, user_data: Dict[str, Any]) -> User:
        """创建用户（静态方法）"""
        service = UserService.get_instance()
        return await service.create_user_account(session, user_data)
    
    @staticmethod
    async def update_last_login(session: AsyncSession, username: str) -> Optional[User]:
        """更新最后登录时间（静态方法）"""
        service = UserService.get_instance()
        return await service._dao.update_last_login(session, username)
    
    # ==================== 实例方法（新架构） ====================
    
    @transactional()
    async def create_user_account(
        self, 
        session: AsyncSession,
        user_data: Dict[str, Any]
    ) -> User:
        """创建用户账户（实例方法）"""
        # 业务验证
        if not user_data.get('user_name'):
            raise ValueError("Username is required")
        
        # 检查用户名是否已存在
        existing = await self._dao.get_by_username(session, user_data['user_name'])
        if existing:
            raise ValueError(f"User with name {user_data['user_name']} already exists")
        
        # 检查邮箱是否已存在
        if user_data.get('email'):
            existing_email = await self._dao.get_by_email(session, user_data['email'])
            if existing_email:
                raise ValueError(f"User with email {user_data['email']} already exists")
        
        # 设置默认值
        user_data.setdefault('user_type', 'regular')
        user_data.setdefault('is_active', True)
        
        logger.info(f"Creating user: {user_data['user_name']}")
        return await self._dao.create(session, user_data)
    
    async def get_user_by_id(
        self, 
        session: AsyncSession, 
        user_id: int
    ) -> Optional[User]:
        """根据ID获取用户（实例方法）"""
        return await self._dao.get_by_id(session, user_id)
    
    async def get_user_list(
        self, 
        session: AsyncSession,
        active_only: bool = True,
        user_type: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取用户列表（实例方法）"""
        offset = (page - 1) * size
        
        # 构建过滤条件
        filters = {}
        if active_only:
            filters['is_active'] = True
        if user_type:
            filters['user_type'] = user_type
        
        # 获取数据和总数
        users = await self._dao.get_list(
            session, 
            filters=filters if filters else None,
            limit=size, 
            offset=offset,
            order_by='create_time'
        )
        
        total = await self._dao.count(session, filters=filters if filters else None)
        
        return {
            'items': [user.to_dict() for user in users],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    async def search_users(
        self, 
        session: AsyncSession,
        keyword: str,
        active_only: bool = True,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """搜索用户（实例方法）"""
        offset = (page - 1) * size
        
        users = await self._dao.search_by_name(
            session, 
            keyword,
            active_only=active_only,
            limit=size, 
            offset=offset
        )
        
        # 获取搜索结果总数（简化实现）
        all_results = await self._dao.search_by_name(session, keyword, active_only=active_only)
        total = len(all_results)
        
        return {
            'items': [user.to_dict() for user in users],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size,
            'keyword': keyword
        }
    
    @transactional()
    async def update_user(
        self, 
        session: AsyncSession,
        username: str,
        update_data: Dict[str, Any]
    ) -> Optional[User]:
        """更新用户信息（实例方法）"""
        # 检查是否存在
        existing = await self._dao.get_by_username(session, username)
        if not existing:
            raise ValueError(f"User with name {username} not found")
        
        # 移除不可更新的字段
        update_data.pop('user_name', None)
        update_data.pop('create_time', None)
        
        logger.info(f"Updating user: {username}")
        return await self._dao.update_by_field(session, 'user_name', username, update_data)
    
    @transactional()
    async def deactivate_user(
        self, 
        session: AsyncSession,
        username: str
    ) -> Optional[User]:
        """停用用户（实例方法）"""
        logger.info(f"Deactivating user: {username}")
        return await self._dao.deactivate_user(session, username)
    
    async def get_user_statistics(
        self, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """获取用户统计信息（实例方法）"""
        total_users = await self._dao.count(session)
        active_users = await self._dao.count_active_users(session)
        regular_users = await self._dao.count_by_user_type(session, 'regular')
        admin_users = await self._dao.count_by_user_type(session, 'admin')
        
        return {
            'total': total_users,
            'active': active_users,
            'inactive': total_users - active_users,
            'regular': regular_users,
            'admin': admin_users
        }
    
    # ==================== 向后兼容方法 ====================
    
    async def get_by_username(self, session: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户（向后兼容）"""
        return await self._dao.get_by_username(session, username)


class UserThreadService:
    """用户会话服务 - 支持新旧两种调用方式"""
    
    _instance = None
    _dao = None
    
    def __init__(self):
        if not self._dao:
            self._dao = UserThreadDAO()
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    # ==================== 静态方法（兼容现有API） ====================
    
    @staticmethod
    async def get_user_threads(
        session: AsyncSession, 
        username: str,
        include_archived: bool = False
    ) -> List[UserThread]:
        """获取用户会话（静态方法）"""
        service = UserThreadService.get_instance()
        return await service._dao.get_user_threads(session, username, include_archived)
    
    @staticmethod
    async def create_thread(session: AsyncSession, thread_data: Dict[str, Any]) -> UserThread:
        """创建用户会话（静态方法）"""
        service = UserThreadService.get_instance()
        return await service.create_user_thread(session, thread_data)
    
    @staticmethod
    async def update_thread_message_count(
        session: AsyncSession, 
        username: str, 
        thread_id: str,
        count: int
    ) -> Optional[UserThread]:
        """更新会话消息数量（静态方法）"""
        service = UserThreadService.get_instance()
        return await service._dao.update_message_count(session, username, thread_id, count)
    
    # ==================== 实例方法（新架构） ====================
    
    @transactional()
    async def create_user_thread(
        self, 
        session: AsyncSession,
        thread_data: Dict[str, Any]
    ) -> UserThread:
        """创建用户会话（实例方法）"""
        # 业务验证
        if not thread_data.get('user_name'):
            raise ValueError("Username is required")
        if not thread_data.get('thread_id'):
            raise ValueError("Thread ID is required")
        
        # 检查是否已存在
        existing = await self._dao.get_by_user_and_thread(
            session, thread_data['user_name'], thread_data['thread_id']
        )
        if existing:
            raise ValueError(f"Thread {thread_data['thread_id']} already exists for user {thread_data['user_name']}")
        
        # 设置默认值
        thread_data.setdefault('is_archived', False)
        thread_data.setdefault('message_count', 0)
        
        logger.info(f"Creating thread {thread_data['thread_id']} for user {thread_data['user_name']}")
        return await self._dao.create(session, thread_data)
    
    async def get_user_thread_list(
        self, 
        session: AsyncSession,
        username: str,
        include_archived: bool = False,
        agent_id: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取用户会话列表（实例方法）"""
        offset = (page - 1) * size
        
        # 构建过滤条件
        filters = {'user_name': username}
        if not include_archived:
            filters['is_archived'] = False
        if agent_id:
            filters['agent_id'] = agent_id
        
        # 获取数据和总数
        threads = await self._dao.get_list(
            session, 
            filters=filters,
            limit=size, 
            offset=offset,
            order_by='update_at'
        )
        
        total = await self._dao.count(session, filters=filters)
        
        return {
            'items': [thread.to_dict() for thread in threads],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    @transactional()
    async def archive_user_thread(
        self, 
        session: AsyncSession,
        username: str,
        thread_id: str
    ) -> Optional[UserThread]:
        """归档用户会话（实例方法）"""
        logger.info(f"Archiving thread {thread_id} for user {username}")
        return await self._dao.archive_thread(session, username, thread_id)
    
    async def get_thread_statistics(
        self, 
        session: AsyncSession,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取会话统计信息（实例方法）"""
        if username:
            # 单个用户的统计
            total_threads = await self._dao.count_user_threads(session, username, include_archived=True)
            active_threads = await self._dao.count_user_threads(session, username, include_archived=False)
            
            return {
                'user': username,
                'total': total_threads,
                'active': active_threads,
                'archived': total_threads - active_threads
            }
        else:
            # 全局统计
            total_threads = await self._dao.count(session)
            archived_threads = await self._dao.count(session, filters={'is_archived': True})
            
            return {
                'total': total_threads,
                'active': total_threads - archived_threads,
                'archived': archived_threads
            }


# 创建全局实例以支持导入使用
user_service = UserService()
user_thread_service = UserThreadService()