"""
认证和权限中间件
自动检查请求的权限
"""

from typing import Callable, Optional, List
from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db, async_session_maker
from src.apps.auth.utils import JWTUtils, TokenBlacklist
from src.apps.auth.rbac_service import RBACService
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    自动验证JWT令牌
    """
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/api/v1/auth/login",
            "/api/v1/auth/sso",
            "/api/v1/auth/forgot-password",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否是排除的路径
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # 获取Authorization头
        authorization = request.headers.get("Authorization")
        if not authorization:
            # 检查API Key
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                raise BusinessException(
                    "未提供认证凭据",
                    ResponseCode.UNAUTHORIZED
                )
        
        # 解析Bearer Token
        if authorization:
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != "bearer":
                raise BusinessException(
                    "无效的认证方案",
                    ResponseCode.UNAUTHORIZED
                )
            
            try:
                # 验证JWT
                payload = JWTUtils.decode_token(token)
                
                # 检查黑名单
                jti = payload.get("jti")
                if jti and TokenBlacklist.is_blacklisted(jti):
                    raise BusinessException(
                        "令牌已失效",
                        ResponseCode.UNAUTHORIZED
                    )
                
                # 将用户信息添加到请求状态
                request.state.user = payload
                
            except BusinessException:
                raise
            except Exception:
                raise BusinessException(
                    "令牌验证失败",
                    ResponseCode.UNAUTHORIZED
                )
        
        # 继续处理请求
        response = await call_next(request)
        return response


class RBACMiddleware(BaseHTTPMiddleware):
    """
    RBAC权限中间件
    自动检查API权限
    """
    
    def __init__(
        self, 
        app, 
        check_permissions: bool = True,
        exclude_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.check_permissions = check_permissions
        self.exclude_paths = exclude_paths or [
            "/api/v1/auth",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要权限检查
        if not self.check_permissions:
            return await call_next(request)
        
        # 检查是否是排除的路径
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # 获取用户信息（由AuthMiddleware设置）
        user = getattr(request.state, "user", None)
        if not user:
            # 如果没有用户信息，说明是公开接口
            return await call_next(request)
        
        # 检查权限
        user_id = user.get("sub")
        method = request.method
        
        # 创建数据库会话
        async with async_session_maker() as db:
            service = RBACService(db)
            
            # 检查是否有访问权限
            has_permission = await service.check_permission(user_id, path, method)
            if not has_permission:
                raise BusinessException(
                    f"没有访问权限: {method} {path}",
                    ResponseCode.FORBIDDEN
                )
        
        # 继续处理请求
        response = await call_next(request)
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计中间件
    记录API访问日志
    """
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求信息
        if self.log_requests:
            user = getattr(request.state, "user", None)
            user_id = user.get("sub") if user else "anonymous"
            
            # TODO: 实际应该写入数据库或日志系统
            print(f"[AUDIT] {request.method} {request.url.path} - User: {user_id}")
        
        # 处理请求
        response = await call_next(request)
        
        # 记录响应信息
        if self.log_responses:
            print(f"[AUDIT] Response: {response.status_code}")
        
        return response


def setup_auth_middleware(app):
    """
    设置认证相关的中间件
    
    使用示例:
    ```python
    from fastapi import FastAPI
    from src.apps.auth.middleware import setup_auth_middleware
    
    app = FastAPI()
    setup_auth_middleware(app)
    ```
    """
    # 添加审计中间件（最外层）
    app.add_middleware(AuditMiddleware, log_requests=True)
    
    # 添加RBAC权限中间件
    app.add_middleware(RBACMiddleware, check_permissions=True)
    
    # 添加认证中间件
    app.add_middleware(AuthMiddleware)


# 动态权限检查装饰器
def check_resource_permission(resource_type: str):
    """
    动态资源权限检查装饰器
    
    使用示例:
    ```python
    @router.get("/items/{item_id}")
    @check_resource_permission("item")
    async def get_item(item_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
        # 检查用户是否有访问该item的权限
        pass
    ```
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取当前用户和资源ID
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")
            
            if not current_user or not db:
                raise BusinessException(
                    "权限检查配置错误",
                    ResponseCode.INTERNAL_ERROR
                )
            
            # 获取资源ID（假设第一个参数是资源ID）
            resource_id = args[0] if args else kwargs.get(f"{resource_type}_id")
            
            # TODO: 实现具体的资源权限检查逻辑
            # 例如：检查用户是否是资源的所有者或有相应角色
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator