"""
CAS Session认证中间件
处理基于Session的CAS认证，与JWT认证完全隔离
"""

from typing import Optional
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.apps.auth.models import AuthSession
from src.shared.db.config import get_async_db_context
from src.shared.core.logging import get_logger
from datetime import datetime, timezone

logger = get_logger(__name__)


class CASSessionMiddleware:
    """CAS Session认证中间件"""
    
    def __init__(self, exclude_paths: list = None):
        """
        初始化中间件
        
        Args:
            exclude_paths: 不需要认证的路径列表
        """
        self.exclude_paths = exclude_paths or [
            "/api/v1/auth/cas/login",
            "/api/v1/auth/cas/callback",
            "/api/v1/auth/cas/logout",
            "/docs",
            "/openapi.json",
            "/health"
        ]
    
    async def __call__(self, request: Request, call_next):
        """处理请求"""
        # 检查是否需要跳过认证
        if self._should_skip_auth(request):
            return await call_next(request)
        
        # 检查是否是CAS保护的路径
        if not self._is_cas_protected_path(request):
            return await call_next(request)
        
        # 验证CAS Session
        session_id = self._get_session_id(request)
        if not session_id:
            raise HTTPException(
                status_code=401,
                detail="需要CAS认证"
            )
        
        # 验证Session有效性
        user_info = await self._validate_session(session_id)
        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="CAS会话无效或已过期"
            )
        
        # 将用户信息添加到请求中
        request.state.cas_user = user_info
        request.state.auth_type = "cas"
        
        # 继续处理请求
        response = await call_next(request)
        return response
    
    def _should_skip_auth(self, request: Request) -> bool:
        """检查是否应该跳过认证"""
        path = request.url.path
        return any(path.startswith(exclude) for exclude in self.exclude_paths)
    
    def _is_cas_protected_path(self, request: Request) -> bool:
        """检查是否是CAS保护的路径"""
        path = request.url.path
        # 定义需要CAS认证的路径模式
        cas_protected_patterns = [
            "/api/v1/cas/",  # CAS专用API
            "/cas/",         # CAS相关页面
        ]
        return any(path.startswith(pattern) for pattern in cas_protected_patterns)
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """从请求中获取Session ID"""
        # 1. 从Cookie中获取
        session_id = request.cookies.get("cas_session_id")
        if session_id:
            return session_id
        
        # 2. 从Header中获取（某些场景下可能需要）
        session_header = request.headers.get("X-CAS-Session-ID")
        if session_header:
            return session_header
        
        return None
    
    async def _validate_session(self, session_id: str) -> Optional[dict]:
        """验证Session有效性"""
        async with get_async_db_context() as db:
            # 查询Session
            stmt = select(AuthSession).where(
                AuthSession.session_id == session_id,
                AuthSession.sso_provider == "cas",
                AuthSession.is_active == True
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            # 检查是否过期
            if session.expires_at < datetime.now(timezone.utc):
                # Session已过期
                session.is_active = False
                session.terminated_at = datetime.now(timezone.utc)
                session.termination_reason = "会话过期"
                await db.commit()
                return None
            
            # 更新最后访问时间
            session.last_accessed_at = datetime.now(timezone.utc)
            await db.commit()
            
            # 返回用户信息
            return {
                "user_id": session.user_id,
                "session_id": session.session_id,
                "expires_at": session.expires_at
            }


def get_cas_user(request: Request) -> dict:
    """
    获取当前CAS用户信息
    
    在需要CAS认证的端点中使用：
    ```python
    @router.get("/cas/protected")
    async def cas_protected_endpoint(cas_user: dict = Depends(get_cas_user)):
        return {"message": f"Hello {cas_user['user_id']}"}
    ```
    """
    if not hasattr(request.state, "cas_user"):
        raise HTTPException(
            status_code=401,
            detail="需要CAS认证"
        )
    return request.state.cas_user