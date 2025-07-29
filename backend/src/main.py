"""
FastAPI应用入口文件
"""

import uvicorn
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
from .router import api_router

# 导入LLM相关模块
from .apps.agent.utils import test_postgres_connection




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
    
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        logger.info("🚀 启动LangGraph Platform API...")
        
        # 测试PostgreSQL连接
        await test_postgres_connection()
        
        # 智能体配置完全基于数据库，无需静态初始化
        logger.info("📊 智能体配置完全基于数据库，动态加载")
        
        # 初始化用户线程数据库
        from .apps.agent.service.user_threads_db import init_user_threads_db
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
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app",host=settings.HOST,port=settings.PORT,reload=settings.DEBUG,log_level="info")