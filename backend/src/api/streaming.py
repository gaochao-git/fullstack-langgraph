"""
流式处理相关接口和函数
"""
import json
import logging
from typing import Dict, Any, List
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from .utils import (
    should_use_postgres_mode, 
    prepare_graph_config, 
    serialize_value,
    POSTGRES_CONNECTION_STRING,
    recover_thread_from_postgres
)
from .user_threads_db import (
    check_user_thread_exists,
    create_user_thread_mapping,
    init_user_threads_db
)

logger = logging.getLogger(__name__)

# 存储引用 - 从app.py导入时设置
threads_store = None
thread_messages = None
thread_interrupts = None
ASSISTANTS = None

def init_refs(ts, tm, ti, assistants):
    """初始化引用"""
    global threads_store, thread_messages, thread_interrupts, ASSISTANTS
    threads_store = ts
    thread_messages = tm
    thread_interrupts = ti
    ASSISTANTS = assistants

class RunCreate(BaseModel):
    assistant_id: str
    input: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    stream_mode: Optional[List[str]] = ["values"]
    interrupt_before: Optional[List[str]] = None
    interrupt_after: Optional[List[str]] = None
    on_disconnect: Optional[str] = None
    command: Optional[Dict[str, Any]] = None
    checkpoint: Optional[Dict[str, Any]] = None
    user_name: Optional[str] = None  # 用户名，用于线程关联

async def process_stream_chunk(chunk, event_id, thread_id):
    """处理单个流式数据块"""    
    # Handle tuple format from LangGraph streaming
    if isinstance(chunk, tuple) and len(chunk) >= 2:
        if len(chunk) == 2:
            # 标准格式: (event_type, data)
            event_type, data = chunk
        elif len(chunk) == 3:
            # 子图格式: (namespace, event_type, data)
            namespace, event_type, data = chunk
        else:
            # 未知格式，尝试获取最后两个元素
            event_type, data = chunk[-2:]
            logger.warning(f"⚠️ 未知的chunk格式，长度={len(chunk)}, 尝试使用后两个元素")
        
        serialized_data = serialize_value(data)
        
        # Save messages to thread history from LangGraph state
        if event_type == "values" and isinstance(data, dict) and "messages" in data:
            if thread_messages is not None:
                if thread_id not in thread_messages:
                    thread_messages[thread_id] = []
                thread_messages[thread_id] = [serialize_value(msg) for msg in data["messages"]]
                logger.info(f"💾 保存了 {len(data['messages'])} 条消息到线程 {thread_id}")
        
        # Also save messages from updates events (when nodes return message updates)
        elif event_type == "updates" and isinstance(data, dict):
            for node_name, node_data in data.items():
                if isinstance(node_data, dict) and "messages" in node_data:
                    if thread_messages is not None:
                        if thread_id not in thread_messages:
                            thread_messages[thread_id] = []
                        # Append new messages instead of replacing
                        new_messages = [serialize_value(msg) for msg in node_data["messages"]]
                        thread_messages[thread_id].extend(new_messages)
                        logger.info(f"💾 从节点 {node_name} 追加了 {len(new_messages)} 条消息到线程 {thread_id}")
                    break  # Only process the first node with messages
        
        # Check for interrupts
        has_interrupt = False
        if event_type == "updates" and isinstance(data, dict) and "__interrupt__" in data:
            logger.info(f"Interrupt detected: {data}")
            if thread_interrupts is not None:
                if thread_id not in thread_interrupts:
                    thread_interrupts[thread_id] = []
                thread_interrupts[thread_id].append(data["__interrupt__"][0])
            has_interrupt = True
        
        return f"id: {event_id}\nevent: {event_type}\ndata: {json.dumps(serialized_data, ensure_ascii=False)}\n\n", has_interrupt
    else:
        # Handle dict format (fallback)
        serializable_chunk = {}
        for key, value in chunk.items():
            serializable_chunk[key] = serialize_value(value)
        
        event_type = list(serializable_chunk.keys())[0] if serializable_chunk else "data"
        return f"id: {event_id}\nevent: {event_type}\ndata: {json.dumps(serializable_chunk[event_type], ensure_ascii=False)}\n\n", False

async def stream_with_graph_postgres(graph, request_body, thread_id):
    """PostgreSQL模式专用的图流媒体处理函数"""
    config, graph_input, stream_modes, checkpoint = prepare_graph_config(request_body, thread_id)
    logger.info(f"Starting stream with modes: {stream_modes}, checkpoint: {checkpoint}")
    
    event_id = 0
    has_interrupt = False
    
    async for chunk in graph.astream(graph_input, config=config, stream_mode=stream_modes, subgraphs=True):
        try:
            event_id += 1
            sse_data, chunk_has_interrupt = await process_stream_chunk(chunk, event_id, thread_id)
            yield sse_data
            if chunk_has_interrupt:
                has_interrupt = True
        except Exception as e:
            logger.error(f"Serialization error: {e}, chunk type: {type(chunk)}, chunk: {chunk}")
            event_id += 1
            yield f"id: {event_id}\nevent: error\ndata: {json.dumps({'error': str(e), 'chunk_type': str(type(chunk)), 'chunk': str(chunk)}, ensure_ascii=False)}\n\n"
    
    # End event - only send if no interrupt occurred
    if not has_interrupt:
        event_id += 1
        yield f"id: {event_id}\nevent: end\ndata: {json.dumps({'status': 'completed'}, ensure_ascii=False)}\n\n"
    else:
        logger.info("Skipping end event due to interrupt - waiting for user approval")

async def stream_with_graph(graph, request_body, thread_id):
    """通用的图流媒体处理函数"""
    config, graph_input, stream_modes, checkpoint = prepare_graph_config(request_body, thread_id)
    logger.info(f"Starting stream with modes: {stream_modes}, checkpoint: {checkpoint}")
    
    event_id = 0
    has_interrupt = False
    
    async for chunk in graph.astream(graph_input, config=config, stream_mode=stream_modes, subgraphs=True):
        try:
            event_id += 1
            sse_data, chunk_has_interrupt = await process_stream_chunk(chunk, event_id, thread_id)
            yield sse_data
            if chunk_has_interrupt:
                has_interrupt = True
        except Exception as e:
            logger.error(f"Serialization error: {e}, chunk type: {type(chunk)}, chunk: {chunk}")
            event_id += 1
            yield f"id: {event_id}\nevent: error\ndata: {json.dumps({'error': str(e), 'chunk_type': str(type(chunk)), 'chunk': str(chunk)}, ensure_ascii=False)}\n\n"
    
    # End event - only send if no interrupt occurred
    if not has_interrupt:
        event_id += 1
        yield f"id: {event_id}\nevent: end\ndata: {json.dumps({'status': 'completed'}, ensure_ascii=False)}\n\n"
    else:
        logger.info("Skipping end event due to interrupt - waiting for user approval")

async def handle_postgres_streaming(request_body, thread_id):
    """处理PostgreSQL模式的流式响应"""
    from src.agents.diagnostic_agent.main_graph import builder
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    
    logger.info(f"🔍 PostgreSQL模式 - 按照官方模式使用async with")
    if thread_id in threads_store:
        threads_store[thread_id]["streaming_status"] = "starting"
    
    # 按照官方模式：在async with内完成整个请求周期
    async with AsyncPostgresSaver.from_conn_string(POSTGRES_CONNECTION_STRING) as checkpointer:
        await checkpointer.setup()
        graph = builder.compile(checkpointer=checkpointer, name="diagnostic-agent")
        
        # 在同一个async with内执行完整的流式处理
        async for item in stream_with_graph_postgres(graph, request_body, thread_id):
            yield item

async def handle_memory_streaming(request_body, thread_id):
    """处理内存模式的流式响应"""
    assistant = ASSISTANTS[request_body.assistant_id]
    graph = assistant["graph"]
    
    # 使用现有图进行流式处理
    async for item in stream_with_graph(graph, request_body, thread_id):
        yield item

async def stream_run_standard(thread_id: str, request_body: RunCreate):
    """Standard LangGraph streaming endpoint"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    if request_body.assistant_id not in ASSISTANTS: 
        raise HTTPException(status_code=400, detail="Invalid assistant_id")
    
    # 创建用户线程关联（如果提供了用户名且关联不存在）
    # 用户名可能在 request_body.user_name 或 request_body.input.user_name 中
    user_name = None
    if request_body.user_name:
        user_name = request_body.user_name
    elif request_body.input and isinstance(request_body.input, dict) and "user_name" in request_body.input:
        user_name = request_body.input["user_name"]
    
    if user_name:
        logger.info(f"🔍 开始处理用户线程关联: {user_name} -> {thread_id}")
        try:
            exists = await check_user_thread_exists(user_name, thread_id)
            logger.info(f"🔍 检查用户线程是否存在: {exists}")
            if not exists:
                # 尝试从输入内容中提取标题
                thread_title = None
                if request_body.input and "messages" in request_body.input:
                    messages = request_body.input["messages"]
                    if messages and len(messages) > 0:
                        last_msg = messages[-1]
                        if isinstance(last_msg, dict) and "content" in last_msg:
                            content = str(last_msg["content"])
                            # 取前20个字符作为标题
                            thread_title = content[:20] + "..." if len(content) > 20 else content
                
                logger.info(f"🔍 准备创建用户线程关联，标题: {thread_title}")
                success = await create_user_thread_mapping(
                    user_name, 
                    thread_id, 
                    thread_title
                )
                if success:
                    logger.info(f"✅ 已创建用户线程关联: {user_name} -> {thread_id}")
                else:
                    logger.warning(f"❌ 创建用户线程关联失败: {user_name} -> {thread_id}")
            else:
                logger.info(f"ℹ️ 用户线程关联已存在，跳过创建: {user_name} -> {thread_id}")
        except Exception as e:
            logger.error(f"处理用户线程关联时出错: {e}")
            # 不影响主流程，继续执行
    else:
        logger.warning(f"⚠️ 请求中没有提供用户名，跳过用户线程关联创建")

    async def generate():
        try:
            # 根据助手类型和checkpointer类型选择处理策略
            if should_use_postgres_mode(request_body.assistant_id):
                async for item in handle_postgres_streaming(request_body, thread_id):
                    yield item
            else:
                async for item in handle_memory_streaming(request_body, thread_id):
                    yield item
                
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield f"event: error\n"
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/event-stream"
        }
    )