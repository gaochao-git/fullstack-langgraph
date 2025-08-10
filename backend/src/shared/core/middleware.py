"""
FastAPI中间件模块
提供请求日志、性能监控、错误处理等中间件
"""

import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging import get_logger, set_request_context, clear_request_context, logger_manager, log_request, log_alarm


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = logger_manager.generate_request_id()
        
        # 从请求头获取用户信息（如果有的话）
        user_id = request.headers.get("X-User-ID")
        agent_id = request.headers.get("X-Agent-ID")
        
        # 设置请求上下文
        set_request_context(
            request_id=request_id,
            user_id=user_id,
            agent_id=agent_id
        )
        
        # 记录请求开始
        start_time = time.time()
        
        # 获取请求体（小心处理，避免消费stream）
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                if request.headers.get("content-type", "").startswith("application/json"):
                    body = await request.body()
                    if body:
                        request_body = json.loads(body.decode())
                        # 过滤敏感信息
                        if isinstance(request_body, dict):
                            request_body = self._filter_sensitive_data(request_body)
            except:
                request_body = None
        
        # 请求开始时只做简单记录，详细信息在完成时记录
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 使用新的请求日志格式
            log_request(
                method=request.method,
                url=request.url.path,
                status_code=response.status_code,
                response_time=process_time * 1000,  # 转换为毫秒
                client_ip=request.client.host if request.client else "-",
                user_id=user_id,
                error_code=str(response.status_code)
            )
            
            # 仅在DEBUG模式下记录详细日志
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Request completed: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)", extra={
                    'method': request.method,
                    'url': str(request.url),
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'process_time': f"{process_time:.3f}s"
                })
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求日志（错误状态）
            log_request(
                method=request.method,
                url=request.url.path,
                status_code=500,
                response_time=process_time * 1000,
                client_ip=request.client.host if request.client else "-",
                user_id=user_id,
                error_code="500"
            )
            
            # 记录报警日志
            log_alarm(
                error_msg=f"{type(e).__name__}: {str(e)}",
                error_code="INTERNAL_ERROR",
                client_ip=request.client.host if request.client else "-"
            )
            
            # 应用日志记录错误概要（包含完整堆栈信息）
            self.logger.error(f"Request failed: {request.method} {request.url.path} - {type(e).__name__}", exc_info=True)
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "request_id": request_id,
                    "message": "An error occurred while processing your request"
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": f"{process_time:.3f}s"
                }
            )
        
        finally:
            # 清除请求上下文
            clear_request_context()
    
    def _filter_sensitive_data(self, data: dict) -> dict:
        """过滤敏感数据"""
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'auth',
            'credential', 'passwd', 'pwd', 'api_key'
        }
        
        filtered_data = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
                filtered_data[key] = "***FILTERED***"
            elif isinstance(value, dict):
                filtered_data[key] = self._filter_sensitive_data(value)
            else:
                filtered_data[key] = value
        
        return filtered_data


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 5.0):
        super().__init__(app)
        self.logger = get_logger(__name__)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 记录慢请求
        if process_time > self.slow_request_threshold:
            self.logger.warning("Slow request detected", extra={
                'method': request.method,
                'url': str(request.url),
                'process_time': f"{process_time:.3f}s",
                'threshold': f"{self.slow_request_threshold}s"
            })
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查请求大小
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            self.logger.warning("Large request detected", extra={
                'method': request.method,
                'url': str(request.url),
                'content_length': content_length,
                'client_ip': request.client.host if request.client else None
            })
        
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


class CORSLoggingMiddleware(BaseHTTPMiddleware):
    """CORS日志中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        if origin and request.method == "OPTIONS":
            self.logger.debug("CORS preflight request", extra={
                'origin': origin,
                'method': request.method,
                'url': str(request.url)
            })
        
        response = await call_next(request)
        return response


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """API指标收集中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(__name__)
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 更新指标
            self.metrics['total_requests'] += 1
            if 200 <= response.status_code < 400:
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1
            
            # 更新平均响应时间
            self.metrics['average_response_time'] = (
                (self.metrics['average_response_time'] * (self.metrics['total_requests'] - 1) + process_time)
                / self.metrics['total_requests']
            )
            
            # 每100个请求记录一次指标
            if self.metrics['total_requests'] % 100 == 0:
                self.logger.info("API metrics update", extra=self.metrics.copy())
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            self.metrics['total_requests'] += 1
            self.metrics['failed_requests'] += 1
            raise


def setup_middlewares(app):
    """设置所有中间件"""
    
    # 请求日志中间件（最外层）
    app.add_middleware(RequestLoggingMiddleware)
    
    # 性能监控中间件
    app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=5.0)
    
    # 安全中间件
    app.add_middleware(SecurityMiddleware)
    
    # CORS日志中间件
    app.add_middleware(CORSLoggingMiddleware)
    
    # API指标中间件
    app.add_middleware(APIMetricsMiddleware)
    
    logger = get_logger(__name__)
    logger.info("All middlewares configured successfully")