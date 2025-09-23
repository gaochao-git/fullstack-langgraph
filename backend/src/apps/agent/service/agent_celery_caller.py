"""
Agent 模块专用的 Celery 调用器
提供同步方式调用 Agent，供 Celery 任务使用
"""
import asyncio
from typing import Dict, Any, Optional
from .run_handler import RunCreate, execute_graph_request
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


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


def execute_agent_for_celery(
    agent_id: str,
    message: str,
    user_name: str,
    conversation_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    为 Celery 任务提供的同步执行 Agent 方法
    
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
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 在事件循环中运行异步函数，设置超时
        result = loop.run_until_complete(
            asyncio.wait_for(
                _execute_agent_async(agent_id, message, user_name, conversation_id, config),
                timeout=timeout
            )
        )
        
        return result
        
    except asyncio.TimeoutError:
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
    finally:
        # 清理事件循环
        try:
            loop.close()
        except:
            pass