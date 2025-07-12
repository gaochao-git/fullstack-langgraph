# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import os
# Import graphs
from src.agents.diagnostic_agent.graph import graph as diagnostic_graph
from src.agents.research_agent.graph import graph as research_graph
from src.agents.diagnostic_agent.configuration import Configuration as DiagnosticConfiguration
from src.agents.research_agent.configuration import Configuration as ResearchConfiguration

# Define the FastAPI app
app = FastAPI(title="LangGraph Server", version="1.0.0")

# 应用启动时测试PostgreSQL连接
@app.on_event("startup")
async def startup_event():
    await test_postgres_connection()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# In-memory storage for threads and runs (TODO: replace with persistent storage)
threads_store: Dict[str, Dict[str, Any]] = {}
runs_store: Dict[str, Dict[str, Any]] = {}
# Store message history for each thread
thread_messages: Dict[str, List[Dict[str, Any]]] = {}
# Store interrupt information for each thread
thread_interrupts: Dict[str, List[Dict[str, Any]]] = {}

# 全局连接字符串配置
POSTGRES_CONNECTION_STRING = "postgresql://postgres:fffjjj@82.156.146.51:5432/langgraph_memory"

async def test_postgres_connection():
    """启动时测试PostgreSQL连接"""
    checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
    if checkpointer_type == "postgres":
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            async with AsyncPostgresSaver.from_conn_string(POSTGRES_CONNECTION_STRING) as checkpointer:
                await checkpointer.setup()
                logger.info("✅ PostgreSQL连接测试成功")
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接测试失败: {e}")
            raise e

# 线程恢复工具函数
async def recover_thread_from_postgres(thread_id: str) -> bool:
    """从PostgreSQL checkpointer中恢复线程信息"""
    try:
        checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
        if checkpointer_type != "postgres":
            return False
            
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
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

# Available assistants based on langgraph.json
ASSISTANTS = {
    "research_agent": {
        "assistant_id": "research_agent",
        "graph": research_graph,
        "config_class": ResearchConfiguration,
        "description": "Research agent for information gathering and analysis"
    },
    "diagnostic_agent": {
        "assistant_id": "diagnostic_agent", 
        "graph": diagnostic_graph,
        "config_class": DiagnosticConfiguration,
        "description": "Diagnostic agent for system troubleshooting"
    }
}

# Pydantic models
class ThreadCreate(BaseModel):
    metadata: Optional[Dict[str, Any]] = None

class ThreadResponse(BaseModel):
    thread_id: str
    created_at: str
    metadata: Dict[str, Any]

class RunCreate(BaseModel):
    assistant_id: str
    input: Optional[Dict[str, Any]] = None  # 改为可选，resume时不需要input
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    stream_mode: Optional[List[str]] = ["values"]  # 修改为数组类型
    interrupt_before: Optional[List[str]] = None
    interrupt_after: Optional[List[str]] = None
    on_disconnect: Optional[str] = None  # 添加前端发送的字段
    command: Optional[Dict[str, Any]] = None  # 添加command字段用于resume
    checkpoint: Optional[Dict[str, Any]] = None  # 添加checkpoint字段

class RunResponse(BaseModel):
    run_id: str
    thread_id: str
    assistant_id: str
    created_at: str
    status: str
    metadata: Dict[str, Any]

class AssistantResponse(BaseModel):
    assistant_id: str
    description: str

# Thread Management Endpoints
@app.post("/threads", response_model=ThreadResponse)
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

@app.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str):
    """Get thread details"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadResponse(**threads_store[thread_id])

@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Get thread state"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    return threads_store[thread_id].get("state", {})

@app.post("/threads/{thread_id}/state")
async def update_thread_state(thread_id: str, state: Dict[str, Any]):
    """Update thread state"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    threads_store[thread_id]["state"] = state
    return {"success": True}

@app.get("/threads/{thread_id}/history")
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

@app.post("/threads/{thread_id}/history")
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

# Run Management Endpoints
@app.post("/threads/{thread_id}/runs", response_model=RunResponse)
async def create_run(thread_id: str, run_create: RunCreate):
    """Create and start a new run"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    
    if run_create.assistant_id not in ASSISTANTS:
        raise HTTPException(status_code=400, detail="Invalid assistant_id")
    
    run_id = str(uuid.uuid4())
    run_data = {
        "run_id": run_id,
        "thread_id": thread_id,
        "assistant_id": run_create.assistant_id,
        "created_at": datetime.now().isoformat(),
        "status": "running",
        "metadata": run_create.metadata or {},
        "config": run_create.config or {},
        "input": run_create.input
    }
    runs_store[run_id] = run_data
    logger.info(f"Created run: {run_id} for thread: {thread_id}")
    
    # Start async run
    asyncio.create_task(_execute_run(run_id))
    
    return RunResponse(**run_data)

@app.get("/threads/{thread_id}/runs/{run_id}")
async def get_run(thread_id: str, run_id: str):
    """Get run details"""
    if run_id not in runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_data = runs_store[run_id]
    if run_data["thread_id"] != thread_id:
        raise HTTPException(status_code=404, detail="Run not found in thread")
    
    return run_data

# 工具函数 - 提取到模块级别
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
        }
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

async def process_stream_chunk(chunk, event_id, thread_id):
    """处理单个流式数据块"""
    # Handle tuple format from LangGraph streaming
    if isinstance(chunk, tuple) and len(chunk) == 2:
        event_type, data = chunk
        serialized_data = serialize_value(data)
        
        # Save messages to thread history from LangGraph state
        if event_type == "values" and isinstance(data, dict) and "messages" in data:
            if thread_id not in thread_messages:
                thread_messages[thread_id] = []
            thread_messages[thread_id] = [serialize_value(msg) for msg in data["messages"]]
        
        # Check for interrupts
        has_interrupt = False
        if event_type == "updates" and isinstance(data, dict) and "__interrupt__" in data:
            logger.info(f"Interrupt detected: {data}")
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
    
    async for chunk in graph.astream(graph_input, config=config, stream_mode=stream_modes):
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
    
    async for chunk in graph.astream(graph_input, config=config, stream_mode=stream_modes):
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
    from src.agents.diagnostic_agent.graph import builder
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

# LangGraph标准的流媒体端点
@app.post("/threads/{thread_id}/runs/stream")
async def stream_run_standard(thread_id: str, request_body: RunCreate):
    """Standard LangGraph streaming endpoint"""
    if thread_id not in threads_store:
        # 尝试从PostgreSQL恢复线程
        recovered = await recover_thread_from_postgres(thread_id)
        if not recovered:
            raise HTTPException(status_code=404, detail="Thread not found")
    if request_body.assistant_id not in ASSISTANTS: 
        raise HTTPException(status_code=400, detail="Invalid assistant_id")

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


@app.post("/threads/{thread_id}/runs/{run_id}/interrupt")
async def interrupt_run(thread_id: str, run_id: str):
    """Interrupt a running run"""
    if run_id not in runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
    
    runs_store[run_id]["status"] = "interrupted"
    return {"success": True, "run_id": run_id}

@app.post("/threads/{thread_id}/runs/{run_id}/resume")
async def resume_run(thread_id: str, run_id: str, command: Optional[Dict[str, Any]] = None):
    """Resume an interrupted run"""
    if run_id not in runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
    
    runs_store[run_id]["status"] = "running"
    # TODO: Implement actual resume logic with command
    return {"success": True, "run_id": run_id}

# Assistant Management Endpoints
@app.get("/assistants", response_model=List[AssistantResponse])
async def list_assistants():
    """List available assistants"""
    return [
        AssistantResponse(
            assistant_id=assistant_id,
            description=assistant["description"]
        )
        for assistant_id, assistant in ASSISTANTS.items()
    ]

@app.get("/assistants/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(assistant_id: str):
    """Get assistant details"""
    if assistant_id not in ASSISTANTS:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    assistant = ASSISTANTS[assistant_id]
    return AssistantResponse(
        assistant_id=assistant_id,
        description=assistant["description"]
    )

# Helper function to execute runs
async def _execute_run(run_id: str):
    """Execute a run asynchronously"""
    try:
        run_data = runs_store[run_id]
        assistant = ASSISTANTS[run_data["assistant_id"]]
        graph = assistant["graph"]
        
        # Build config
        config = {
            "configurable": run_data.get("config", {}),
            "thread_id": run_data["thread_id"]
        }
        
        # Execute the graph
        result = await graph.ainvoke(run_data["input"], config=config)
        
        # Update thread state with result
        threads_store[run_data["thread_id"]]["state"].update(result)
        runs_store[run_id]["status"] = "completed"
        runs_store[run_id]["result"] = result
        
    except Exception as e:
        logger.error(f"Error executing run {run_id}: {e}")
        runs_store[run_id]["status"] = "failed"
        runs_store[run_id]["error"] = str(e)


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    return StaticFiles(directory=build_path, html=True)


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
) 