"""
数据库事务管理模块
提供事务装饰器和上下文管理器
"""

import functools
from typing import Callable, Any, Optional, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.shared.db.config import get_async_db, get_sync_db
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 泛型类型变量
T = TypeVar('T')


class TransactionError(Exception):
    """事务相关异常"""
    pass


# ==================== 异步事务装饰器 ====================

def transactional(rollback_on: Optional[tuple] = None):
    """
    异步事务装饰器
    
    Args:
        rollback_on: 指定哪些异常需要回滚，默认为所有异常
    
    Usage:
        @transactional()
        async def complex_operation():
            # 多个数据库操作会在同一个事务中执行
            pass
            
        @transactional(rollback_on=(ValueError, TypeError))
        async def specific_rollback():
            # 只有 ValueError 和 TypeError 会触发回滚
            pass
    """
    if rollback_on is None:
        rollback_on = (Exception,)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 检查是否已经在事务中
            if 'session' in kwargs and isinstance(kwargs['session'], AsyncSession):
                # 如果已经传入session，直接执行函数
                return await func(*args, **kwargs)
            
            # 创建新的事务
            try:
                async with get_async_db() as session:
                    try:
                        # 将session注入到函数参数中
                        if 'session' not in kwargs:
                            kwargs['session'] = session
                        
                        result = await func(*args, **kwargs)
                        await session.commit()
                        
                        logger.debug(f"Transaction committed for {func.__name__}")
                        return result
                        
                    except rollback_on as e:
                        await session.rollback()
                        logger.warning(f"Transaction rolled back for {func.__name__}: {str(e)}")
                        raise TransactionError(f"Transaction failed in {func.__name__}: {str(e)}") from e
                    
                    except Exception as e:
                        await session.rollback()
                        logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                        raise
                        
            except SQLAlchemyError as e:
                logger.error(f"Database error in {func.__name__}: {str(e)}")
                raise TransactionError(f"Database operation failed: {str(e)}") from e
        
        return wrapper
    return decorator


def sync_transactional(rollback_on: Optional[tuple] = None):
    """
    同步事务装饰器（兼容现有代码）
    
    Args:
        rollback_on: 指定哪些异常需要回滚，默认为所有异常
    """
    if rollback_on is None:
        rollback_on = (Exception,)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 检查是否已经在事务中
            if 'session' in kwargs and isinstance(kwargs['session'], Session):
                # 如果已经传入session，直接执行函数
                return func(*args, **kwargs)
            
            # 创建新的事务
            try:
                with get_sync_db() as session:
                    try:
                        # 将session注入到函数参数中
                        if 'session' not in kwargs:
                            kwargs['session'] = session
                        
                        result = func(*args, **kwargs)
                        session.commit()
                        
                        logger.debug(f"Sync transaction committed for {func.__name__}")
                        return result
                        
                    except rollback_on as e:
                        session.rollback()
                        logger.warning(f"Sync transaction rolled back for {func.__name__}: {str(e)}")
                        raise TransactionError(f"Transaction failed in {func.__name__}: {str(e)}") from e
                    
                    except Exception as e:
                        session.rollback()
                        logger.error(f"Unexpected error in sync {func.__name__}: {str(e)}")
                        raise
                        
            except SQLAlchemyError as e:
                logger.error(f"Database error in sync {func.__name__}: {str(e)}")
                raise TransactionError(f"Database operation failed: {str(e)}") from e
        
        return wrapper
    return decorator


# ==================== 事务上下文管理器 ====================

class AsyncTransactionContext:
    """异步事务上下文管理器"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self._own_session = session is None
    
    async def __aenter__(self) -> AsyncSession:
        if self._own_session:
            async with get_async_db() as session:
                self.session = session
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                await self.session.rollback()
                logger.warning(f"Transaction rolled back due to: {exc_type.__name__}")
            else:
                await self.session.commit()
                logger.debug("Transaction committed successfully")
            
            if self._own_session:
                await self.session.close()


class SyncTransactionContext:
    """同步事务上下文管理器"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self._own_session = session is None
    
    def __enter__(self) -> Session:
        if self._own_session:
            self.session = get_sync_db().__enter__()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                self.session.rollback()
                logger.warning(f"Sync transaction rolled back due to: {exc_type.__name__}")
            else:
                self.session.commit()
                logger.debug("Sync transaction committed successfully")
            
            if self._own_session:
                self.session.close()


# ==================== 便捷函数 ====================

async def execute_in_transaction(func: Callable, *args, **kwargs) -> Any:
    """
    在事务中执行函数
    
    Usage:
        result = await execute_in_transaction(my_function, arg1, arg2, kwarg1=value1)
    """
    async with AsyncTransactionContext() as session:
        kwargs['session'] = session
        return await func(*args, **kwargs)


def sync_execute_in_transaction(func: Callable, *args, **kwargs) -> Any:
    """
    在同步事务中执行函数
    
    Usage:
        result = sync_execute_in_transaction(my_function, arg1, arg2, kwarg1=value1)
    """
    with SyncTransactionContext() as session:
        kwargs['session'] = session
        return func(*args, **kwargs)


# ==================== 批量操作事务支持 ====================

class BatchOperation:
    """批量操作支持"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.operations = []
    
    def add_operation(self, operation: Callable, *args, **kwargs):
        """添加操作到批次中"""
        self.operations.append((operation, args, kwargs))
    
    async def execute_all(self) -> list:
        """执行所有操作"""
        results = []
        try:
            for operation, args, kwargs in self.operations:
                kwargs['session'] = self.session
                result = await operation(*args, **kwargs)
                results.append(result)
            
            await self.session.commit()
            logger.info(f"Batch operation completed: {len(self.operations)} operations")
            return results
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Batch operation failed: {str(e)}")
            raise TransactionError(f"Batch operation failed: {str(e)}") from e


async def execute_batch(operations: list) -> list:
    """
    批量执行操作
    
    Args:
        operations: [(function, args, kwargs), ...]
    
    Returns:
        List of results
    """
    async with AsyncTransactionContext() as session:
        batch = BatchOperation(session)
        
        for operation, args, kwargs in operations:
            batch.add_operation(operation, *args, **kwargs)
        
        return await batch.execute_all()