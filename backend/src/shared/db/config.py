"""Database configuration and setup."""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
logger = logging.getLogger(__name__)
# 使用新的配置系统
from src.shared.core.config import settings

# 数据库配置从统一配置获取
DATABASE_TYPE = settings.DATABASE_TYPE
DATABASE_HOST = settings.DATABASE_HOST
DATABASE_PORT = settings.DATABASE_PORT
DATABASE_NAME = settings.DATABASE_NAME
DATABASE_USER = settings.DATABASE_USER
DATABASE_PASSWORD = settings.DATABASE_PASSWORD

# Build database URL
def get_sync_database_url():
    if DATABASE_TYPE == "postgresql":
        return f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    elif DATABASE_TYPE == "mysql":
        return f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    else:
        raise ValueError(f"Unsupported database type: {DATABASE_TYPE}")

def get_async_database_url():
    if DATABASE_TYPE == "postgresql":
        return f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    elif DATABASE_TYPE == "mysql":
        return f"mysql+aiomysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    else:
        raise ValueError(f"Unsupported database type: {DATABASE_TYPE}")

# 全局变量，将在应用启动时初始化
async_engine = None
sync_engine = None
AsyncSessionLocal = None
SessionLocal = None

def create_sync_engine():
    """创建同步数据库引擎"""
    sync_database_url = get_sync_database_url()
    
    if DATABASE_TYPE == "mysql":
        # MySQL特定的连接池配置
        return create_engine(
            sync_database_url, 
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "connect_timeout": 10,
                "read_timeout": 30,
                "write_timeout": 30,
                "charset": "utf8mb4"
            }
        )
    else:
        # PostgreSQL配置
        return create_engine(
            sync_database_url, 
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )

def create_async_engine_instance():
    """创建异步数据库引擎"""
    async_database_url = get_async_database_url()
    
    if DATABASE_TYPE == "mysql":
        # MySQL异步连接池配置
        return create_async_engine(
            async_database_url,
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "connect_timeout": 10,
                "charset": "utf8mb4"
            }
        )
    else:
        # PostgreSQL配置
        return create_async_engine(
            async_database_url,
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )

async def init_db():
    """初始化数据库连接池 - 应该在每个worker的事件循环中调用"""
    global async_engine, sync_engine, AsyncSessionLocal, SessionLocal
    
    logger.info(f"初始化数据库连接池 (PID: {os.getpid()})")
    
    # 创建引擎
    sync_engine = create_sync_engine()
    async_engine = create_async_engine_instance()
    
    # 创建会话工厂
    AsyncSessionLocal = sessionmaker(
        async_engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=False
    )
    SessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=sync_engine
    )
    
    logger.info("数据库连接池初始化成功")

async def close_db():
    """关闭数据库连接池"""
    global async_engine, sync_engine
    
    if async_engine:
        await async_engine.dispose()
        logger.info("异步数据库连接池已关闭")
    
    if sync_engine:
        sync_engine.dispose()
        logger.info("同步数据库连接池已关闭")

# Create declarative base
Base = declarative_base()


# ==================== 异步数据库会话 ====================

async def get_async_db():
    """
    获取异步数据库会话 - 用于依赖注入
    
    Usage:
        async def api_endpoint(db: AsyncSession = Depends(get_async_db)):
            return await service.method(db, ...)
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("数据库未初始化，请确保应用正确启动")
        
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_async_db_context():
    """
    获取异步数据库会话上下文管理器 - 用于手动管理
    
    Usage:
        async with get_async_db_context() as db:
            result = await db.execute(...)
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("数据库未初始化，请确保应用正确启动")
        
    return AsyncSessionLocal()


# ==================== 向后兼容性 ====================

async def get_async_session():
    """
    获取异步数据库会话 - 向后兼容
    @deprecated: 建议使用 get_async_db() 用于依赖注入，或 get_async_db_context() 用于上下文管理
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("数据库未初始化，请确保应用正确启动")
        
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_async_session_context():
    """获取异步会话上下文管理器 - 用于手动管理"""
    if AsyncSessionLocal is None:
        raise RuntimeError("数据库未初始化，请确保应用正确启动")
        
    return AsyncSessionLocal()


# ==================== 同步数据库会话 ====================

def get_sync_db():
    """获取同步数据库会话 - 统一接口，支持依赖注入和上下文管理"""
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请确保应用正确启动")
        
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class SyncDBContext:
    """同步数据库会话上下文管理器 - 支持with语句"""
    
    def __init__(self):
        if SessionLocal is None:
            raise RuntimeError("数据库未初始化，请确保应用正确启动")
        self.session = None
    
    def __enter__(self):
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


# 统一接口：既可以用于依赖注入，也可以用于上下文管理
# 1. 依赖注入：db: Session = Depends(get_sync_db)  
# 2. 上下文管理：with get_sync_db() as db:


# ==================== 便捷函数 ====================

async def execute_async(func, *args, **kwargs):
    """在异步会话中执行函数"""
    async with AsyncSessionLocal() as session:
        try:
            kwargs['db'] = session
            result = await func(*args, **kwargs)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise


def execute_sync(func, *args, **kwargs):
    """在同步会话中执行函数"""
    session = SessionLocal()
    try:
        kwargs['db'] = session
        result = func(*args, **kwargs)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Legacy compatibility (deprecated, use get_sync_db instead)
def get_db():
    """@deprecated: Use get_sync_db() instead"""
    return get_sync_db()


async def init_database():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def test_database_connection():
    """Test database connection."""
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.exception(f"❌ Database connection failed: {e}")
        return False