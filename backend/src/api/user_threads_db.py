"""
用户线程数据库操作模块
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# 导入与LangGraph相同的连接配置
from .utils import POSTGRES_CONNECTION_STRING

# 全局数据库连接池
db_pool = None

async def init_user_threads_db():
    """初始化用户线程数据库连接"""
    global db_pool
    
    try:
        import asyncpg
        # 使用与LangGraph相同的连接字符串
        db_pool = await asyncpg.create_pool(POSTGRES_CONNECTION_STRING)
        logger.info("用户线程数据库连接池初始化成功 - PostgreSQL")
        
    except ImportError:
        logger.error("缺少asyncpg依赖，请安装: pip install asyncpg")
        db_pool = None
    except Exception as e:
        logger.error(f"用户线程数据库连接失败: {e}")
        # 不抛出异常，允许应用继续运行（降级到内存模式）
        db_pool = None

async def check_user_thread_exists(user_name: str, thread_id: str) -> bool:
    """检查用户线程关联是否存在"""
    if not db_pool:
        return False
        
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM user_threads WHERE user_name = $1 AND thread_id = $2",
                user_name, thread_id
            )
            return result > 0
                    
    except Exception as e:
        logger.error(f"检查用户线程关联失败: {e}")
        return False

async def create_user_thread_mapping(
    user_name: str, 
    thread_id: str, 
    thread_title: Optional[str] = None
) -> bool:
    """创建用户线程关联"""
    logger.info(f"📝 create_user_thread_mapping 被调用: user={user_name}, thread={thread_id}, title={thread_title}")
    if not db_pool:
        logger.warning("❌ 数据库连接池未初始化，跳过用户线程关联创建")
        return False
        
    try:
        # 如果没有标题，使用时间戳生成默认标题
        if not thread_title:
            thread_title = f"对话 {datetime.now().strftime('%m-%d %H:%M')}"
            logger.info(f"🏷️ 使用默认标题: {thread_title}")
        
        logger.info(f"🔗 准备执行数据库插入操作...")
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                """
                INSERT INTO user_threads (user_name, thread_id, thread_title, create_at, update_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (user_name, thread_id) DO NOTHING
                """,
                user_name, thread_id, thread_title
            )
            logger.info(f"🗄️ 数据库执行结果: {result}")
                    
        logger.info(f"✅ 创建用户线程关联成功: {user_name} -> {thread_id}")
        return True
        
    except Exception as e:
        logger.error(f"创建用户线程关联失败: {e}")
        return False

async def get_user_threads(
    user_name: str, 
    limit: int = 10, 
    offset: int = 0
) -> List[Dict[str, Any]]:
    """获取用户的所有线程"""
    if not db_pool:
        return []
        
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT thread_id, thread_title, create_at, update_at
                FROM user_threads 
                WHERE user_name = $1 
                ORDER BY create_at DESC 
                LIMIT $2 OFFSET $3
                """,
                user_name, limit, offset
            )
            return [dict(row) for row in rows]
                    
    except Exception as e:
        logger.error(f"获取用户线程列表失败: {e}")
        return []

async def update_thread_title(
    user_name: str, 
    thread_id: str, 
    new_title: str
) -> bool:
    """更新线程标题"""
    if not db_pool:
        return False
        
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE user_threads 
                SET thread_title = $1, update_at = CURRENT_TIMESTAMP
                WHERE user_name = $2 AND thread_id = $3
                """,
                new_title, user_name, thread_id
            )
            return result == "UPDATE 1"
                    
    except Exception as e:
        logger.error(f"更新线程标题失败: {e}")
        return False

async def close_user_threads_db():
    """关闭数据库连接池"""
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None
        logger.info("用户线程数据库连接池已关闭")