"""
FastAPI应用入口文件
"""

import pathlib
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入核心模块
from .shared.core.config import settings
from .shared.core.logging import setup_logging, get_logger
from .shared.core.middleware import setup_middlewares
from .api.router import api_router

# 导入智能体相关
from src.agents.diagnostic_agent.graph import graph as diagnostic_graph
from src.agents.research_agent.graph import graph as research_graph
from src.agents.generic_agent.graph import create_main_graph
from src.agents.diagnostic_agent.configuration import Configuration as DiagnosticConfiguration
from src.agents.research_agent.configuration import Configuration as ResearchConfiguration
from src.agents.generic_agent.configuration import Configuration as GenericConfiguration

# 导入API相关模块
from .api.utils import test_postgres_connection
from .api.threads import (
    ThreadCreate, ThreadResponse,
    create_thread, get_thread_history_post
)
from .api.streaming import RunCreate, stream_run_standard, init_refs




def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    # 配置日志系统（优先配置）
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_dir=settings.LOG_DIR,
        app_name="error",  # 日志文件名为error.log
        enable_json=False,  # 默认使用文本格式
        rotation_type="time"  # 按时间轮转，适合长期运行的应用
    )
    
    logger = get_logger(__name__)
    
    # 创建应用
    app = FastAPI(
        title=settings.APP_NAME,
        description="智能诊断平台后端API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 设置所有中间件
    setup_middlewares(app)
    
    # 静态智能体配置
    ASSISTANTS = {
        "diagnostic_agent": {
            "assistant_id": "diagnostic_agent",
            "graph": diagnostic_graph,
            "config_class": DiagnosticConfiguration,
            "description": "Diagnostic agent for system troubleshooting"
        },
        "research_agent": {
            "assistant_id": "research_agent",
            "graph": research_graph,
            "config_class": ResearchConfiguration,
            "description": "Research agent for information gathering and analysis"
        },
        "generic_agent": {
            "assistant_id": "generic_agent",
            "graph": create_main_graph(),
            "config_class": GenericConfiguration,
            "description": "Generic agent for custom agents configuration"
        }
    }
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        logger.info("🚀 启动LangGraph Platform API...")
        
        # 测试PostgreSQL连接
        await test_postgres_connection()
        
        # 初始化智能体配置
        logger.info(f"📊 初始化智能体配置: {list(ASSISTANTS.keys())}")
        init_refs(ASSISTANTS)
        
        # 初始化用户线程数据库
        from .api.user_threads_db import init_user_threads_db
        await init_user_threads_db()
        
        # 初始化SOP数据库
        try:
            from .shared.db.config import init_database, test_database_connection
            db_connected = await test_database_connection()
            if db_connected:
                await init_database()
                logger.info("✅ SOP数据库初始化成功")
            else:
                logger.warning("⚠️  SOP数据库连接失败，跳过数据库初始化")
        except Exception as e:
            logger.warning(f"⚠️  SOP数据库初始化失败: {e}，API将继续启动但SOP功能可能不可用")
    
    # 注册API路由
    app.include_router(api_router, prefix="/api")
    
    # 线程管理端点
    @app.post("/threads", response_model=ThreadResponse)
    async def create_thread_endpoint(thread_create: ThreadCreate):
        return await create_thread(thread_create)
    
    @app.post("/threads/{thread_id}/history")
    async def get_thread_history_post_endpoint(thread_id: str, request_body: Optional[Dict[str, Any]] = None):
        return await get_thread_history_post(thread_id, request_body)
    
    @app.post("/threads/{thread_id}/runs/stream")
    async def stream_run_standard_endpoint(thread_id: str, request_body: RunCreate):
        return await stream_run_standard(thread_id, request_body)
    
    # 用户线程管理
    @app.get("/users/{user_name}/threads")
    async def get_user_threads_endpoint(user_name: str, limit: int = 10, offset: int = 0):
        """获取用户的所有线程"""
        from .api.user_threads_db import get_user_threads
        threads = await get_user_threads(user_name, limit, offset)
        return {"user_name": user_name, "threads": threads, "total": len(threads)}
    
    # 智能体状态查询
    @app.get("/api/admin/assistants-status")
    async def get_assistants_status():
        """获取核心智能体架构状态"""
        return {
            "core_assistants": list(ASSISTANTS.keys()),
            "message": "所有智能体配置完全基于数据库，无需刷新"
        }
    
    class AssistantResponse(BaseModel):
        assistant_id: str
        description: str
    
    # 前端静态文件服务
    def create_frontend_router(build_dir="../frontend/dist"):
        """创建前端静态文件路由"""
        build_path = pathlib.Path(__file__).parent.parent.parent / build_dir
        
        if not build_path.is_dir() or not (build_path / "index.html").is_file():
            logger.warning(f"前端构建目录未找到: {build_path}")
            from starlette.routing import Route
            
            async def dummy_frontend(request):
                return Response(
                    "Frontend not built. Run 'npm run build' in the frontend directory.",
                    media_type="text/plain",
                    status_code=503,
                )
            
            return Route("/{path:path}", endpoint=dummy_frontend)
        
        return StaticFiles(directory=build_path, html=True)
    
    # 挂载前端
    app.mount("/app", create_frontend_router(), name="frontend")
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )