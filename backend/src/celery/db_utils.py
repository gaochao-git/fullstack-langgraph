"""
Celery数据库访问工具函数
"""
from contextlib import contextmanager
from src.shared.db.config import get_sync_db, SessionLocal
from src.celery.logger import get_logger

logger = get_logger(__name__)

@contextmanager
def get_db_session():
    """
    获取数据库会话的上下文管理器
    用于Celery任务中的数据库访问
    """
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请确保Celery正确启动")
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_celery_db():
    """
    初始化Celery的数据库连接
    应该在Celery worker启动时调用
    """
    from src.shared.db.config import init_db
    import asyncio
    
    try:
        # 在同步环境中运行异步初始化函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(init_db())
        loop.close()
        logger.info("Celery数据库连接初始化成功")
    except Exception as e:
        logger.error(f"Celery数据库连接初始化失败: {e}")
        raise