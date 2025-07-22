"""Database configuration and setup."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgresql")  # postgresql or mysql
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432" if DATABASE_TYPE == "postgresql" else "3306")
DATABASE_NAME = os.getenv("DATABASE_NAME", "langgraph_db")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres" if DATABASE_TYPE == "postgresql" else "root")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "password")

# Build database URL
if DATABASE_TYPE == "postgresql":
    SYNC_DATABASE_URL = f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
elif DATABASE_TYPE == "mysql":
    SYNC_DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    ASYNC_DATABASE_URL = f"mysql+aiomysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
else:
    raise ValueError(f"Unsupported database type: {DATABASE_TYPE}")

# Create engines
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

# Create session makers
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Create declarative base
Base = declarative_base()


async def get_async_session():
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Get sync database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


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