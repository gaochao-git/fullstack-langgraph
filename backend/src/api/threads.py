"""
线程管理相关接口
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from pydantic import BaseModel

from .utils import recover_thread_from_postgres

logger = logging.getLogger(__name__)

# 删除所有threads_store、thread_messages、thread_interrupts相关全局变量和init_storage_refs相关内容

class ThreadCreate(BaseModel):
    metadata: Optional[Dict[str, Any]] = None

class ThreadResponse(BaseModel):
    thread_id: str
    created_at: str
    metadata: Dict[str, Any]

async def create_thread(thread_create: ThreadCreate):
    """Create a new thread"""
    thread_id = str(uuid.uuid4())
    thread_data = {
        "thread_id": thread_id,
        "created_at": datetime.now().isoformat(),
        "metadata": thread_create.metadata or {},
        "state": {}
    }
    # 持久化到PostgreSQL
    # 这里需要一个PostgreSQL客户端来执行插入操作
    # 例如：await postgres_client.insert_thread(thread_id, thread_data)
    logger.info(f"Created thread: {thread_id}")
    return ThreadResponse(**thread_data)

async def get_thread(thread_id: str):
    """Get thread details"""
    # 尝试从PostgreSQL获取线程
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadResponse(**thread_data)

async def get_thread_state(thread_id: str):
    """Get thread state"""
    # 尝试从PostgreSQL获取线程
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread_data.get("state", {})

async def update_thread_state(thread_id: str, state: Dict[str, Any]):
    """Update thread state"""
    # 尝试从PostgreSQL获取线程
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        raise HTTPException(status_code=404, detail="Thread not found")
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
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Return history with actual messages and interrupt information
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
                "messages": [], # 历史消息需要从PostgreSQL获取
                **thread_data.get("state", {})
            },
            "next": [],
            "tasks": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "current_task",
                    "interrupts": [], # 历史中断需要从PostgreSQL获取
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
    # 尝试从PostgreSQL获取线程
    thread_data = await recover_thread_from_postgres(thread_id)
    if not thread_data:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Extract parameters from request body if provided
    limit = 10
    before = None
    if request_body:
        limit = request_body.get("limit", 10)
        before = request_body.get("before", None)
    
    # Return history with actual messages and interrupt information
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
                "messages": [], # 历史消息需要从PostgreSQL获取
                **thread_data.get("state", {})
            },
            "next": [],
            "tasks": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "current_task",
                    "interrupts": [], # 历史中断需要从PostgreSQL获取
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