"""
Checkpoint 单例模块
"""
from typing import Union
from contextlib import AsyncExitStack

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.mysql.aio import AIOMySQLSaver
from src.shared.core.config import settings, get_checkpoint_uri
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 全局单例
_checkpointer: Union[AsyncPostgresSaver, AIOMySQLSaver, None] = None
_exit_stack: AsyncExitStack = None


def get_checkpointer() -> Union[AsyncPostgresSaver, AIOMySQLSaver]:
    """获取 checkpointer 单例"""
    if _checkpointer is None:
        raise RuntimeError("Checkpointer 未初始化")
    return _checkpointer


async def init():
    """初始化 checkpointer"""
    global _checkpointer, _exit_stack
    
    if _checkpointer is not None:
        return
    
    checkpointer_type = settings.CHECKPOINTER_TYPE.lower()
    uri = get_checkpoint_uri()
    
    logger.info(f"初始化 {checkpointer_type} checkpointer...")
    
    # 创建 AsyncExitStack 保持连接
    _exit_stack = AsyncExitStack()
    
    if checkpointer_type == "postgres":
        _checkpointer = await _exit_stack.enter_async_context(
            AsyncPostgresSaver.from_conn_string(uri)
        )
    elif checkpointer_type == "mysql":
        _checkpointer = await _exit_stack.enter_async_context(
            AIOMySQLSaver.from_conn_string(uri)
        )
    else:
        raise ValueError(f"不支持的类型: {checkpointer_type}")
    
    await _checkpointer.setup()
    logger.info(f"✅ {checkpointer_type} checkpointer 初始化成功")


async def cleanup():
    """清理资源"""
    global _checkpointer, _exit_stack
    
    if _exit_stack:
        await _exit_stack.aclose()
        _exit_stack = None
        _checkpointer = None
        logger.info("✅ Checkpointer 已清理")


async def recover_thread_from_checkpoint(thread_id: str):
    """从 checkpoint 恢复线程信息"""
    try:
        checkpointer = get_checkpointer()
        config = {"configurable": {"thread_id": thread_id}}
        history = [c async for c in checkpointer.alist(config, limit=1)]
        
        if history:
            checkpoint_tuple = history[0]
            return {
                "thread_id": thread_id,
                "created_at": checkpoint_tuple.metadata.get("created_at") if checkpoint_tuple.metadata else None,
                "metadata": checkpoint_tuple.metadata or {},
                "state": checkpoint_tuple.checkpoint.get("channel_values", {}) if checkpoint_tuple.checkpoint else {},
            }
        return None
    except Exception as e:
        logger.error(f"恢复线程失败: {e}")
        return None