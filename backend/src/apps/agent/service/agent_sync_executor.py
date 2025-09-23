"""
智能体同步执行器
为Celery任务提供优化的同步执行方式，避免事件循环冲突
"""
import asyncio
import threading
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from .run_handler import RunCreate, execute_graph_request
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 全局线程池，用于运行异步任务
_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="agent_executor")

# 线程本地存储，每个线程维护自己的事件循环
_thread_local = threading.local()


def _get_event_loop():
    """获取或创建线程本地的事件循环"""
    try:
        loop = _thread_local.event_loop
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except (AttributeError, RuntimeError):
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _thread_local.event_loop = loop
    return loop


async def _execute_agent_async(
    agent_id: str,
    message: str,
    user_name: str,
    conversation_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    异步执行Agent
    
    Args:
        agent_id: 智能体ID
        message: 消息内容
        user_name: 用户名
        conversation_id: 对话ID（可选）
        config: 额外配置（可选）
        
    Returns:
        执行结果字典
    """
    try:
        # 构建请求体
        request_body = RunCreate(
            agent_id=agent_id,
            user_name=user_name,
            query=message,
            chat_mode="blocking",  # 非流式模式
            config=config or {}
        )
        
        # 使用对话ID作为thread_id，如果没有则生成一个
        thread_id = conversation_id or f"celery_task_{agent_id}_{user_name}"
        
        # 执行Agent（非流式模式）
        result = None
        async for response in execute_graph_request(
            request_body=request_body,
            thread_id=thread_id,
            request=None,  # Celery任务没有HTTP请求对象
            is_streaming=False
        ):
            result = response
            break
        
        if result:
            logger.info(f"Agent执行成功: agent_id={agent_id}, thread_id={thread_id}")
            return {
                "status": "SUCCESS",
                "data": result,
                "thread_id": thread_id
            }
        else:
            logger.error(f"Agent执行未返回结果: agent_id={agent_id}")
            return {
                "status": "FAILED",
                "error": "Agent执行未返回结果"
            }
            
    except Exception as e:
        logger.error(f"Agent执行异常: agent_id={agent_id}, error={str(e)}")
        return {
            "status": "ERROR",
            "error": str(e)
        }


def _run_in_thread(coro):
    """在线程中运行协程"""
    loop = _get_event_loop()
    return loop.run_until_complete(coro)


def execute_agent_sync(
    agent_id: str,
    message: str,
    user_name: str,
    conversation_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    同步执行智能体（优化版本）
    使用线程池避免在Celery worker中创建事件循环的问题
    
    Args:
        agent_id: 智能体ID
        message: 消息内容
        user_name: 用户名
        conversation_id: 对话ID（可选）
        config: 额外配置（可选）
        timeout: 超时时间（秒）
        
    Returns:
        执行结果字典
    """
    try:
        # 创建异步任务
        coro = _execute_agent_async(agent_id, message, user_name, conversation_id, config)
        
        # 提交到线程池执行
        future = _executor.submit(_run_in_thread, coro)
        
        # 等待结果，设置超时
        result = future.result(timeout=timeout)
        
        return result
        
    except FutureTimeoutError:
        logger.error(f"Agent执行超时: agent_id={agent_id}, timeout={timeout}s")
        return {
            "status": "TIMEOUT",
            "error": f"Agent执行超时（{timeout}秒）"
        }
    except Exception as e:
        logger.error(f"同步执行Agent失败: {str(e)}")
        return {
            "status": "ERROR",
            "error": str(e)
        }


def cleanup_executor():
    """清理执行器资源（应在程序退出时调用）"""
    _executor.shutdown(wait=True, cancel_futures=True)
    logger.info("Agent同步执行器已关闭")