"""Database configuration and setup."""
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 使用新的配置系统
from ..core.config import settings

# 数据库配置从统一配置获取
DATABASE_TYPE = settings.DATABASE_TYPE
DATABASE_HOST = settings.DATABASE_HOST
DATABASE_PORT = settings.DATABASE_PORT
DATABASE_NAME = settings.DATABASE_NAME
DATABASE_USER = settings.DATABASE_USER
DATABASE_PASSWORD = settings.DATABASE_PASSWORD

# Build database URL
if DATABASE_TYPE == "postgresql":
    SYNC_DATABASE_URL = f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
elif DATABASE_TYPE == "mysql":
    SYNC_DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    ASYNC_DATABASE_URL = f"mysql+aiomysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
else:
    raise ValueError(f"Unsupported database type: {DATABASE_TYPE}")

# Create engines with connection pooling and reconnection
if DATABASE_TYPE == "mysql":
    # MySQL特定的连接池配置
    sync_engine = create_engine(
        SYNC_DATABASE_URL, 
        echo=False,
        # 连接池配置
        pool_size=20,                   # 连接池大小
        max_overflow=30,                # 超出连接池大小的最大连接数
        pool_pre_ping=True,            # 连接前ping测试，自动重连
        pool_recycle=3600,             # 连接回收时间(1小时)
        # MySQL连接参数
        connect_args={
            "connect_timeout": 10,      # 连接超时10秒
            "read_timeout": 30,         # 读取超时30秒  
            "write_timeout": 30,        # 写入超时30秒
            "charset": "utf8mb4"
        }
    )
    
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        # 连接池配置
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        # MySQL异步连接参数
        connect_args={
            "connect_timeout": 10,
            "charset": "utf8mb4"
        }
    )
else:
    # PostgreSQL配置
    sync_engine = create_engine(
        SYNC_DATABASE_URL, 
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600
    )

# Create session makers
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

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
        async with get_async_db_context() as session:
            result = await session.execute(...)
    """
    return AsyncSessionLocal()


# ==================== 向后兼容性 ====================

async def get_async_session():
    """
    获取异步数据库会话 - 向后兼容
    @deprecated: 建议使用 get_async_db() 用于依赖注入，或 get_async_db_context() 用于上下文管理
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_async_session_context():
    """获取异步会话上下文管理器 - 用于手动管理"""
    return AsyncSessionLocal()


# ==================== 同步数据库会话 ====================

def get_sync_db():
    """获取同步数据库会话 - 统一接口，支持依赖注入和上下文管理"""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


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
        from sqlalchemy import text
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print(f"✅ Database connection successful ({DATABASE_TYPE})")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False