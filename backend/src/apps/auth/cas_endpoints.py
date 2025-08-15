"""
CAS专用端点
与JWT认证完全隔离
"""

from fastapi import APIRouter, Depends, Request, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.shared.db.config import get_async_db
from src.apps.auth.service import CASService
from src.apps.auth.cas_dependencies import require_cas_auth, optional_cas_auth, get_cas_session
from src.apps.auth.models import AuthSession
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode, success_response
from datetime import datetime, timezone

router = APIRouter(prefix="/v1/cas", tags=["CAS认证"])


@router.get("/login", summary="获取CAS登录URL")
async def get_cas_login_url(
    next_url: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取CAS登录URL
    
    Args:
        next_url: 登录成功后的跳转URL
    """
    service = CASService(db)
    login_url = service.get_login_url()
    
    # 如果有next_url，可以存储在session或state中
    if next_url:
        # TODO: 存储next_url以便callback时使用
        pass
    
    return success_response({
        "login_url": login_url
    })


@router.get("/callback", summary="CAS登录回调")
async def cas_callback(
    ticket: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db)
):
    """
    处理CAS登录回调
    创建Session并设置Cookie
    """
    service = CASService(db)
    
    # 获取客户端信息
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    
    # 处理CAS登录
    cas_result = await service.process_cas_login(ticket, ip_address, user_agent)
    
    # 设置Session Cookie
    response.set_cookie(
        key="cas_session_id",
        value=cas_result["session_id"],
        max_age=cas_result["expires_in"],
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax"
    )
    
    return success_response({
        "message": "CAS登录成功",
        "user": cas_result["user"],
        "expires_in": cas_result["expires_in"]
    })


@router.post("/logout", summary="CAS登出")
async def cas_logout(
    response: Response,
    session: Optional[AuthSession] = Depends(get_cas_session),
    db: AsyncSession = Depends(get_async_db)
):
    """
    CAS登出
    清除Session和Cookie
    """
    if session:
        # 标记Session为非活跃
        session.is_active = False
        session.terminated_at = datetime.now(timezone.utc)
        session.termination_reason = "用户主动登出"
        await db.commit()
    
    # 清除Cookie
    response.delete_cookie("cas_session_id")
    
    # 获取CAS登出URL
    service = CASService(db)
    logout_url = service.get_logout_url()
    
    return success_response({
        "message": "登出成功",
        "logout_url": logout_url
    })


@router.get("/session", summary="获取当前CAS会话信息")
async def get_cas_session_info(
    cas_user: dict = Depends(require_cas_auth)
):
    """
    获取当前CAS会话信息
    需要CAS认证
    """
    return success_response({
        "session": cas_user
    })


@router.get("/check", summary="检查CAS认证状态")
async def check_cas_auth(
    cas_user: Optional[dict] = Depends(optional_cas_auth)
):
    """
    检查CAS认证状态
    不需要认证，返回当前状态
    """
    if cas_user:
        return success_response({
            "authenticated": True,
            "user": cas_user
        })
    else:
        return success_response({
            "authenticated": False,
            "user": None
        })


@router.get("/protected-resource", summary="CAS保护的资源示例")
async def cas_protected_resource(
    cas_user: dict = Depends(require_cas_auth)
):
    """
    需要CAS认证才能访问的资源示例
    """
    return success_response({
        "message": f"欢迎 {cas_user['display_name']}！",
        "data": {
            "resource": "这是一个受CAS保护的资源",
            "user_id": cas_user['user_id'],
            "auth_type": cas_user['auth_type']
        }
    })


@router.get("/sessions/active", summary="获取用户活跃会话")
async def get_active_sessions(
    cas_user: dict = Depends(require_cas_auth),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前用户的所有活跃CAS会话
    """
    from sqlalchemy import select
    
    stmt = select(AuthSession).where(
        AuthSession.user_id == cas_user['user_id'],
        AuthSession.sso_provider == "cas",
        AuthSession.is_active == True
    ).order_by(AuthSession.created_at.desc())
    
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    session_list = []
    for session in sessions:
        session_list.append({
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "last_accessed_at": session.last_accessed_at.isoformat() if session.last_accessed_at else None,
            "ip_address": session.ip_address,
            "is_current": session.session_id == cas_user['session_id']
        })
    
    return success_response({
        "sessions": session_list,
        "total": len(session_list)
    })