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
POSTGRES_CONNECTION_STRING = os.getenv("POSTGRES_CHECKPOINT_URI")

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

async def test_postgres_connection():
    """启动时测试PostgreSQL连接"""
    checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
    if checkpointer_type == "postgres":
        try:
            async with AsyncPostgresSaver.from_conn_string(POSTGRES_CONNECTION_STRING) as checkpointer:
                await checkpointer.setup()
                logger.info("✅ PostgreSQL连接测试成功")
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接测试失败: {e}")
            raise e

async def recover_thread_from_postgres(thread_id: str) -> bool:
    """从PostgreSQL checkpointer中恢复线程信息"""
    try:
        checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
        if checkpointer_type != "postgres":
            return False
            
        # 每次创建新的checkpointer连接来恢复线程
        async with AsyncPostgresSaver.from_conn_string(POSTGRES_CONNECTION_STRING) as checkpointer:
            await checkpointer.setup()
            
            config = {"configurable": {"thread_id": thread_id}}
            # 获取最新的checkpoint来验证thread存在
            history = [c async for c in checkpointer.alist(config, limit=1)]
            
            if history:
                logger.info(f"✅ 从PostgreSQL恢复线程: {thread_id}")
                checkpoint_tuple = history[0]
                
                # 重建threads_store条目 - 使用正确的属性访问
                threads_store[thread_id] = {
                    "thread_id": thread_id,
                    "created_at": checkpoint_tuple.metadata.get("created_at", datetime.now().isoformat()) if checkpoint_tuple.metadata else datetime.now().isoformat(),
                    "metadata": {},
                    "state": {},
                    "recovered_from_postgres": True
                }
                
                # 初始化相关存储
                if thread_id not in thread_messages:
                    thread_messages[thread_id] = []
                if thread_id not in thread_interrupts:
                    thread_interrupts[thread_id] = []
                
                # 从checkpoint恢复消息 - 使用官方结构
                try:
                    if checkpoint_tuple.checkpoint and "channel_values" in checkpoint_tuple.checkpoint:
                        channel_values = checkpoint_tuple.checkpoint["channel_values"]
                        if "messages" in channel_values:
                            thread_messages[thread_id] = channel_values["messages"]
                            logger.info(f"恢复了 {len(thread_messages[thread_id])} 条消息")
                        
                        # 也尝试恢复其他状态
                        if "diagnosis_progress" in channel_values:
                            threads_store[thread_id]["state"]["diagnosis_progress"] = channel_values["diagnosis_progress"]
                        logger.info(f"从checkpoint恢复的通道: {list(channel_values.keys())}")
                    else:
                        logger.info(f"Checkpoint结构: {list(checkpoint_tuple.checkpoint.keys()) if checkpoint_tuple.checkpoint else 'None'}")
                except Exception as e:
                    logger.warning(f"恢复状态时出错，但线程恢复成功: {e}")
                
                return True
            else:
                logger.info(f"❌ PostgreSQL中未找到线程: {thread_id}")
                return False
                
    except Exception as e:
        logger.error(f"恢复线程失败: {e}")
        return False

def should_use_postgres_mode(assistant_id: str) -> bool:
    """判断是否应该使用PostgreSQL模式"""
    checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
    return assistant_id == "diagnostic_agent" and checkpointer_type == "postgres"

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
        if thread_id in thread_interrupts:
            thread_interrupts[thread_id] = []
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