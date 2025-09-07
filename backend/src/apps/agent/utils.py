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
logger = get_logger(__name__)

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