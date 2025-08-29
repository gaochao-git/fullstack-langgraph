"""
线程管理相关接口
"""
import uuid
from datetime import datetime
from src.shared.core.logging import get_logger
from src.shared.db.models import now_shanghai
from typing import Dict, Any, Optional, List
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from pydantic import BaseModel

from ..utils import recover_thread_from_postgres

logger = get_logger(__name__)

# 删除所有threads_store、thread_messages、thread_interrupts相关全局变量和init_storage_refs相关内容

class ThreadCreate(BaseModel):
    assistant_id: str  # 使用 assistant_id，与 LangGraph SDK 保持一致
    user_name: str
    metadata: Optional[Dict[str, Any]] = None  # 保留用于其他扩展信息

class ThreadResponse(BaseModel):
    thread_id: str
    created_at: str
    metadata: Dict[str, Any]

async def create_thread(thread_create: ThreadCreate):
    """Create a new thread"""
    thread_id = str(uuid.uuid4())
    
    # 构建metadata，包含assistant_id和user_name
    metadata = thread_create.metadata or {}
    metadata.update({
        "assistant_id": thread_create.assistant_id,  # 保持与请求参数一致
        "user_name": thread_create.user_name,
        "created_at": now_shanghai().isoformat()
    })
    
    thread_data = {
        "thread_id": thread_id,
        "created_at": now_shanghai().isoformat(),
        "metadata": metadata,
        "state": {}
    }
    # 持久化到PostgreSQL
    # 这里需要一个PostgreSQL客户端来执行插入操作
    # 例如：await postgres_client.insert_thread(thread_id, thread_data)
    logger.info(f"Created thread: {thread_id} for agent: {thread_create.assistant_id}, user: {thread_create.user_name}")
    return ThreadResponse(**thread_data)

async def get_thread(thread_id: str):
    """Get thread details"""
    # 尝试从PostgreSQL获取线程
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        raise BusinessException("Thread not found", ResponseCode.NOT_FOUND)
    return ThreadResponse(**thread_data)

async def get_thread_state(thread_id: str):
    """Get thread state"""
    # 尝试从PostgreSQL获取线程
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        raise BusinessException("Thread not found", ResponseCode.NOT_FOUND)
    return thread_data.get("state", {})

async def update_thread_state(thread_id: str, state: Dict[str, Any]):
    """Update thread state"""
    # 尝试从PostgreSQL获取线程
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        raise BusinessException("Thread not found", ResponseCode.NOT_FOUND)
    thread_data["state"] = state
    # 持久化到PostgreSQL
    # 这里需要一个PostgreSQL客户端来执行更新操作
    # 例如：await postgres_client.update_thread_state(thread_id, state)
    return {"success": True}

async def get_thread_history(thread_id: str, limit: int = 10, before: Optional[str] = None):
    """Get all past states for a thread"""
    logger.info(f"请求history - thread_id: {thread_id}")
    # 尝试从PostgreSQL获取线程
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        raise BusinessException("Thread not found", ResponseCode.NOT_FOUND)
    
    # Return history with actual messages and interrupt information
    messages = thread_data.get("state", {}).get("messages", [])
    interrupts = thread_data.get("state", {}).get("interrupts", [])
    history = [
        {
            "checkpoint": {
                "thread_id": thread_id,
                "checkpoint_ns": "",
                "checkpoint_id": str(uuid.uuid4()),
                "checkpoint_map": {}
            },
            "metadata": {
                "step": 0,
                "writes": {},
                "parents": {}
            },
            "values": {
                "messages": messages,
                **thread_data.get("state", {})
            },
            "next": [],
            "tasks": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "current_task",
                    "interrupts": interrupts,
                    "error": None
                }
            ],
            "config": {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": ""
                }
            },
            "created_at": thread_data.get("created_at"),
            "parent_config": None
        }
    ]
    
    return history[:limit]

async def get_thread_history_post(thread_id: str, request_body: Optional[Dict[str, Any]] = None):
    """Get all past states for a thread (POST version)"""
    logger.info(f"请求history(POST) - thread_id: {thread_id}")
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        # 对于新创建的线程，返回空历史记录而不是抛出错误
        logger.info(f"Thread {thread_id} 尚未有对话历史，返回空历史")
        return []
    messages = thread_data.get("state", {}).get("messages", [])
    interrupts = thread_data.get("state", {}).get("interrupts", [])
    history = [
        {
            "checkpoint": {
                "thread_id": thread_id,
                "checkpoint_ns": "",
                "checkpoint_id": str(uuid.uuid4()),
                "checkpoint_map": {}
            },
            "metadata": {
                "step": 0,
                "writes": {},
                "parents": {}
            },
            "values": {
                "messages": messages
            },
            "next": [],
            "tasks": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "current_task",
                    "interrupts": interrupts,
                    "error": None
                }
            ],
            "config": {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": ""
                }
            },
            "created_at": thread_data.get("created_at"),
            "parent_config": None
        }
    ]
    return history