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

# 存储引用 - 从app.py导入时设置
threads_store = None
thread_messages = None
thread_interrupts = None

def init_storage_refs(ts, tm, ti):
    """初始化存储引用"""
    global threads_store, thread_messages, thread_interrupts
    threads_store = ts
    thread_messages = tm
    thread_interrupts = ti

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
    threads_store[thread_id] = thread_data
    thread_messages[thread_id] = []  # Initialize empty message history
    thread_interrupts[thread_id] = []  # Initialize empty interrupt history
    logger.info(f"Created thread: {thread_id}")
    return ThreadResponse(**thread_data)

async def get_thread(thread_id: str):
    """Get thread details"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadResponse(**threads_store[thread_id])

async def get_thread_state(thread_id: str):
    """Get thread state"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    return threads_store[thread_id].get("state", {})

async def update_thread_state(thread_id: str, state: Dict[str, Any]):
    """Update thread state"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    threads_store[thread_id]["state"] = state
    return {"success": True}

async def get_thread_history(thread_id: str, limit: int = 10, before: Optional[str] = None):
    """Get all past states for a thread"""
    logger.info(f"请求history - thread_id: {thread_id}")
    logger.info(f"当前threads_store中的thread_ids: {list(threads_store.keys())}")
    
    if thread_id not in threads_store:
        logger.warning(f"Thread {thread_id} 未找到在threads_store中，尝试从PostgreSQL恢复")
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            logger.error(f"Thread {thread_id} 无法从PostgreSQL恢复")
            raise HTTPException(status_code=404, detail="Thread not found")
        logger.info(f"✅ 成功从PostgreSQL恢复线程: {thread_id}")
    
    thread_data = threads_store[thread_id]
    messages = thread_messages.get(thread_id, [])
    interrupts = thread_interrupts.get(thread_id, [])
    
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
            ] if interrupts else [],
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
    logger.info(f"当前threads_store中的thread_ids: {list(threads_store.keys())}")
    
    if thread_id not in threads_store:
        logger.warning(f"Thread {thread_id} 未找到在threads_store中，尝试从PostgreSQL恢复")
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            logger.error(f"Thread {thread_id} 无法从PostgreSQL恢复")
            raise HTTPException(status_code=404, detail="Thread not found")
        logger.info(f"✅ 成功从PostgreSQL恢复线程: {thread_id}")
    
    # Extract parameters from request body if provided
    limit = 10
    before = None
    if request_body:
        limit = request_body.get("limit", 10)
        before = request_body.get("before", None)
    
    thread_data = threads_store[thread_id]
    messages = thread_messages.get(thread_id, [])
    interrupts = thread_interrupts.get(thread_id, [])
    
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
            ] if interrupts else [],
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