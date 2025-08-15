"""
CAS会话清理任务
定期清理过期的CAS会话
"""

import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db_context
from src.apps.auth.models import AuthSession
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


async def cleanup_expired_sessions():
    """
    清理过期的CAS会话
    应该定期执行（如每小时）
    """
    async with get_async_db_context() as db:
        try:
            # 查找所有过期但仍标记为活跃的会话
            stmt = select(AuthSession).where(
                AuthSession.is_active == True,
                AuthSession.expires_at < datetime.now(timezone.utc)
            )
            result = await db.execute(stmt)
            expired_sessions = result.scalars().all()
            
            if not expired_sessions:
                logger.info("没有过期的会话需要清理")
                return
            
            # 批量更新过期会话
            for session in expired_sessions:
                session.is_active = False
                session.terminated_at = datetime.now(timezone.utc)
                session.termination_reason = "会话过期"
            
            await db.commit()
            
            logger.info(f"成功清理了 {len(expired_sessions)} 个过期会话")
            
            # 返回清理的会话信息
            return {
                "cleaned_count": len(expired_sessions),
                "session_ids": [s.session_id for s in expired_sessions]
            }
            
        except Exception as e:
            logger.error(f"清理过期会话时发生错误: {e}")
            raise


async def cleanup_old_inactive_sessions(days_to_keep: int = 30):
    """
    清理长时间不活跃的会话记录
    
    Args:
        days_to_keep: 保留最近N天的非活跃会话记录
    """
    async with get_async_db_context() as db:
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            # 查找需要删除的旧会话
            stmt = select(AuthSession).where(
                AuthSession.is_active == False,
                AuthSession.terminated_at < cutoff_date
            )
            result = await db.execute(stmt)
            old_sessions = result.scalars().all()
            
            if not old_sessions:
                logger.info("没有需要删除的旧会话记录")
                return
            
            # 批量删除
            for session in old_sessions:
                await db.delete(session)
            
            await db.commit()
            
            logger.info(f"成功删除了 {len(old_sessions)} 条旧会话记录")
            
            return {
                "deleted_count": len(old_sessions)
            }
            
        except Exception as e:
            logger.error(f"删除旧会话记录时发生错误: {e}")
            raise


async def get_session_statistics():
    """
    获取会话统计信息
    """
    async with get_async_db_context() as db:
        try:
            # 统计活跃会话
            active_stmt = select(AuthSession).where(
                AuthSession.is_active == True
            )
            active_result = await db.execute(active_stmt)
            active_count = len(active_result.scalars().all())
            
            # 统计今日创建的会话
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            today_stmt = select(AuthSession).where(
                AuthSession.created_at >= today_start
            )
            today_result = await db.execute(today_stmt)
            today_count = len(today_result.scalars().all())
            
            # 统计不同终止原因
            terminated_stmt = select(
                AuthSession.termination_reason,
                AuthSession
            ).where(
                AuthSession.is_active == False,
                AuthSession.termination_reason.isnot(None)
            )
            terminated_result = await db.execute(terminated_stmt)
            
            termination_stats = {}
            for reason, session in terminated_result:
                if reason not in termination_stats:
                    termination_stats[reason] = 0
                termination_stats[reason] += 1
            
            return {
                "active_sessions": active_count,
                "today_created": today_count,
                "termination_reasons": termination_stats
            }
            
        except Exception as e:
            logger.error(f"获取会话统计信息时发生错误: {e}")
            raise


# 如果作为独立脚本运行
if __name__ == "__main__":
    async def main():
        print("开始执行会话清理任务...")
        
        # 清理过期会话
        result1 = await cleanup_expired_sessions()
        print(f"清理过期会话: {result1}")
        
        # 清理旧记录
        result2 = await cleanup_old_inactive_sessions()
        print(f"清理旧记录: {result2}")
        
        # 获取统计信息
        stats = await get_session_statistics()
        print(f"会话统计: {stats}")
    
    asyncio.run(main())