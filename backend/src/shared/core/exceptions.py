"""全局异常处理"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from src.shared.schemas.response import error_response, ResponseCode
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class BusinessException(Exception):
    """业务异常"""
    def __init__(self, message: str, code: int = ResponseCode.BAD_REQUEST):
        self.message = message
        self.code = code
        super().__init__(message)


class DatabaseException(Exception):
    """数据库异常"""
    def __init__(self, message: str = "数据库操作失败"):
        self.message = message
        super().__init__(message)


async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    logger.warning(f"业务异常: {exc.message}")
    response = error_response(msg=exc.message, code=exc.code)
    return JSONResponse(
        status_code=200,  # 业务异常返回200，通过response.status区分
        content=response.dict()
    )


async def database_exception_handler(request: Request, exc: DatabaseException):
    """数据库异常处理器"""
    logger.error(f"数据库异常: {exc.message}", exc_info=True)
    response = error_response(
        msg=exc.message, 
        code=ResponseCode.INTERNAL_ERROR
    )
    return JSONResponse(
        status_code=200,
        content=response.dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    # 映射HTTP状态码到我们的错误码
    code_mapping = {
        400: ResponseCode.BAD_REQUEST,
        401: ResponseCode.UNAUTHORIZED,
        403: ResponseCode.FORBIDDEN,
        404: ResponseCode.NOT_FOUND,
        405: ResponseCode.METHOD_NOT_ALLOWED,
        409: ResponseCode.CONFLICT,
        422: ResponseCode.VALIDATION_ERROR,
        500: ResponseCode.INTERNAL_ERROR,
        501: ResponseCode.NOT_IMPLEMENTED,
        502: ResponseCode.BAD_GATEWAY,
        503: ResponseCode.SERVICE_UNAVAILABLE,
    }
    
    response_code = code_mapping.get(exc.status_code, ResponseCode.INTERNAL_ERROR)
    response = error_response(msg=str(exc.detail), code=response_code)
    
    return JSONResponse(
        status_code=200,
        content=response.dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数验证异常处理器"""
    # 简化日志记录，详细信息由审计中间件处理
    logger.warning("参数验证失败")
    
    # 提取第一个验证错误的详细信息
    first_error = exc.errors()[0] if exc.errors() else {}
    field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "参数验证失败")
    
    error_msg = f"字段 {field}: {msg}" if field else msg
    
    response = error_response(
        msg=error_msg,
        code=ResponseCode.VALIDATION_ERROR
    )
    
    return JSONResponse(
        status_code=422,  # 使用标准的422状态码
        content=response.dict()
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """SQLAlchemy异常处理器"""
    logger.error(f"数据库异常: {str(exc)}", exc_info=True)
    response = error_response(
        msg="数据库操作失败",
        code=ResponseCode.INTERNAL_ERROR
    )
    return JSONResponse(
        status_code=200,
        content=response.dict()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    response = error_response(
        msg="服务器内部错误",
        code=ResponseCode.INTERNAL_ERROR
    )
    return JSONResponse(
        status_code=200,
        content=response.dict()
    )


# 异常处理器映射
EXCEPTION_HANDLERS = {
    BusinessException: business_exception_handler,
    DatabaseException: database_exception_handler,
    HTTPException: http_exception_handler,
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    ValidationError: validation_exception_handler,
    SQLAlchemyError: sqlalchemy_exception_handler,
    Exception: general_exception_handler,
}