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

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# Import graphs
from src.agents.diagnostic_agent.graph import graph as diagnostic_graph
from src.agents.research_agent.graph import graph as research_graph
from src.agents.diagnostic_agent.configuration import Configuration as DiagnosticConfiguration
from src.agents.research_agent.configuration import Configuration as ResearchConfiguration

# Import API modules
from .utils import test_postgres_connection
from .threads import (
    ThreadCreate, ThreadResponse, 
    create_thread, get_thread, get_thread_state, update_thread_state,
    get_thread_history, get_thread_history_post
)
from .streaming import (
    RunCreate, stream_run_standard,
    init_refs
)
from .sop_routes import router as sop_router
from .mcp_routes import router as mcp_router
from .agent_routes import router as agent_router
from .ai_model_routes import router as ai_model_router

# Define the FastAPI app
app = FastAPI(title="LangGraph Server", version="1.0.0")

# 应用启动时测试PostgreSQL连接
@app.on_event("startup")
async def startup_event():
    await test_postgres_connection()
    # 初始化各模块的存储引用（只初始化ASSISTANTS）
    init_refs(ASSISTANTS)
    
    # 初始化用户线程数据库连接
    from .user_threads_db import init_user_threads_db
    await init_user_threads_db()
    
    # 初始化SOP数据库（如果连接失败则跳过）
    try:
        from ..database.config import init_database, test_database_connection
        db_connected = await test_database_connection()
        if db_connected:
            await init_database()
            logger.info("✅ SOP数据库初始化成功")
        else:
            logger.warning("⚠️  SOP数据库连接失败，跳过数据库初始化")
    except Exception as e:
        logger.warning(f"⚠️  SOP数据库初始化失败: {e}，API将继续启动但SOP功能可能不可用")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
import os
from datetime import datetime

# 配置日志路径（可通过环境变量设置）
log_dir = os.getenv("LOG_DIR", "logs")
os.makedirs(log_dir, exist_ok=True)

# 配置日志格式和输出
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 配置日志文件名（按日期）
log_filename = os.path.join(log_dir, f"backend_{datetime.now().strftime('%Y%m%d')}.log")

# 同时输出到控制台和文件
logging.basicConfig(
    level=getattr(logging, log_level),
    format=log_format,
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler(log_filename, encoding='utf-8')  # 文件输出
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"📝 日志配置完成，级别: {log_level}, 文件: {log_filename}")


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

class AssistantResponse(BaseModel):
    assistant_id: str
    description: str

# Include routers
app.include_router(sop_router)
app.include_router(mcp_router, prefix="/api/mcp", tags=["mcp"])
app.include_router(agent_router)
app.include_router(ai_model_router, prefix="/api", tags=["ai-models"])

# Thread Management Endpoints - 使用导入的函数
@app.post("/threads", response_model=ThreadResponse)
async def create_thread_endpoint(thread_create: ThreadCreate):
    return await create_thread(thread_create)

# @app.get("/threads/{thread_id}", response_model=ThreadResponse)
# async def get_thread_endpoint(thread_id: str):
#     return await get_thread(thread_id)

# @app.get("/threads/{thread_id}/state")
# async def get_thread_state_endpoint(thread_id: str):
#     return await get_thread_state(thread_id)

# @app.post("/threads/{thread_id}/state")
# async def update_thread_state_endpoint(thread_id: str, state: Dict[str, Any]):
#     return await update_thread_state(thread_id, state)

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

# @app.put("/users/{user_name}/threads/{thread_id}/title")
# async def update_thread_title_endpoint(user_name: str, thread_id: str, request_body: Dict[str, Any]):
#     """更新线程标题"""
#     from .user_threads_db import update_thread_title
#     new_title = request_body.get("title", "")
#     if not new_title:
#         raise HTTPException(status_code=400, detail="Title is required")
    
#     success = await update_thread_title(user_name, thread_id, new_title)
#     if success:
#         return {"success": True, "message": "Thread title updated successfully"}
#     else:
#         raise HTTPException(status_code=404, detail="Thread not found or update failed")

# Assistant Management Endpoints
# @app.get("/assistants", response_model=List[AssistantResponse])
# async def list_assistants():
#     """List available assistants"""
#     return [
#         AssistantResponse(
#             assistant_id=assistant_id,
#             description=assistant["description"]
#         )
#         for assistant_id, assistant in ASSISTANTS.items()
#     ]

# @app.get("/assistants/{assistant_id}", response_model=AssistantResponse)
# async def get_assistant(assistant_id: str):
#     """Get assistant details"""
#     if assistant_id not in ASSISTANTS:
#         raise HTTPException(status_code=404, detail="Assistant not found")
    
#     assistant = ASSISTANTS[assistant_id]
#     return AssistantResponse(
#         assistant_id=assistant_id,
#         description=assistant["description"]
#     )


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
