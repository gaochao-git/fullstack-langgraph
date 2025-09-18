"""
FastAPI应用入口文件
"""

import uvicorn
import pathlib
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
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
from .shared.core.exceptions import EXCEPTION_HANDLERS
from .router import api_router





@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    logger = get_logger(__name__)
    
    # 初始化 checkpoint
    try:
        from .apps.agent import checkpoint_factory
        await checkpoint_factory.init()
    except Exception as e:
        logger.error(f"Checkpoint 初始化失败: {e}", exc_info=True)
    
    # 自动扫描并同步API权限
    try:
        from .shared.core.api_permission_scanner import scan_and_sync_api_permissions
        stats = await scan_and_sync_api_permissions(app)
        logger.info(f"✅ API权限同步完成: 新增 {stats['created']}, 跳过 {stats['skipped']}")
        if stats['orphaned'] > 0:
            logger.warning(f"⚠️ 发现 {stats['orphaned']} 个孤立权限")
    except Exception as e:
        logger.error(f"❌ API权限同步失败: {e}", exc_info=True)
    
    yield  # 应用运行期间
    
    # 关闭事件
    try:
        from .apps.agent import checkpoint_factory
        await checkpoint_factory.cleanup()
    except Exception as e:
        logger.error(f"清理失败: {e}", exc_info=True)
    
    # 关闭数据库引擎
    try:
        from .shared.db.config import async_engine
        if async_engine:
            await async_engine.dispose()
            logger.info("✅ 异步数据库引擎已关闭")
    except Exception as e:
        logger.error(f"关闭数据库引擎失败: {e}", exc_info=True)


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
        lifespan=lifespan  # 使用新的lifespan事件处理
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
app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app",host=settings.HOST,port=settings.PORT,reload=settings.DEBUG,log_level="info")