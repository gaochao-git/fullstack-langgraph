"""
认证和权限中间件
自动检查请求的权限
"""

from typing import Callable, Optional, List
from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db, AsyncSessionLocal
from src.apps.auth.utils import JWTUtils, TokenBlacklist
from src.apps.auth.service.rbac_service import RBACService
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


# 定义认证排除路径常量
AUTH_EXCLUDE_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/sso",
    "/api/v1/auth/cas",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/password-policy",
    "/api/v1/auth/check",
    "/api/v1/auth/admin/menus",  # 菜单列表（公开）
    "/api/v1/auth/init",
    "/api/v1/config/system",  # 系统配置（公开）
    "/api/v1/mcp/gateway/configs/all",  # MCP Gateway配置（公开）
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/health",
]

# 定义RBAC权限检查排除路径常量
RBAC_EXCLUDE_PATHS = [
    "/api/v1/auth",
    "/api/v1/agent/ws",  # WebSocket不需要权限检查
    "/api/v1/agent/sse",  # SSE流式接口
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/health",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    支持JWT、CAS、Agent Key等多种认证方式
    """
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or AUTH_EXCLUDE_PATHS
    
    async def _authenticate_jwt(self, token: str) -> Optional[dict]:
        """
        JWT认证
        """
        try:
            # 验证JWT
            payload = JWTUtils.decode_token(token)
            
            # 检查黑名单
            jti = payload.get("jti")
            if jti and TokenBlacklist.is_blacklisted(jti):
                raise BusinessException("令牌已失效", ResponseCode.UNAUTHORIZED)
            
            return {
                "user_info": payload,
                "auth_type": "jwt"
            }
        except Exception as e:
            logger.debug(f"JWT认证失败: {e}")
            return None
    
    async def _authenticate_agent_key(self, token: str, request: Request) -> Optional[dict]:
        """
        Agent Key认证 - 通过agent_permission表查找关联信息
        """
        if not token.startswith("sk-"):
            return None
        
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                from src.apps.agent.models import AgentConfig, AgentPermission
                from src.apps.user.models import RbacUser
                
                # 1. 首先从请求中获取agent_id（必须）
                agent_id = None
                user_name = None
                
                # 从查询参数获取
                agent_id = request.query_params.get("agent_id")
                
                # 如果是POST请求且查询参数中没有，尝试从请求体获取
                if request.method == "POST" and not agent_id:
                    content_type = request.headers.get("content-type", "")
                    
                    # 处理JSON请求
                    if "application/json" in content_type:
                        body = await request.body()
                        request._body = body  # 保存以供后续使用
                        
                        if body:
                            import json
                            try:
                                data = json.loads(body)
                                if not agent_id:
                                    agent_id = data.get("agent_id")
                            except json.JSONDecodeError:
                                pass
                    
                    # 处理multipart/form-data请求（文件上传）
                    elif "multipart/form-data" in content_type:
                        try:
                            from starlette.datastructures import FormData
                            async def receive():
                                body = await request.body()
                                return {"type": "http.request", "body": body}
                            
                            # 创建新的请求对象来解析form data
                            scope = request.scope.copy()
                            form_request = Request(scope, receive)
                            form = await form_request.form()
                            
                            if not agent_id:
                                agent_id = form.get("agent_id")
                            
                            # 保存form数据以供后续使用
                            request._form = form
                        except Exception as e:
                            logger.debug(f"解析FormData失败: {e}")
                
                # 对于某些接口，agent_id 是可选的
                path = request.url.path
                agent_id_optional_paths = [
                    "/api/v1/chat/threads",  # 获取线程列表
                    "/api/chat/threads",  # 兼容旧路径
                ]
                
                # 验证是否有agent_id
                if not agent_id and not any(path.startswith(p) for p in agent_id_optional_paths):
                    raise BusinessException("使用agent_key认证时必须提供agent_id", ResponseCode.BAD_REQUEST)
                
                # 2. 通过agent_key和agent_id在permission表中查找（如果有agent_id）
                permission = None
                if agent_id:
                    perm_stmt = select(AgentPermission).where(
                        AgentPermission.agent_key == token,
                        AgentPermission.agent_id == agent_id,
                        AgentPermission.is_active == True
                    )
                    perm_result = await db.execute(perm_stmt)
                    permission = perm_result.scalar_one_or_none()
                
                if permission:
                    # 使用permission表中的user_name
                    user_name = permission.user_name
                    logger.info(f"通过agent_permission表找到权限配置: agent_id={agent_id}, user_name={user_name}, key={token[:10]}...")
                else:
                    # 如果没有找到匹配的权限记录
                    if agent_id:
                        logger.warning(f"agent_key和agent_id不匹配: key={token[:10]}..., agent_id={agent_id}")
                        raise BusinessException("agent_key无效或未授权访问该智能体", ResponseCode.FORBIDDEN)
                    else:
                        # 对于不需要agent_id的接口，无法验证权限
                        logger.warning(f"agent_key无法验证（缺少agent_id）: key={token[:10]}...")
                        raise BusinessException("agent_key无效或未授权", ResponseCode.FORBIDDEN)
                
                # 3. 验证agent是否存在（如果提供了agent_id）
                agent = None
                if agent_id:
                    stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
                    result = await db.execute(stmt)
                    agent = result.scalar_one_or_none()
                    
                    if not agent:
                        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
                
                # 5. 验证用户是否存在
                user_stmt = select(RbacUser).where(RbacUser.user_name == user_name)
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                
                if not user:
                    raise BusinessException(f"用户 {user_name} 不存在", ResponseCode.NOT_FOUND)
                
                # 保存agent信息到request（如果有）
                if agent:
                    request.state.agent = agent
                
                # 构建用户信息
                user_info = {
                    "sub": user.user_id,
                    "user_id": user.user_id,
                    "username": user.user_name,
                    "display_name": user.display_name,
                    "auth_type": "agent_key",
                    "roles": [],  # TODO: 可以加载用户的实际角色
                    "is_agent": True
                }
                
                # 如果有agent信息，添加到用户信息中
                if agent:
                    user_info["agent_id"] = agent.agent_id
                    user_info["agent_name"] = agent.agent_name
                
                return {
                    "user_info": user_info,
                    "auth_type": "agent_key"
                }
                
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Agent Key认证失败: {e}")
            return None
    
    async def _authenticate_cas(self, request: Request) -> Optional[dict]:
        """
        CAS认证（通过Cookie）
        """
        cas_session_id = request.cookies.get("cas_session_id")
        if not cas_session_id:
            return None
        
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                from src.apps.auth.models import AuthSession
                from datetime import datetime, timezone
                
                stmt = select(AuthSession).where(
                    AuthSession.session_id == cas_session_id,
                    AuthSession.is_active == True
                )
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()
                
                if session and session.expires_at > datetime.now():
                    # 获取用户详细信息
                    from src.apps.user.models import RbacUser, RbacUsersRoles, RbacRole
                    user_stmt = select(RbacUser).where(RbacUser.user_id == session.user_id)
                    user_result = await db.execute(user_stmt)
                    user = user_result.scalar_one_or_none()
                    
                    if user and user.is_active:
                        # 获取用户角色
                        roles_stmt = select(RbacRole).join(
                            RbacUsersRoles, RbacUsersRoles.role_id == RbacRole.role_id
                        ).where(RbacUsersRoles.user_id == user.user_id)
                        
                        roles_result = await db.execute(roles_stmt)
                        roles = list(roles_result.scalars().all())
                        
                        return {
                            "user_info": {
                                "sub": session.user_id,
                                "username": user.user_name,
                                "email": user.email,
                                "display_name": user.display_name,
                                "auth_type": "cas",
                                "session_id": session.session_id,
                                "roles": [{"role_id": r.role_id, "role_name": r.role_name} for r in roles]
                            },
                            "auth_type": "cas"
                        }
        except Exception as e:
            logger.error(f"CAS认证失败: {e}")
            
        return None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否是排除的路径
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        try:
            # 尝试各种认证方式
            auth_result = None
            
            # 1. 检查Authorization头
            authorization = request.headers.get("Authorization")
            if authorization:
                scheme, token = get_authorization_scheme_param(authorization)
                if scheme.lower() == "bearer":
                    # 尝试JWT认证
                    auth_result = await self._authenticate_jwt(token)
                    
                    # 如果JWT失败，尝试Agent Key认证
                    if not auth_result:
                        auth_result = await self._authenticate_agent_key(token, request)
            
            # 2. 如果Authorization认证失败，尝试CAS认证
            if not auth_result:
                auth_result = await self._authenticate_cas(request)
            
            # 3. TODO: 其他认证方式（如API Key）
            if not auth_result:
                api_key = request.headers.get("X-API-Key")
                if api_key:
                    # TODO: 实现API Key验证
                    pass
            
            # 检查是否有有效的认证
            if not auth_result:
                logger.info(f"No authentication provided for path: {request.url.path}")
                raise BusinessException("未提供有效的认证凭据", ResponseCode.UNAUTHORIZED)
            
            # 设置请求状态
            request.state.current_user = auth_result["user_info"]
            request.state.auth_type = auth_result["auth_type"]
            
            # 继续处理请求
            response = await call_next(request)
            return response
            
        except BusinessException as e:
            # 捕获业务异常并返回统一格式响应
            from fastapi.responses import JSONResponse
            from src.shared.schemas.response import error_response
            
            response = error_response(msg=e.message, code=e.code)
            return JSONResponse(
                status_code=200,
                content=response.model_dump()
            )


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
        self.exclude_paths = exclude_paths or RBAC_EXCLUDE_PATHS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要权限检查
        if not self.check_permissions:
            return await call_next(request)
        
        # 检查是否是排除的路径
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        try:
            # 获取用户信息（由AuthMiddleware设置）
            user = getattr(request.state, "current_user", None)
            if not user:
                # 如果没有用户信息，说明是公开接口或认证中间件没有正确设置
                return await call_next(request)
            
            # 检查认证类型，如果是agent_key认证，跳过权限检查
            auth_type = getattr(request.state, "auth_type", None)
            if auth_type == "agent_key":
                return await call_next(request)
            
            # 检查权限
            user_id = user.get("sub")
            method = request.method
            
            # 创建数据库会话
            async with AsyncSessionLocal() as db:
                service = RBACService(db)
                
                # 检查是否有访问权限
                has_permission = await service.check_permission(user_id, path, method)
                if not has_permission:
                    # 记录权限拒绝日志
                    from src.shared.core.logging import get_logger
                    logger = get_logger(__name__)
                    logger.warning(f"Permission denied for user {user_id}: {method} {path}")
                    
                    raise BusinessException(
                        f"没有访问权限: {method} {path}",
                        ResponseCode.FORBIDDEN
                    )
            
            # 继续处理请求
            response = await call_next(request)
            return response
            
        except BusinessException as e:
            # 捕获业务异常并返回统一格式响应
            from fastapi.responses import JSONResponse
            from src.shared.schemas.response import error_response
            
            response = error_response(msg=e.message, code=e.code)
            return JSONResponse(
                status_code=200,
                content=response.dict()
            )


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
    
    注意：中间件的添加顺序很重要
    - 后添加的中间件先执行
    - 认证必须在权限检查之前
    
    使用示例:
    ```python
    from fastapi import FastAPI
    from src.apps.auth.middleware import setup_auth_middleware
    
    app = FastAPI()
    setup_auth_middleware(app)
    ```
    """
    # 添加RBAC权限中间件（需要认证信息）
    # 使用默认的排除路径，不再重复定义
    app.add_middleware(
        RBACMiddleware, 
        check_permissions=True
    )
    
    # 添加认证中间件（必须在权限中间件之前）
    # 使用默认的排除路径，不再重复定义
    app.add_middleware(AuthMiddleware)
    
    # 添加审计中间件（最内层，可选）
    # app.add_middleware(AuditMiddleware, log_requests=True)


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