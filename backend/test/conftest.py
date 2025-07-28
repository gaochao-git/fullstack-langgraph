"""
pytest全局配置和fixture
"""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.shared.db.config import get_async_session
from src.shared.db.models import Base


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db_session() -> AsyncMock:
    """创建模拟数据库会话"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话（使用内存SQLite）"""
    # 使用内存SQLite数据库进行测试
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # 清理
    await engine.dispose()


@pytest.fixture
def override_get_db(test_db_session):
    """覆盖get_async_session依赖"""
    async def _override_get_db():
        yield test_db_session
    
    return _override_get_db