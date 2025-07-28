"""
API工具函数模块
"""
import os
import json
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import HTTPException
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)

# 全局连接字符串配置 - 从环境变量读取
from ..shared.core.config import get_checkpoint_uri
CHECK_POINT_URI = get_checkpoint_uri()

# 删除所有threads_store、thread_messages、thread_interrupts相关全局变量和init_storage_refs相关内容

async def test_postgres_connection():
    """启动时测试PostgreSQL连接"""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    try:
        async with AsyncPostgresSaver.from_conn_string(CHECK_POINT_URI) as checkpointer:
            await checkpointer.setup()
            logger.info("✅ PostgreSQL连接测试成功")
    except Exception as e:
        logger.error(f"❌ PostgreSQL连接测试失败: {e}")
        raise e

async def recover_thread_from_postgres(thread_id: str):
    """从PostgreSQL checkpointer中恢复线程信息，查到返回dict，查不到返回None"""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    try:
        async with AsyncPostgresSaver.from_conn_string(CHECK_POINT_URI) as checkpointer:
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

def prepare_graph_config(request_body, thread_id):
    """准备图执行配置"""
    config = {
        "configurable": {
            "thread_id": thread_id,
            **(request_body.config or {}).get("configurable", {})
        },
        "recursion_limit": (request_body.config or {}).get("recursion_limit", 100)
    }
    
    # Handle resume command for interrupted execution
    if request_body.command and "resume" in request_body.command:
        from langgraph.types import Command
        graph_input = Command(resume=request_body.command["resume"])
        logger.info(f"Resuming execution with command: {request_body.command}")
        # Clear interrupt information when resuming
        # if thread_id in thread_interrupts: # 不再写入内存变量
        #     thread_interrupts[thread_id] = []
    elif request_body.input is not None:
        graph_input = request_body.input
    else:
        raise HTTPException(status_code=400, detail="Either 'input' or 'command' must be provided")
    
    # Use checkpoint from request if provided  
    checkpoint = request_body.checkpoint
    if checkpoint and "thread_id" in checkpoint:
        del checkpoint["thread_id"]
    
    # Combine stream modes
    stream_modes = list(set([
        "values", "messages", "updates", "custom", "checkpoints", "tasks"
    ] + (request_body.stream_mode or [])))
    
    return config, graph_input, stream_modes, checkpoint

def serialize_value(val):
    """通用序列化函数"""
    # Handle tuples (like from LangGraph messages)
    if isinstance(val, tuple):
        return [serialize_value(item) for item in val]
    # Handle LangGraph Interrupt objects
    elif hasattr(val, 'value') and hasattr(val, 'resumable') and hasattr(val, 'ns'):
        return {
            "value": serialize_value(val.value),
            "resumable": val.resumable,
            "ns": val.ns,
            "when": getattr(val, 'when', 'during')
        }
    elif hasattr(val, 'dict'):
        return val.dict()
    elif hasattr(val, 'to_dict'):
        return val.to_dict()
    elif hasattr(val, '__dict__'):
        result = {}
        for k, v in val.__dict__.items():
            if not k.startswith('_'):
                result[k] = serialize_value(v)
        return result
    elif isinstance(val, list):
        return [serialize_value(item) for item in val]
    elif isinstance(val, dict):
        return {k: serialize_value(v) for k, v in val.items()}
    else:
        try:
            json.dumps(val)
            return val
        except (TypeError, ValueError):
            return str(val)