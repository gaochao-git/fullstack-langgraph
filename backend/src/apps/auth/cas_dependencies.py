"""
CAS认证依赖项
用于FastAPI的依赖注入
"""

from typing import Optional
from fastapi import Depends, HTTPException, Request, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from src.shared.db.config import get_async_db
from src.apps.auth.models import AuthSession
from src.apps.user.models import RbacUser
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


async def get_cas_session(
    cas_session_id: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[AuthSession]:
    """
    获取CAS会话
    从Cookie中读取session_id并验证
    """
    if not cas_session_id:
        return None
    
    # 查询Session
    stmt = select(AuthSession).where(
        AuthSession.session_id == cas_session_id,
        AuthSession.sso_provider == "cas",
        AuthSession.is_active == True
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        return None
    
    # 检查是否过期
    if session.expires_at < datetime.now(timezone.utc):
        # Session已过期，标记为非活跃
        session.is_active = False
        session.terminated_at = datetime.now(timezone.utc)
        session.termination_reason = "会话过期"
        await db.commit()
        return None
    
    # 更新最后访问时间
    session.last_accessed_at = datetime.now(timezone.utc)
    await db.commit()
    
    return session


async def require_cas_auth(
    session: Optional[AuthSession] = Depends(get_cas_session),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    要求CAS认证的依赖项
    
    使用方法：
    ```python
    @router.get("/cas/protected")
    async def protected_endpoint(cas_user: dict = Depends(require_cas_auth)):
        return {"message": f"Hello {cas_user['username']}"}
    ```
    """
    if not session:
        raise HTTPException(
            status_code=401,
            detail="需要CAS认证",
            headers={"WWW-Authenticate": "CAS"}
        )
    
    # 获取用户信息
    stmt = select(RbacUser).where(RbacUser.user_id == session.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    return {
        "user_id": user.user_id,
        "username": user.user_name,
        "display_name": user.display_name,
        "email": user.email,
        "session_id": session.session_id,
        "auth_type": "cas"
    }


async def optional_cas_auth(
    session: Optional[AuthSession] = Depends(get_cas_session),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[dict]:
    """
    可选的CAS认证
    如果有Session返回用户信息，没有则返回None
    """
    if not session:
        return None
    
    # 获取用户信息
    stmt = select(RbacUser).where(RbacUser.user_id == session.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    return {
        "user_id": user.user_id,
        "username": user.user_name,
        "display_name": user.display_name,
        "email": user.email,
        "session_id": session.session_id,
        "auth_type": "cas"
    }


async def get_current_auth_info(
    request: Request,
    cas_user: Optional[dict] = Depends(optional_cas_auth)
) -> dict:
    """
    获取当前认证信息（支持JWT和CAS混合）
    
    返回统一的认证信息格式：
    - auth_type: "jwt" | "cas" | None
    - user: 用户信息字典
    """
    # 1. 检查是否有CAS认证
    if cas_user:
        return {
            "auth_type": "cas",
            "user": cas_user
        }
    
    # 2. 检查是否有JWT认证（从request.state获取）
    if hasattr(request.state, "current_user"):
        return {
            "auth_type": "jwt",
            "user": request.state.current_user
        }
    
    # 3. 未认证
    return {
        "auth_type": None,
        "user": None
    }