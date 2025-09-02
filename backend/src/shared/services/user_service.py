"""
用户服务层 - 统一的服务类实现
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, update, delete

from src.apps.user.models import User, UserThread
from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode

logger = get_logger(__name__)


class UserService:
    """用户服务 - 与项目其他服务类风格一致"""
    
    async def get_user_by_name(self, db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await db.execute(
            select(User).where(User.user_name == username)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_users(self, db: AsyncSession) -> List[User]:
        """获取活跃用户"""
        result = await db.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())
    
    async def create_user(self, db: AsyncSession, user_data: Dict[str, Any]) -> User:
        """创建用户"""
        async with db.begin():
            # 业务验证
            if not user_data.get('user_name'):
                raise BusinessException("用户名是必需的", ResponseCode.BAD_REQUEST)
            
            # 检查用户名是否已存在
            result = await db.execute(
                select(User).where(User.user_name == user_data['user_name'])
            )
            if result.scalar_one_or_none():
                raise BusinessException(
                    f"用户名 {user_data['user_name']} 已存在",
                    ResponseCode.DUPLICATE_RESOURCE
                )
            
            # 检查邮箱是否已存在
            if user_data.get('email'):
                result = await db.execute(
                    select(User).where(User.email == user_data['email'])
                )
                if result.scalar_one_or_none():
                    raise BusinessException(
                        f"邮箱 {user_data['email']} 已被使用",
                        ResponseCode.DUPLICATE_RESOURCE
                    )
            
            # 设置默认值
            user_data.setdefault('user_id', f"user_{now_shanghai().timestamp()}")
            user_data.setdefault('user_type', 'regular')
            user_data.setdefault('is_active', True)
            user_data.setdefault('create_time', now_shanghai())
            user_data.setdefault('update_time', now_shanghai())
            
            # 创建用户
            user = User(**user_data)
            db.add(user)
            await db.flush()
            await db.refresh(user)
            
            logger.info(f"Created user: {user.user_name}")
            return user
    
    async def update_user(
        self,
        db: AsyncSession,
        username: str,
        update_data: Dict[str, Any]
    ) -> Optional[User]:
        """更新用户信息"""
        async with db.begin():
            # 检查用户是否存在
            result = await db.execute(
                select(User).where(User.user_name == username)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise BusinessException(
                    f"用户 {username} 不存在",
                    ResponseCode.NOT_FOUND
                )
            
            # 如果更新邮箱，检查邮箱是否已被使用
            if 'email' in update_data and update_data['email'] != user.email:
                result = await db.execute(
                    select(User).where(
                        and_(
                            User.email == update_data['email'],
                            User.user_name != username
                        )
                    )
                )
                if result.scalar_one_or_none():
                    raise BusinessException(
                        f"邮箱 {update_data['email']} 已被使用",
                        ResponseCode.DUPLICATE_RESOURCE
                    )
            
            # 更新字段
            update_data['update_time'] = now_shanghai()
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
    
    async def delete_user(self, db: AsyncSession, username: str) -> bool:
        """删除用户（软删除）"""
        async with db.begin():
            update_data = {
                'is_active': False,
                'update_time': now_shanghai()
            }
            result = await db.execute(
                update(User)
                .where(User.user_name == username)
                .values(**update_data)
            )
            return result.rowcount > 0
    
    async def update_last_login(self, db: AsyncSession, username: str) -> Optional[User]:
        """更新最后登录时间"""
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
    
    async def search_users(
        self,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[User], int]:
        """搜索用户"""
        offset = (page - 1) * page_size
        
        # 构建搜索条件
        search_condition = or_(
            User.user_name.contains(keyword),
            User.display_name.contains(keyword),
            User.email.contains(keyword)
        )
        
        # 查询数据
        query = select(User).where(search_condition)
        query = query.order_by(User.create_time.desc())
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        users = list(result.scalars().all())
        
        # 统计总数
        count_query = select(func.count(User.id)).where(search_condition)
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return users, total
    
    async def get_user_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """获取用户统计信息"""
        # 总用户数
        total_result = await db.execute(
            select(func.count(User.id))
        )
        total_users = total_result.scalar()
        
        # 活跃用户数
        active_result = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_result.scalar()
        
        # 今日新增
        today = now_shanghai().date()
        today_result = await db.execute(
            select(func.count(User.id)).where(
                func.date(User.create_time) == today
            )
        )
        today_users = today_result.scalar()
        
        return {
            'total': total_users,
            'active': active_users,
            'inactive': total_users - active_users,
            'today_new': today_users
        }


class UserThreadService:
    """用户会话服务 - 与项目其他服务类风格一致"""
    
    async def get_user_threads(
        self,
        db: AsyncSession,
        username: str,
        page: int = 1,
        page_size: int = 10,
        archived: Optional[bool] = None
    ) -> Tuple[List[UserThread], int]:
        """获取用户的所有会话"""
        offset = (page - 1) * page_size
        
        # 构建查询条件
        query = select(UserThread).where(UserThread.user_name == username)
        if archived is not None:
            query = query.where(UserThread.is_archived == archived)
        
        # 排序和分页
        query = query.order_by(UserThread.update_at.desc())
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        threads = list(result.scalars().all())
        
        # 统计总数
        count_query = select(func.count(UserThread.id)).where(
            UserThread.user_name == username
        )
        if archived is not None:
            count_query = count_query.where(UserThread.is_archived == archived)
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return threads, total
    
    async def create_thread(self, db: AsyncSession, thread_data: Dict[str, Any]) -> UserThread:
        """创建用户会话"""
        async with db.begin():
            # 验证必要字段
            if not thread_data.get('user_name'):
                raise BusinessException("用户名是必需的", ResponseCode.BAD_REQUEST)
            if not thread_data.get('thread_id'):
                raise BusinessException("会话ID是必需的", ResponseCode.BAD_REQUEST)
            
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
                raise BusinessException(
                    f"会话 {thread_data['thread_id']} 已存在",
                    ResponseCode.DUPLICATE_RESOURCE
                )
            
            # 设置默认值
            thread_data.setdefault('thread_title', f"会话 {now_shanghai().strftime('%Y-%m-%d %H:%M')}")
            thread_data.setdefault('message_count', 0)
            thread_data.setdefault('is_archived', False)
            thread_data.setdefault('create_at', now_shanghai())
            thread_data.setdefault('update_at', now_shanghai())
            
            # 创建会话
            thread = UserThread(**thread_data)
            db.add(thread)
            await db.flush()
            await db.refresh(thread)
            
            logger.info(f"Created thread: {thread.thread_id} for user: {thread.user_name}")
            return thread
    
    async def update_thread(
        self,
        db: AsyncSession,
        username: str,
        thread_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[UserThread]:
        """更新会话信息"""
        async with db.begin():
            # 检查会话是否存在
            result = await db.execute(
                select(UserThread).where(
                    and_(
                        UserThread.user_name == username,
                        UserThread.thread_id == thread_id
                    )
                )
            )
            thread = result.scalar_one_or_none()
            if not thread:
                raise BusinessException(
                    f"会话 {thread_id} 不存在",
                    ResponseCode.NOT_FOUND
                )
            
            # 更新字段
            update_data['update_at'] = now_shanghai()
            await db.execute(
                update(UserThread)
                .where(
                    and_(
                        UserThread.user_name == username,
                        UserThread.thread_id == thread_id
                    )
                )
                .values(**update_data)
            )
            
            # 返回更新后的会话
            result = await db.execute(
                select(UserThread).where(
                    and_(
                        UserThread.user_name == username,
                        UserThread.thread_id == thread_id
                    )
                )
            )
            return result.scalar_one_or_none()
    
    async def delete_thread(
        self,
        db: AsyncSession,
        username: str,
        thread_id: str
    ) -> bool:
        """删除会话"""
        async with db.begin():
            result = await db.execute(
                delete(UserThread).where(
                    and_(
                        UserThread.user_name == username,
                        UserThread.thread_id == thread_id
                    )
                )
            )
            return result.rowcount > 0
    
    async def archive_thread(
        self,
        db: AsyncSession,
        username: str,
        thread_id: str,
        archived: bool = True
    ) -> Optional[UserThread]:
        """归档或取消归档会话"""
        return await self.update_thread(
            db, username, thread_id,
            {'is_archived': archived}
        )
    
    async def update_message_count(
        self,
        db: AsyncSession,
        username: str,
        thread_id: str,
        increment: int = 1
    ) -> Optional[UserThread]:
        """更新会话消息数量"""
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
            
            if not thread:
                return None
            
            # 更新消息数量
            new_count = max(0, (thread.message_count or 0) + increment)
            
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
    
    async def get_thread_statistics(
        self,
        db: AsyncSession,
        username: str
    ) -> Dict[str, Any]:
        """获取用户会话统计信息"""
        # 总会话数
        total_result = await db.execute(
            select(func.count(UserThread.id)).where(
                UserThread.user_name == username
            )
        )
        total_threads = total_result.scalar()
        
        # 归档会话数
        archived_result = await db.execute(
            select(func.count(UserThread.id)).where(
                and_(
                    UserThread.user_name == username,
                    UserThread.is_archived == True
                )
            )
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