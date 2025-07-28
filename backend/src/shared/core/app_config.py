"""FastAPI应用配置 - 注册全局异常处理器"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.shared.core.exceptions import (
    BusinessException,
    DatabaseException,
    business_exception_handler,
    database_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)


def configure_exception_handlers(app: FastAPI) -> None:
    """配置全局异常处理器"""
    
    # 业务异常
    app.add_exception_handler(BusinessException, business_exception_handler)
    
    # 数据库异常
    app.add_exception_handler(DatabaseException, database_exception_handler)
    
    # HTTP异常
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 参数验证异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # SQLAlchemy异常
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # 通用异常处理器（放在最后）
    app.add_exception_handler(Exception, general_exception_handler)


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title="FullStack LangGraph API",
        description="统一响应格式的API服务",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置异常处理器
    configure_exception_handlers(app)
    
    return app


# 使用示例
"""
在 main.py 中使用:

from src.shared.core.app_config import create_app
from src.apps.sop.router.endpoints import router as sop_router

app = create_app()

# 注册路由
app.include_router(sop_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""