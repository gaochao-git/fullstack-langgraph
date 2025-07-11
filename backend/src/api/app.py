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

# Import graphs
from src.agents.diagnostic_agent.graph import graph as diagnostic_graph
from src.agents.research_agent.graph import graph as research_graph
from src.agents.diagnostic_agent.configuration import Configuration as DiagnosticConfiguration
from src.agents.research_agent.configuration import Configuration as ResearchConfiguration

# Define the FastAPI app
app = FastAPI(title="LangGraph Server", version="1.0.0")

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
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    stream_mode: Optional[List[str]] = ["values"]  # 修改为数组类型
    interrupt_before: Optional[List[str]] = None
    interrupt_after: Optional[List[str]] = None
    on_disconnect: Optional[str] = None  # 添加前端发送的字段

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
    logger.info(f"Created thread: {thread_id}")
    return ThreadResponse(**thread_data)

@app.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str):
    """Get thread details"""
    if thread_id not in threads_store:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadResponse(**threads_store[thread_id])

@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Get thread state"""
    if thread_id not in threads_store:
        raise HTTPException(status_code=404, detail="Thread not found")
    return threads_store[thread_id].get("state", {})

@app.post("/threads/{thread_id}/state")
async def update_thread_state(thread_id: str, state: Dict[str, Any]):
    """Update thread state"""
    if thread_id not in threads_store:
        raise HTTPException(status_code=404, detail="Thread not found")
    threads_store[thread_id]["state"] = state
    return {"success": True}

@app.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str, limit: int = 10, before: Optional[str] = None):
    """Get all past states for a thread"""
    if thread_id not in threads_store:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # TODO: Implement proper history tracking with checkpoints
    # For now, return a simple history based on stored state
    thread_data = threads_store[thread_id]
    
    # Mock history response - in real implementation this would come from checkpoints
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
            "values": thread_data.get("state", {}),
            "next": [],
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
    if thread_id not in threads_store:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Extract parameters from request body if provided
    limit = 10
    before = None
    if request_body:
        limit = request_body.get("limit", 10)
        before = request_body.get("before", None)
    
    # TODO: Implement proper history tracking with checkpoints
    # For now, return a simple history based on stored state
    thread_data = threads_store[thread_id]
    
    # Mock history response - in real implementation this would come from checkpoints
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
            "values": thread_data.get("state", {}),
            "next": [],
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

# LangGraph标准的流媒体端点
@app.post("/threads/{thread_id}/runs/stream")
async def stream_run_standard(thread_id: str, request_body: RunCreate):
    """Standard LangGraph streaming endpoint"""
    if thread_id not in threads_store:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if request_body.assistant_id not in ASSISTANTS:
        raise HTTPException(status_code=400, detail="Invalid assistant_id")
    
    async def generate():
        try:
            assistant = ASSISTANTS[request_body.assistant_id]
            graph = assistant["graph"]
            
            # Build config
            config = {
                "configurable": request_body.config or {},
                "thread_id": thread_id
            }
            
            # Stream the graph execution in proper SSE format
            event_id = 0
            async for chunk in graph.astream(request_body.input, config=config,stream_mode=["values", "messages", "updates","custom","checkpoints","tasks"]):
                try:
                    event_id += 1
                    # Convert chunk to JSON-serializable format
                    def serialize_value(val):
                        # Handle tuples (like from LangGraph messages)
                        if isinstance(val, tuple):
                            return [serialize_value(item) for item in val]
                        elif hasattr(val, 'dict'):
                            # Pydantic models
                            return val.dict()
                        elif hasattr(val, 'to_dict'):
                            # Objects with to_dict method
                            return val.to_dict()
                        elif hasattr(val, '__dict__'):
                            # Regular objects - recursively serialize
                            result = {}
                            for k, v in val.__dict__.items():
                                if not k.startswith('_'):  # Skip private attributes
                                    result[k] = serialize_value(v)
                            return result
                        elif isinstance(val, list):
                            # Lists - recursively serialize each item
                            return [serialize_value(item) for item in val]
                        elif isinstance(val, dict):
                            # Dictionaries - recursively serialize values
                            return {k: serialize_value(v) for k, v in val.items()}
                        else:
                            # Primitive types or fallback to string
                            try:
                                json.dumps(val)  # Test if serializable
                                return val
                            except (TypeError, ValueError):
                                return str(val)
                    
                    # Handle tuple format from LangGraph streaming
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        event_type, data = chunk
                        serialized_data = serialize_value(data)
                        yield f"id: {event_id}\n"
                        yield f"event: {event_type}\n"
                        yield f"data: {json.dumps(serialized_data)}\n\n"
                    else:
                        # Handle dict format (fallback)
                        serializable_chunk = {}
                        for key, value in chunk.items():
                            serializable_chunk[key] = serialize_value(value)
                        
                        # Format as proper SSE with event type based on chunk key
                        event_type = list(serializable_chunk.keys())[0] if serializable_chunk else "data"
                        yield f"id: {event_id}\n"
                        yield f"event: {event_type}\n"
                        yield f"data: {json.dumps(serializable_chunk[event_type])}\n\n"
                except Exception as e:
                    logger.error(f"Serialization error: {e}, chunk type: {type(chunk)}, chunk: {chunk}")
                    event_id += 1
                    yield f"id: {event_id}\n"
                    yield f"event: error\n"
                    yield f"data: {json.dumps({'error': str(e), 'chunk_type': str(type(chunk)), 'chunk': str(chunk)})}\n\n"
                
            # End event
            event_id += 1
            yield f"id: {event_id}\n"
            yield f"event: end\n"
            yield f"data: {json.dumps({'status': 'completed'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield f"event: error\n"
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
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

@app.post("/threads/{thread_id}/runs/{run_id}/stream")
async def stream_run(thread_id: str, run_id: str):
    """Stream run results"""
    if run_id not in runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_data = runs_store[run_id]
    if run_data["thread_id"] != thread_id:
        raise HTTPException(status_code=404, detail="Run not found in thread")
    
    async def generate():
        try:
            assistant = ASSISTANTS[run_data["assistant_id"]]
            graph = assistant["graph"]
            
            # Build config
            config = {
                "configurable": run_data.get("config", {}),
                "thread_id": thread_id
            }
            
            # Stream the graph execution
            async for chunk in graph.astream(run_data["input"], config=config,stream_mode=["values", "messages", "updates","custom","checkpoints","tasks"]):
                try:
                    # Convert chunk to JSON-serializable format
                    serializable_chunk = {}
                    for key, value in chunk.items():
                        if hasattr(value, 'dict'):
                            # Pydantic models
                            serializable_chunk[key] = value.dict()
                        elif hasattr(value, '__dict__'):
                            # Regular objects with __dict__
                            serializable_chunk[key] = value.__dict__
                        else:
                            # Primitive types
                            serializable_chunk[key] = value
                    yield f"data: {json.dumps(serializable_chunk)}\n\n"
                except Exception as e:
                    logger.error(f"Serialization error: {e}")
                    yield f"data: {json.dumps({'type': 'chunk', 'data': str(chunk)})}\n\n"
                
            # Update run status
            runs_store[run_id]["status"] = "completed"
            yield f"data: {json.dumps({'type': 'end', 'run_id': run_id})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in run {run_id}: {e}")
            runs_store[run_id]["status"] = "failed"
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
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