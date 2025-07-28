"""
数据库会话使用示例
展示在不同层如何正确使用异步和同步会话
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi import Depends

from .config import get_async_db, get_async_db_context, get_sync_db, execute_async, execute_sync
from .models import SOPTemplate


# ==================== API层使用方式 ====================

async def api_endpoint_with_dependency(db: AsyncSession = Depends(get_async_db)):
    """API端点：使用依赖注入的异步会话"""
    # 直接使用注入的异步会话
    result = await db.execute(select(SOPTemplate))
    return result.scalars().all()


async def api_endpoint_manual():
    """API端点：手动管理异步会话"""
    async with get_async_db() as db:
        result = await db.execute(select(SOPTemplate))  
        return result.scalars().all()


# ==================== 服务层使用方式 ====================

async def service_method_with_session(db: AsyncSession, sop_id: str):
    """服务方法：接收外部传入的会话"""
    result = await db.execute(select(SOPTemplate).where(SOPTemplate.sop_id == sop_id))
    return result.scalar_one_or_none()


async def service_method_self_managed(sop_id: str):
    """服务方法：自管理异步会话"""
    async with get_async_db() as db:
        result = await db.execute(select(SOPTemplate).where(SOPTemplate.sop_id == sop_id))
        return result.scalar_one_or_none()


async def service_method_using_helper(sop_id: str):
    """服务方法：使用便捷函数"""
    async def _query(db: AsyncSession):
        result = await db.execute(select(SOPTemplate).where(SOPTemplate.sop_id == sop_id))
        return result.scalar_one_or_none()
    
    return await execute_async(_query)


# ==================== 工具层使用方式 ====================

def tool_method_context_manager(sop_id: str):
    """工具方法：使用上下文管理器（推荐）"""
    with get_sync_db() as db:
        result = db.query(SOPTemplate).filter(SOPTemplate.sop_id == sop_id).first()
        return result.to_dict() if result else None


def tool_method_using_helper(sop_id: str):
    """工具方法：使用便捷函数"""
    def _query(db: Session):
        result = db.query(SOPTemplate).filter(SOPTemplate.sop_id == sop_id).first()
        return result.to_dict() if result else None
    
    return execute_sync(_query)


# ==================== DAO层使用方式 ====================

class SOPSyncDAO:
    """同步DAO - 用于工具层"""
    
    def get_by_id(self, db: Session, sop_id: str):
        return db.query(SOPTemplate).filter(SOPTemplate.sop_id == sop_id).first()
    
    def list_all(self, db: Session, limit: int = 100):
        return db.query(SOPTemplate).limit(limit).all()


class SOPAsyncDAO:
    """异步DAO - 用于服务层"""
    
    async def get_by_id(self, db: AsyncSession, sop_id: str):
        result = await db.execute(select(SOPTemplate).where(SOPTemplate.sop_id == sop_id))
        return result.scalar_one_or_none()
    
    async def list_all(self, db: AsyncSession, limit: int = 100):
        result = await db.execute(select(SOPTemplate).limit(limit))
        return result.scalars().all()


# ==================== 使用建议 ====================

"""
层级使用建议：

1. API层（FastAPI路由）:
   - 优先使用：Depends(get_async_db) 依赖注入
   - 备选：async with get_async_db() as db:

2. 服务层（业务逻辑）:
   - 优先接收外部session：async def method(db: AsyncSession, ...)
   - 备选：async with get_async_db() as db:
   - 便捷：await execute_async(func)

3. 工具层（LangGraph工具）:
   - 优先使用：with get_sync_db() as db:
   - 备选：execute_sync(func)

4. DAO层：
   - 同步DAO：def method(self, db: Session, ...)
   - 异步DAO：async def method(self, db: AsyncSession, ...)

性能提示：
- 异步会话：用于高并发API处理
- 同步会话：用于简单工具操作，避免事件循环复杂性
- 两套会话独立管理，各司其职
"""