"""
Checkpoint 工厂模块，支持多种 checkpoint 后端
"""
from typing import AsyncContextManager, Union
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.mysql.aio import AIOMySQLSaver
from src.shared.core.config import settings, get_checkpoint_uri
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def create_checkpointer() -> AsyncContextManager[Union[AsyncPostgresSaver, AIOMySQLSaver]]:
    """
    根据配置创建相应的 checkpointer
    
    Returns:
        AsyncContextManager: PostgreSQL 或 MySQL checkpointer
    """
    checkpointer_type = settings.CHECKPOINTER_TYPE.lower()
    uri = get_checkpoint_uri()
    
    logger.info(f"创建 {checkpointer_type} checkpointer...")
    
    if checkpointer_type == "postgres":
        async with AsyncPostgresSaver.from_conn_string(uri) as checkpointer:
            yield checkpointer
            
    elif checkpointer_type == "mysql":
        async with AIOMySQLSaver.from_conn_string(uri) as checkpointer:
            yield checkpointer
            
    else:
        raise ValueError(f"不支持的 CHECKPOINTER_TYPE: {checkpointer_type}")


async def test_checkpoint_connection():
    """测试 checkpoint 连接"""
    checkpointer_type = settings.CHECKPOINTER_TYPE.lower()
    
    try:
        async with create_checkpointer() as checkpointer:
            await checkpointer.setup()
            logger.info(f"✅ {checkpointer_type.upper()} checkpoint 连接测试成功")
    except Exception as e:
        logger.error(f"❌ {checkpointer_type.upper()} checkpoint 连接测试失败: {e}")
        raise e


async def recover_thread_from_checkpoint(thread_id: str):
    """从 checkpoint 中恢复线程信息"""
    try:
        async with create_checkpointer() as checkpointer:
            await checkpointer.setup()
            config = {"configurable": {"thread_id": thread_id}}
            history = [c async for c in checkpointer.alist(config, limit=1)]
            if history:
                checkpoint_tuple = history[0]
                thread_data = {
                    "thread_id": thread_id,
                    "created_at": checkpoint_tuple.metadata.get("created_at") if checkpoint_tuple.metadata else None,
                    "metadata": checkpoint_tuple.metadata or {},
                    "state": checkpoint_tuple.checkpoint.get("channel_values", {}) if checkpoint_tuple.checkpoint else {},
                }
                return thread_data
            else:
                return None
    except Exception as e:
        logger.error(f"恢复线程失败: {e}")
        return None