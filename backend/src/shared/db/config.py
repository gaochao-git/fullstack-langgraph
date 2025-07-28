"""Database configuration and setup."""
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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


async def get_async_session():
    """Get async database session with reconnection handling."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with AsyncSessionLocal() as session:
                # 测试连接
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                yield session
                return
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise e
            await asyncio.sleep(0.5)  # 等待0.5秒后重试


def get_sync_session():
    """Get sync database session with reconnection handling."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        session = SessionLocal()
        try:
            # 测试连接
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            yield session
            return
        except Exception as e:
            session.close()
            retry_count += 1
            if retry_count >= max_retries:
                raise e
            import time
            time.sleep(0.5)  # 等待0.5秒后重试
        finally:
            session.close()


def get_db():
    """Get database session for FastAPI dependency injection with reconnection."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        db = SessionLocal()
        try:
            # 测试连接
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            yield db
            return
        except Exception as e:
            db.close()
            retry_count += 1
            if retry_count >= max_retries:
                raise e
            import time
            time.sleep(0.5)  # 等待0.5秒后重试
        finally:
            db.close()


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