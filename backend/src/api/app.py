# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import os

# Import graphs
from src.agents.diagnostic_agent.graph import graph as diagnostic_graph
from src.agents.research_agent.graph import graph as research_graph
from src.agents.diagnostic_agent.configuration import Configuration as DiagnosticConfiguration
from src.agents.research_agent.configuration import Configuration as ResearchConfiguration

# Import API modules
from .utils import test_postgres_connection, init_storage_refs as init_utils_refs
from .threads import (
    ThreadCreate, ThreadResponse, 
    create_thread, get_thread, get_thread_state, update_thread_state,
    get_thread_history, get_thread_history_post,
    init_storage_refs as init_threads_refs
)
from .streaming import (
    RunCreate, stream_run_standard,
    init_refs as init_streaming_refs
)

# Define the FastAPI app
app = FastAPI(title="LangGraph Server", version="1.0.0")

# 应用启动时测试PostgreSQL连接
@app.on_event("startup")
async def startup_event():
    await test_postgres_connection()
    # 初始化各模块的存储引用
    init_utils_refs(threads_store, thread_messages, thread_interrupts)
    init_threads_refs(threads_store, thread_messages, thread_interrupts)
    init_streaming_refs(threads_store, thread_messages, thread_interrupts, ASSISTANTS)
    
    # 初始化用户线程数据库连接
    from .user_threads_db import init_user_threads_db
    await init_user_threads_db()

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

# Thread Management Endpoints - 使用导入的函数
@app.post("/threads", response_model=ThreadResponse)
async def create_thread_endpoint(thread_create: ThreadCreate):
    return await create_thread(thread_create)

@app.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread_endpoint(thread_id: str):
    return await get_thread(thread_id)

@app.get("/threads/{thread_id}/state")
async def get_thread_state_endpoint(thread_id: str):
    return await get_thread_state(thread_id)

@app.post("/threads/{thread_id}/state")
async def update_thread_state_endpoint(thread_id: str, state: Dict[str, Any]):
    return await update_thread_state(thread_id, state)

@app.get("/threads/{thread_id}/history")
async def get_thread_history_endpoint(thread_id: str, limit: int = 10, before: Optional[str] = None):
    return await get_thread_history(thread_id, limit, before)

@app.post("/threads/{thread_id}/history")
async def get_thread_history_post_endpoint(thread_id: str, request_body: Optional[Dict[str, Any]] = None):
    return await get_thread_history_post(thread_id, request_body)

# Streaming Endpoints - 使用导入的函数
@app.post("/threads/{thread_id}/runs/stream")
async def stream_run_standard_endpoint(thread_id: str, request_body: RunCreate):
    return await stream_run_standard(thread_id, request_body)

# 用户线程管理接口
@app.get("/users/{user_name}/threads")
async def get_user_threads_endpoint(user_name: str, limit: int = 10, offset: int = 0):
    """获取用户的所有线程"""
    from .user_threads_db import get_user_threads
    threads = await get_user_threads(user_name, limit, offset)
    return {"user_name": user_name, "threads": threads, "total": len(threads)}

@app.put("/users/{user_name}/threads/{thread_id}/title")
async def update_thread_title_endpoint(user_name: str, thread_id: str, request_body: Dict[str, Any]):
    """更新线程标题"""
    from .user_threads_db import update_thread_title
    new_title = request_body.get("title", "")
    if not new_title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    success = await update_thread_title(user_name, thread_id, new_title)
    if success:
        return {"success": True, "message": "Thread title updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Thread not found or update failed")

# Run Management Endpoints
@app.post("/threads/{thread_id}/runs", response_model=RunResponse)
async def create_run(thread_id: str, run_create: RunCreate):
    """Create and start a new run"""
    from .utils import recover_thread_from_postgres
    
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
