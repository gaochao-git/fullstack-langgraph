"""
User统一服务层
直接使用 SQLAlchemy，不依赖 DAO 层
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, update, delete

from src.apps.user.models import User, UserThread
from src.shared.db.models import now_shanghai
from src.shared.db.transaction import transactional, sync_transactional
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """用户服务 - 支持新旧两种调用方式"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    # ==================== 静态方法（兼容现有API） ====================
    
    @staticmethod
    async def get_user_by_name(db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户（静态方法）"""
        result = await db.execute(
            select(User).where(User.user_name == username)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_users(db: AsyncSession) -> List[User]:
        """获取活跃用户（静态方法）"""
        result = await db.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: Dict[str, Any]) -> User:
        """创建用户（静态方法）"""
        service = UserService.get_instance()
        return await service.create_user_account(db, user_data)
    
    @staticmethod
    async def update_last_login(db: AsyncSession, username: str) -> Optional[User]:
        """更新最后登录时间（静态方法）"""
        async with db.begin():
            result = await db.execute(
                update(User)
                .where(User.user_name == username)
                .values(last_login=now_shanghai())
            )
            if result.rowcount > 0:
                result = await db.execute(
                    select(User).where(User.user_name == username)
                )
                return result.scalar_one_or_none()
        return None
    
    # ==================== 实例方法（新架构） ====================
    
    @transactional()
    async def create_user_account(
        self, 
        db: AsyncSession,
        user_data: Dict[str, Any]
    ) -> User:
        """创建用户账户（实例方法）"""
        # 业务验证
        if not user_data.get('user_name'):
            raise ValueError("Username is required")
        
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.user_name == user_data['user_name'])
        )
        if result.scalar_one_or_none():
            raise ValueError(f"User with name {user_data['user_name']} already exists")
        
        # 检查邮箱是否已存在
        if user_data.get('email'):
            result = await db.execute(
                select(User).where(User.email == user_data['email'])
            )
            if result.scalar_one_or_none():
                raise ValueError(f"User with email {user_data['email']} already exists")
        
        # 设置默认值
        user_data.setdefault('user_type', 'regular')
        user_data.setdefault('is_active', True)
        user_data.setdefault('create_time', now_shanghai())
        user_data.setdefault('update_time', now_shanghai())
        
        # 创建用户
        logger.info(f"Creating user: {user_data['user_name']}")
        user = User(**user_data)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    
    async def get_user_by_id(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[User]:
        """根据ID获取用户（实例方法）"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_list(
        self, 
        db: AsyncSession,
        active_only: bool = True,
        user_type: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取用户列表（实例方法）"""
        offset = (page - 1) * size
        
        # 构建查询
        query = select(User)
        conditions = []
        
        if active_only:
            conditions.append(User.is_active == True)
        if user_type:
            conditions.append(User.user_type == user_type)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 获取数据
        query = query.order_by(User.create_time.desc()).offset(offset).limit(size)
        result = await db.execute(query)
        users = list(result.scalars().all())
        
        # 获取总数
        count_query = select(func.count(User.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return {
            'items': [user.to_dict() for user in users],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    async def search_users(
        self, 
        db: AsyncSession,
        keyword: str,
        active_only: bool = True,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """搜索用户（实例方法）"""
        offset = (page - 1) * size
        
        # 构建查询
        query = select(User).where(
            or_(
                User.user_name.contains(keyword),
                User.display_name.contains(keyword)
            )
        )
        
        if active_only:
            query = query.where(User.is_active == True)
        
        # 获取数据
        query = query.order_by(User.create_time.desc()).offset(offset).limit(size)
        result = await db.execute(query)
        users = list(result.scalars().all())
        
        # 获取总数
        count_query = select(func.count(User.id)).where(
            or_(
                User.user_name.contains(keyword),
                User.display_name.contains(keyword)
            )
        )
        if active_only:
            count_query = count_query.where(User.is_active == True)
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
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
        db: AsyncSession,
        username: str,
        update_data: Dict[str, Any]
    ) -> Optional[User]:
        """更新用户信息（实例方法）"""
        # 检查是否存在
        result = await db.execute(
            select(User).where(User.user_name == username)
        )
        if not result.scalar_one_or_none():
            raise ValueError(f"User with name {username} not found")
        
        # 移除不可更新的字段
        update_data.pop('user_name', None)
        update_data.pop('create_time', None)
        update_data['update_time'] = now_shanghai()
        
        # 更新
        logger.info(f"Updating user: {username}")
        await db.execute(
            update(User)
            .where(User.user_name == username)
            .values(**update_data)
        )
        
        # 返回更新后的用户
        result = await db.execute(
            select(User).where(User.user_name == username)
        )
        return result.scalar_one_or_none()
    
    @transactional()
    async def deactivate_user(
        self, 
        db: AsyncSession,
        username: str
    ) -> Optional[User]:
        """停用用户（实例方法）"""
        logger.info(f"Deactivating user: {username}")
        return await self.update_user(db, username, {'is_active': False})
    
    async def get_user_statistics(
        self, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """获取用户统计信息（实例方法）"""
        # 总用户数
        total_result = await db.execute(select(func.count(User.id)))
        total_users = total_result.scalar()
        
        # 活跃用户数
        active_result = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_result.scalar()
        
        # 普通用户数
        regular_result = await db.execute(
            select(func.count(User.id)).where(User.user_type == 'regular')
        )
        regular_users = regular_result.scalar()
        
        # 管理员用户数
        admin_result = await db.execute(
            select(func.count(User.id)).where(User.user_type == 'admin')
        )
        admin_users = admin_result.scalar()
        
        return {
            'total': total_users,
            'active': active_users,
            'inactive': total_users - active_users,
            'regular': regular_users,
            'admin': admin_users
        }
    
    # ==================== 向后兼容方法 ====================
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户（向后兼容）"""
        return await self.get_user_by_name(db, username)


class UserThreadService:
    """用户会话服务 - 支持新旧两种调用方式"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    # ==================== 静态方法（兼容现有API） ====================
    
    @staticmethod
    async def get_user_threads(
        db: AsyncSession, 
        username: str,
        include_archived: bool = False
    ) -> List[UserThread]:
        """获取用户会话（静态方法）"""
        query = select(UserThread).where(UserThread.user_name == username)
        if not include_archived:
            query = query.where(UserThread.is_archived == False)
        query = query.order_by(UserThread.update_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def create_thread(db: AsyncSession, thread_data: Dict[str, Any]) -> UserThread:
        """创建用户会话（静态方法）"""
        service = UserThreadService.get_instance()
        return await service.create_user_thread(db, thread_data)
    
    @staticmethod
    async def update_thread_message_count(
        db: AsyncSession, 
        username: str, 
        thread_id: str,
        count: int
    ) -> Optional[UserThread]:
        """更新会话消息数量（静态方法）"""
        async with db.begin():
            # 先获取当前记录
            result = await db.execute(
                select(UserThread).where(
                    and_(
                        UserThread.user_name == username,
                        UserThread.thread_id == thread_id
                    )
                )
            )
            thread = result.scalar_one_or_none()
            
            if thread:
                # 更新消息数量
                new_count = max(0, (thread.message_count or 0) + count)
                await db.execute(
                    update(UserThread)
                    .where(
                        and_(
                            UserThread.user_name == username,
                            UserThread.thread_id == thread_id
                        )
                    )
                    .values(
                        message_count=new_count,
                        last_message_time=now_shanghai(),
                        update_at=now_shanghai()
                    )
                )
                
                # 返回更新后的记录
                result = await db.execute(
                    select(UserThread).where(
                        and_(
                            UserThread.user_name == username,
                            UserThread.thread_id == thread_id
                        )
                    )
                )
                return result.scalar_one_or_none()
        
        return None
    
    # ==================== 实例方法（新架构） ====================
    
    @transactional()
    async def create_user_thread(
        self, 
        db: AsyncSession,
        thread_data: Dict[str, Any]
    ) -> UserThread:
        """创建用户会话（实例方法）"""
        # 业务验证
        if not thread_data.get('user_name'):
            raise ValueError("Username is required")
        if not thread_data.get('thread_id'):
            raise ValueError("Thread ID is required")
        
        # 检查是否已存在
        result = await db.execute(
            select(UserThread).where(
                and_(
                    UserThread.user_name == thread_data['user_name'],
                    UserThread.thread_id == thread_data['thread_id']
                )
            )
        )
        if result.scalar_one_or_none():
            raise ValueError(f"Thread {thread_data['thread_id']} already exists for user {thread_data['user_name']}")
        
        # 设置默认值
        thread_data.setdefault('is_archived', False)
        thread_data.setdefault('message_count', 0)
        thread_data.setdefault('create_at', now_shanghai())
        thread_data.setdefault('update_at', now_shanghai())
        
        # 创建线程
        logger.info(f"Creating thread {thread_data['thread_id']} for user {thread_data['user_name']}")
        thread = UserThread(**thread_data)
        db.add(thread)
        await db.flush()
        await db.refresh(thread)
        return thread
    
    async def get_user_thread_list(
        self, 
        db: AsyncSession,
        username: str,
        include_archived: bool = False,
        agent_id: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取用户会话列表（实例方法）"""
        offset = (page - 1) * size
        
        # 构建查询
        query = select(UserThread).where(UserThread.user_name == username)
        conditions = []
        
        if not include_archived:
            conditions.append(UserThread.is_archived == False)
        if agent_id:
            conditions.append(UserThread.agent_id == agent_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 获取数据
        query = query.order_by(UserThread.update_at.desc()).offset(offset).limit(size)
        result = await db.execute(query)
        threads = list(result.scalars().all())
        
        # 获取总数
        count_query = select(func.count(UserThread.id)).where(UserThread.user_name == username)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
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
        db: AsyncSession,
        username: str,
        thread_id: str
    ) -> Optional[UserThread]:
        """归档用户会话（实例方法）"""
        logger.info(f"Archiving thread {thread_id} for user {username}")
        
        # 更新归档状态
        result = await db.execute(
            update(UserThread)
            .where(
                and_(
                    UserThread.user_name == username,
                    UserThread.thread_id == thread_id
                )
            )
            .values(
                is_archived=True,
                update_at=now_shanghai()
            )
        )
        
        if result.rowcount > 0:
            # 返回更新后的记录
            result = await db.execute(
                select(UserThread).where(
                    and_(
                        UserThread.user_name == username,
                        UserThread.thread_id == thread_id
                    )
                )
            )
            return result.scalar_one_or_none()
        
        return None
    
    async def get_thread_statistics(
        self, 
        db: AsyncSession,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取会话统计信息（实例方法）"""
        if username:
            # 单个用户的统计
            total_query = select(func.count(UserThread.id)).where(UserThread.user_name == username)
            total_result = await db.execute(total_query)
            total_threads = total_result.scalar()
            
            active_query = select(func.count(UserThread.id)).where(
                and_(
                    UserThread.user_name == username,
                    UserThread.is_archived == False
                )
            )
            active_result = await db.execute(active_query)
            active_threads = active_result.scalar()
            
            return {
                'user': username,
                'total': total_threads,
                'active': active_threads,
                'archived': total_threads - active_threads
            }
        else:
            # 全局统计
            total_result = await db.execute(select(func.count(UserThread.id)))
            total_threads = total_result.scalar()
            
            archived_result = await db.execute(
                select(func.count(UserThread.id)).where(UserThread.is_archived == True)
            )
            archived_threads = archived_result.scalar()
            
            return {
                'total': total_threads,
                'active': total_threads - archived_threads,
                'archived': archived_threads
            }


# 创建全局实例以支持导入使用
user_service = UserService()
user_thread_service = UserThreadService()