"""
Checkpoint 单例模块
"""
from typing import Union, Optional
from contextlib import AsyncExitStack

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.mysql.aio import AIOMySQLSaver
from src.shared.core.config import settings
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 全局单例
_checkpointer: Union[AsyncPostgresSaver, AIOMySQLSaver, None] = None
_exit_stack: Optional[AsyncExitStack] = None
_initialized: bool = False  # 标记是否已初始化


def _get_checkpoint_uri() -> Optional[str]:
    """构建checkpoint连接URI
    
    Returns:
        连接URI字符串，如果配置不完整返回None
    """
    if not all([settings.CHECKPOINTER_HOST, settings.CHECKPOINTER_PORT, 
               settings.CHECKPOINTER_USER, settings.CHECKPOINTER_PASSWORD, 
               settings.CHECKPOINTER_DB]):
        logger.warning("Checkpoint配置不完整")
        return None
    
    if settings.CHECKPOINTER_TYPE.lower() == "mysql":
        return (f"mysql://{settings.CHECKPOINTER_USER}:{settings.CHECKPOINTER_PASSWORD}"
                f"@{settings.CHECKPOINTER_HOST}:{settings.CHECKPOINTER_PORT}/{settings.CHECKPOINTER_DB}")
    else:
        return (f"postgresql://{settings.CHECKPOINTER_USER}:{settings.CHECKPOINTER_PASSWORD}"
                f"@{settings.CHECKPOINTER_HOST}:{settings.CHECKPOINTER_PORT}/{settings.CHECKPOINTER_DB}")


async def get_checkpointer() -> Union[AsyncPostgresSaver, AIOMySQLSaver]:
    """获取 checkpointer 单例（懒加载）"""
    if not _initialized:
        await init()
    return _checkpointer


async def init():
    """初始化 checkpointer"""
    global _checkpointer, _exit_stack, _initialized
    
    if _initialized:
        return
    
    checkpointer_type = settings.CHECKPOINTER_TYPE.lower()
    uri = _get_checkpoint_uri()
    
    if not uri:
        raise ValueError("Checkpoint配置不完整，请检查环境变量")
    
    logger.info(f"初始化 {checkpointer_type} checkpointer...")
    
    # 创建 AsyncExitStack 保持连接
    _exit_stack = AsyncExitStack()
    
    try:
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
        _initialized = True  # 标记初始化成功
        logger.info(f"✅ {checkpointer_type} checkpointer 初始化成功")
        
    except Exception as e:
        # 初始化失败，清理资源
        await _exit_stack.aclose()
        _exit_stack = None
        _checkpointer = None
        raise


async def cleanup():
    """清理资源"""
    global _checkpointer, _exit_stack, _initialized
    
    if _exit_stack:
        await _exit_stack.aclose()
        _exit_stack = None
        _checkpointer = None
        _initialized = False  # 重置初始化标记
        logger.info("✅ Checkpointer 已清理")


async def recover_thread_from_checkpoint(thread_id: str) -> Optional[dict]:
    """从 checkpoint 恢复线程信息
    
    Args:
        thread_id: 线程ID
        
    Returns:
        线程信息字典，如果不存在返回None
        
    Raises:
        RuntimeError: 如果checkpointer未初始化
    """
    try:
        checkpointer = await get_checkpointer()  # 改为 await 调用
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
    except RuntimeError:
        # checkpointer未初始化，直接抛出
        raise
    except Exception as e:
        logger.error(f"恢复线程 {thread_id} 失败: {e}")
        return None


# 导出 _initialized 供外部使用（如 main.py）
def is_initialized() -> bool:
    """检查 checkpointer 是否已初始化"""
    return _initialized