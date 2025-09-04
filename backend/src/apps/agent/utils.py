"""
API工具函数模块
"""
import os
import json
from typing import Dict, Any
from src.shared.core.logging import get_logger
from datetime import datetime
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from langgraph.types import Command
from .checkpoint_factory import create_checkpointer, test_checkpoint_connection, recover_thread_from_checkpoint as recover_thread_impl

logger = get_logger(__name__)

# 重新导出函数，保持接口兼容性
test_postgres_connection = test_checkpoint_connection
recover_thread_from_postgres = recover_thread_impl

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
        graph_input = Command(resume=request_body.command["resume"])
        logger.info(f"Resuming execution with command: {request_body.command}")
        # Clear interrupt information when resuming
        # if thread_id in thread_interrupts: # 不再写入内存变量
        #     thread_interrupts[thread_id] = []
    elif request_body.input is not None:
        graph_input = request_body.input
    else:
        raise BusinessException("Either 'input' or 'command' must be provided", ResponseCode.BAD_REQUEST)
    # Use stream modes from request, or default if not provided
    default_modes = ["values", "messages", "updates", "custom", "tasks"]
    stream_modes = request_body.stream_mode if request_body.stream_mode else default_modes
    
    return config, graph_input, stream_modes

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