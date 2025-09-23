"""
Celery数据库访问工具函数
Celery Worker 独立维护自己的数据库连接池
"""
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.shared.core.config import settings
from src.celery.logger import get_logger

logger = get_logger(__name__)

# Celery专用的数据库引擎和会话工厂
_celery_engine = None
_celery_session_factory = None

def get_celery_db_url():
    """获取Celery使用的数据库URL"""
    # 只使用 MySQL
    return f"mysql+pymysql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}?charset=utf8mb4"

def init_celery_db():
    """
    初始化Celery的数据库连接
    应该在Celery worker启动时调用
    """
    global _celery_engine, _celery_session_factory
    
    try:
        # 创建数据库引擎
        db_url = get_celery_db_url()
        _celery_engine = create_engine(
            db_url,
            pool_pre_ping=True,  # 连接前检查
            pool_size=5,         # 连接池大小
            max_overflow=10,     # 最大溢出连接数
            pool_recycle=3600    # 连接回收时间（秒）
        )
        
        # 创建会话工厂
        _celery_session_factory = sessionmaker(
            bind=_celery_engine,
            autocommit=False,
            autoflush=False
        )
        
        # 测试连接
        with _celery_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("Celery数据库连接初始化成功")
    except Exception as e:
        logger.error(f"Celery数据库连接初始化失败: {e}")
        raise

@contextmanager
def get_db_session():
    """
    获取数据库会话的上下文管理器
    用于Celery任务中的数据库访问
    """
    if _celery_session_factory is None:
        # 如果还没初始化，立即初始化
        init_celery_db()
    
    session = _celery_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def close_celery_db():
    """关闭Celery的数据库连接池"""
    global _celery_engine, _celery_session_factory
    
    if _celery_engine:
        _celery_engine.dispose()
        _celery_engine = None
        _celery_session_factory = None
        logger.info("Celery数据库连接池已关闭")