"""
LLM智能体API路由端点
整合流式处理和线程管理功能
"""

from fastapi import APIRouter
from typing import Dict, Any, Optional
from pydantic import BaseModel

# 导入原有的功能
from .streaming import stream_run_standard, RunCreate
from .threads import create_thread, get_thread_history_post, ThreadCreate, ThreadResponse

router = APIRouter()

# 线程管理端点
@router.post("/llm/threads", response_model=ThreadResponse)
async def create_thread_endpoint(thread_create: ThreadCreate):
    """创建新的对话线程"""
    return await create_thread(thread_create)

@router.post("/llm/threads/{thread_id}/history")
async def get_thread_history_post_endpoint(thread_id: str, request_body: Optional[Dict[str, Any]] = None):
    """获取线程历史记录"""
    return await get_thread_history_post(thread_id, request_body)

@router.post("/llm/threads/{thread_id}/runs/stream")
async def stream_run_standard_endpoint(thread_id: str, request_body: RunCreate):
    """智能体流式对话处理"""
    return await stream_run_standard(thread_id, request_body)

# 用户线程管理
@router.get("/llm/users/{user_name}/threads")
async def get_user_threads_endpoint(user_name: str, limit: int = 10, offset: int = 0):
    """获取用户的所有线程"""
    from ..llm_service.user_threads_db import get_user_threads
    threads = await get_user_threads(user_name, limit, offset)
    return {"user_name": user_name, "threads": threads, "total": len(threads)}