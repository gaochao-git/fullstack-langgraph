"""
用户线程数据库操作模块
使用MySQL数据库，与agents.py保持统一的代码风格
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import pytz

# 定义上海时区
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

def now_shanghai():
    """返回上海时区的当前时间"""
    return datetime.now(SHANGHAI_TZ).replace(tzinfo=None)
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import IntegrityError

from src.shared.db.config import get_async_db_context
from src.shared.db.models import User, UserThread

logger = logging.getLogger(__name__)


async def check_user_thread_exists(user_name: str, thread_id: str) -> bool:
    """检查用户线程关联是否存在"""
    try:
        async with get_async_db_context() as session:
            result = await session.execute(
                select(UserThread).where(
                    UserThread.user_name == user_name,
                    UserThread.thread_id == thread_id
                )
            )
            user_thread = result.scalar_one_or_none()
            return user_thread is not None
                    
    except Exception as e:
        logger.error(f"检查用户线程关联失败: {e}")
        return False


async def create_user_thread_mapping(
    user_name: str, 
    thread_id: str, 
    thread_title: Optional[str] = None,
    agent_id: Optional[str] = None
) -> bool:
    """创建用户线程关联"""
    logger.info(f"📝 create_user_thread_mapping 被调用: user={user_name}, thread={thread_id}, title={thread_title}")
    
    try:
        # 如果没有标题，使用时间戳生成默认标题
        if not thread_title:
            thread_title = f"对话 {datetime.now().strftime('%m-%d %H:%M')}"
            logger.info(f"🏷️ 使用默认标题: {thread_title}")
        
        async with get_async_db_context() as session:
            # 检查是否已存在，避免重复插入
            existing = await session.execute(
                select(UserThread).where(
                    UserThread.user_name == user_name,
                    UserThread.thread_id == thread_id
                )
            )
            if existing.scalar_one_or_none():
                logger.info(f"✅ 用户线程关联已存在: {user_name} -> {thread_id}")
                return True
            
            # 创建新的用户线程关联
            new_user_thread = UserThread(
                user_name=user_name,
                thread_id=thread_id,
                thread_title=thread_title,
                agent_id=agent_id,
                message_count=0,
                is_archived=False
            )
            
            session.add(new_user_thread)
            await session.commit()
            
            logger.info(f"✅ 创建用户线程关联成功: {user_name} -> {thread_id}")
            return True
        
    except IntegrityError as e:
        logger.warning(f"用户线程关联已存在，跳过创建: {user_name} -> {thread_id}")
        return True  # 已存在也算成功
    except Exception as e:
        logger.error(f"创建用户线程关联失败: {e}")
        return False


async def get_user_threads(
    user_name: str, 
    limit: int = 10, 
    offset: int = 0,
    archived: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """获取用户的所有线程"""
    try:
        async with get_async_db_context() as session:
            query = select(UserThread).where(UserThread.user_name == user_name)
            
            # 如果指定了archived状态，添加过滤条件
            if archived is not None:
                query = query.where(UserThread.is_archived == archived)
            
            # 排序和分页
            query = query.order_by(UserThread.create_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(query)
            user_threads = result.scalars().all()
            
            return [thread.to_dict() for thread in user_threads]
                    
    except Exception as e:
        logger.error(f"获取用户线程列表失败: {e}")
        return []


async def update_thread_title(
    user_name: str, 
    thread_id: str, 
    new_title: str
) -> bool:
    """更新线程标题"""
    try:
        async with get_async_db_context() as session:
            result = await session.execute(
                update(UserThread)
                .where(
                    UserThread.user_name == user_name,
                    UserThread.thread_id == thread_id
                )
                .values(
                    thread_title=new_title,
                    update_at=now_shanghai()
                )
            )
            
            await session.commit()
            
            # 检查是否有行被更新
            rows_affected = result.rowcount
            success = rows_affected > 0
            
            if success:
                logger.info(f"✅ 更新线程标题成功: {user_name} -> {thread_id} -> {new_title}")
            else:
                logger.warning(f"⚠️ 未找到要更新的线程: {user_name} -> {thread_id}")
            
            return success
                    
    except Exception as e:
        logger.error(f"更新线程标题失败: {e}")
        return False


async def archive_thread(
    user_name: str,
    thread_id: str,
    archived: bool = True
) -> bool:
    """归档或取消归档线程"""
    try:
        async with get_async_db_context() as session:
            result = await session.execute(
                update(UserThread)
                .where(
                    UserThread.user_name == user_name,
                    UserThread.thread_id == thread_id
                )
                .values(
                    is_archived=archived,
                    update_at=now_shanghai()
                )
            )
            
            await session.commit()
            
            rows_affected = result.rowcount
            success = rows_affected > 0
            
            if success:
                action = "归档" if archived else "取消归档"
                logger.info(f"✅ {action}线程成功: {user_name} -> {thread_id}")
            else:
                logger.warning(f"⚠️ 未找到要操作的线程: {user_name} -> {thread_id}")
            
            return success
                    
    except Exception as e:
        logger.error(f"归档线程失败: {e}")
        return False


async def delete_thread(user_name: str, thread_id: str) -> bool:
    """删除用户线程关联"""
    try:
        async with get_async_db_context() as session:
            result = await session.execute(
                delete(UserThread).where(
                    UserThread.user_name == user_name,
                    UserThread.thread_id == thread_id
                )
            )
            
            await session.commit()
            
            rows_affected = result.rowcount
            success = rows_affected > 0
            
            if success:
                logger.info(f"✅ 删除线程成功: {user_name} -> {thread_id}")
            else:
                logger.warning(f"⚠️ 未找到要删除的线程: {user_name} -> {thread_id}")
            
            return success
                    
    except Exception as e:
        logger.error(f"删除线程失败: {e}")
        return False


async def update_thread_message_count(
    user_name: str,
    thread_id: str,
    increment: int = 1
) -> bool:
    """更新线程消息数量"""
    try:
        async with get_async_db_context() as session:
            # 先获取当前记录
            result = await session.execute(
                select(UserThread).where(
                    UserThread.user_name == user_name,
                    UserThread.thread_id == thread_id
                )
            )
            user_thread = result.scalar_one_or_none()
            
            if not user_thread:
                logger.warning(f"⚠️ 未找到线程记录: {user_name} -> {thread_id}")
                return False
            
            # 更新消息数量和最后消息时间
            new_count = max(0, (user_thread.message_count or 0) + increment)
            
            await session.execute(
                update(UserThread)
                .where(
                    UserThread.user_name == user_name,
                    UserThread.thread_id == thread_id
                )
                .values(
                    message_count=new_count,
                    last_message_time=now_shanghai(),
                    update_at=now_shanghai()
                )
            )
            
            await session.commit()
            logger.info(f"✅ 更新线程消息数量成功: {user_name} -> {thread_id} -> {new_count}")
            return True
                    
    except Exception as e:
        logger.error(f"更新线程消息数量失败: {e}")
        return False


async def get_thread_by_id(user_name: str, thread_id: str) -> Optional[Dict[str, Any]]:
    """根据ID获取特定线程"""
    try:
        async with get_async_db_context() as session:
            result = await session.execute(
                select(UserThread).where(
                    UserThread.user_name == user_name,
                    UserThread.thread_id == thread_id
                )
            )
            user_thread = result.scalar_one_or_none()
            
            if user_thread:
                return user_thread.to_dict()
            else:
                return None
                    
    except Exception as e:
        logger.error(f"获取线程详情失败: {e}")
        return None


async def create_or_get_user(user_name: str, display_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """创建或获取用户"""
    try:
        async with get_async_db_context() as session:
            # 先尝试获取用户
            result = await session.execute(
                select(User).where(User.user_name == user_name)
            )
            user = result.scalar_one_or_none()
            
            if user:
                return user.to_dict()
            
            # 如果用户不存在，创建新用户
            new_user = User(
                user_name=user_name,
                display_name=display_name or user_name,
                user_type='regular',
                is_active=True
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            logger.info(f"✅ 创建新用户成功: {user_name}")
            return new_user.to_dict()
                    
    except IntegrityError:
        # 可能是并发创建导致的重复，重新获取
        try:
            async with get_async_db_context() as session:
                result = await session.execute(
                    select(User).where(User.user_name == user_name)
                )
                user = result.scalar_one_or_none()
                return user.to_dict() if user else None
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    except Exception as e:
        logger.error(f"创建或获取用户失败: {e}")
        return None


# 保持向后兼容性的初始化和关闭函数
async def init_user_threads_db():
    """初始化用户线程数据库连接 - 保持兼容性"""
    logger.info("用户线程数据库使用统一的SQLAlchemy会话管理 - MySQL")


async def close_user_threads_db():
    """关闭数据库连接池 - 保持兼容性"""
    logger.info("用户线程数据库连接由SQLAlchemy统一管理，无需手动关闭")