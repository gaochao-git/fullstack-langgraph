"""
FastAPI应用入口文件
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入核心模块
from .shared.core.config import settings
from .shared.core.logging import setup_logging, get_logger
from .shared.core.middleware import setup_middlewares
from .shared.core.exceptions import EXCEPTION_HANDLERS
from .router import api_router
from .shared.db.config import init_db, close_db
from .apps.agent.checkpoint_factory import init as init_checkpoint, cleanup as cleanup_checkpoint
from .apps.agent.llm_agents.agent_registry import AgentRegistry
from .shared.db.config import get_async_db_context


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger = get_logger(__name__)
    logger.info("=== 应用启动 ===")
    
    # 初始化数据库连接池
    try:
        await init_db()
        logger.info("业务数据库初始化成功")
    except Exception as e:
        logger.error(f"业务数据库初始化失败: {e}")
        raise
    
    # 初始化checkpoint数据库
    try:
        await init_checkpoint()
        logger.info("Checkpoint数据库初始化成功")
    except Exception as e:
        logger.error(f"Checkpoint数据库初始化失败: {e}")
        # Checkpoint失败不应该阻止应用启动，只记录警告
        logger.warning("应用将在没有checkpoint功能的情况下运行")
    
    # 初始化Agent注册表
    try:
        async with get_async_db_context() as db:
            await AgentRegistry.initialize(db)
        logger.info("Agent注册表初始化成功")
    except Exception as e:
        logger.error(f"Agent注册表初始化失败: {e}")
        # 非关键功能，失败不影响应用启动
        logger.warning("应用将在没有预注册Agent的情况下运行")

    # 初始化Mem0长期记忆系统（向量数据库 PostgreSQL）
    try:
        from src.apps.agent.memory_factory import get_enterprise_memory
        memory = await get_enterprise_memory()
        if memory:
            logger.info("✅ Mem0长期记忆系统初始化成功 (PostgreSQL向量库)")
        else:
            logger.info("Mem0长期记忆系统未启用")
    except Exception as e:
        logger.error(f"Mem0长期记忆系统初始化失败: {e}")
        # Mem0失败不应该阻止应用启动
        logger.warning("应用将在没有长期记忆功能的情况下运行")

    yield
    
    # 清理资源
    logger.info("=== 应用关闭 ===")
    await close_db()
    await cleanup_checkpoint()


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    # 配置日志系统（优先配置）
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_dir=settings.LOG_DIR,
        app_name="omind",  # 日志文件名前缀
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
        redoc_url="/redoc",
        lifespan=lifespan  # 添加生命周期管理
    )
    
    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 设置API审计中间件（在其他中间件之前，确保能捕获到所有请求）
    from .shared.core.api_audit import setup_api_audit_middleware
    setup_api_audit_middleware(app)
    
    # 设置所有中间件
    setup_middlewares(app)
    
    # 注册异常处理器
    for exception_type, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_type, handler)

    # 启动和关闭事件已移至lifespan函数

    # 注册API路由
    app.include_router(api_router, prefix="/api")
    return app


# 创建应用实例
omind_app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:omind_app",host=settings.HOST,port=settings.PORT,reload=settings.DEBUG,log_level="info")