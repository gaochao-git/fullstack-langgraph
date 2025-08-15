"""
认证相关的API路由
"""

import json
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Request, Response, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from src.shared.db.config import get_async_db
from src.apps.auth.service import AuthService, SSOService
from src.apps.auth.schema import (
    LoginRequest, LoginResponse, RefreshTokenRequest, LogoutRequest,
    RegisterRequest, RegisterResponse,
    SSOLoginUrlResponse, SSOCallbackRequest,
    UserProfile, ChangePasswordRequest, ResetPasswordRequest, ForgotPasswordRequest,
    EnableMFARequest, EnableMFAResponse, VerifyMFARequest, DisableMFARequest,
    CreateAPIKeyRequest, CreateAPIKeyResponse, APIKeyInfo,
    SessionInfo, TerminateSessionRequest,
    TokenValidationResponse, PermissionCheckRequest,
    MenuCreateRequest, MenuUpdateRequest, MenuResponse, 
    MenuTreeResponse, MenuListResponse, UserMenuResponse
)
from src.apps.auth.service import menu_service
from src.apps.auth.dependencies import get_current_user, require_auth, require_roles
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode, success_response


router = APIRouter(prefix="/v1/auth", tags=["认证"])
security = HTTPBearer()


# ============= 认证接口 =============

@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    request: LoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户名密码登录
    
    - **username**: 用户名
    - **password**: 密码
    - **mfa_code**: MFA验证码（如果启用了MFA）
    - **device_id**: 设备ID（可选）
    - **device_name**: 设备名称（可选）
    """
    service = AuthService(db)
    
    # 获取请求信息
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent")
    
    return await service.login_with_password(request, ip_address, user_agent)


@router.post("/register", response_model=RegisterResponse, summary="用户注册")
async def register(
    request: RegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户注册
    
    - **username**: 用户名（3-20个字符，只能包含字母数字下划线）
    - **password**: 密码（根据系统密码策略要求）
    - **email**: 邮箱地址
    - **display_name**: 显示名称
    """
    service = AuthService(db)
    
    # 添加请求信息
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent")
    
    return await service.register_user(request, ip_address, user_agent)


@router.get("/password-policy", summary="获取密码策略")
async def get_password_policy():
    """
    获取当前系统的密码策略配置
    
    返回密码要求，供前端动态验证使用
    """
    from src.shared.core.config import settings
    
    # 构建密码要求描述
    requirements = []
    requirements.append(f"至少{settings.MIN_PASSWORD_LENGTH}个字符")
    
    if settings.REQUIRE_UPPERCASE:
        requirements.append("包含大写字母")
    if settings.REQUIRE_LOWERCASE:
        requirements.append("包含小写字母")
    if settings.REQUIRE_DIGITS:
        requirements.append("包含数字")
    if settings.REQUIRE_SPECIAL_CHARS:
        requirements.append("包含特殊字符")
    
    return {
        "min_length": settings.MIN_PASSWORD_LENGTH,
        "require_uppercase": settings.REQUIRE_UPPERCASE,
        "require_lowercase": settings.REQUIRE_LOWERCASE,
        "require_digits": settings.REQUIRE_DIGITS,
        "require_special_chars": settings.REQUIRE_SPECIAL_CHARS,
        "requirements_text": requirements,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?"
    }


@router.post("/refresh", summary="刷新访问令牌")
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """刷新访问令牌"""
    service = AuthService(db)
    return await service.refresh_access_token(request.refresh_token)


@router.post("/logout", summary="用户登出")
async def logout(
    request: LogoutRequest,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户登出
    
    - **everywhere**: 是否登出所有设备
    """
    service = AuthService(db)
    
    # 从token中获取jti
    from src.apps.auth.utils import JWTUtils
    jti = JWTUtils.get_jti(credentials.credentials)
    
    await service.logout(
        user_id=current_user["sub"],
        current_jti=jti,
        everywhere=request.everywhere
    )
    
    return {"message": "登出成功"}


@router.get("/me", response_model=UserProfile, summary="获取当前用户信息")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """获取当前登录用户的详细信息"""
    service = AuthService(db)
    return await service.get_user_profile(current_user["sub"])


@router.get("/me/permissions", summary="获取当前用户权限")
async def get_current_user_permissions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户的权限树（角色、权限、菜单）"""
    from src.apps.auth.rbac_service import RBACService
    
    service = RBACService(db)
    return await service.get_permission_tree(current_user["sub"])


@router.post("/verify", response_model=TokenValidationResponse, summary="验证令牌")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """验证访问令牌是否有效"""
    try:
        from src.apps.auth.utils import JWTUtils
        payload = JWTUtils.decode_token(credentials.credentials)
        
        return TokenValidationResponse(
            valid=True,
            user_id=payload.get("sub"),
            username=payload.get("username"),
            scopes=payload.get("scopes", []),
            expires_at=payload.get("exp")
        )
    except:
        return TokenValidationResponse(valid=False)


# ============= SSO接口 =============

@router.get("/sso/providers", summary="获取SSO提供商列表")
async def get_sso_providers(db: AsyncSession = Depends(get_async_db)):
    """获取可用的SSO提供商列表"""
    from src.apps.auth.models import AuthSSOProvider
    
    providers = db.query(AuthSSOProvider).filter(
        AuthSSOProvider.is_active == True
    ).order_by(AuthSSOProvider.priority.desc()).all()
    
    return [
        {
            "provider_id": p.provider_id,
            "provider_name": p.provider_name,
            "provider_type": p.provider_type
        }
        for p in providers
    ]


@router.get("/sso/url", response_model=SSOLoginUrlResponse, summary="获取SSO登录URL")
async def get_sso_login_url(
    provider: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取SSO登录URL
    
    - **provider**: SSO提供商标识
    """
    service = SSOService(db)
    return await service.get_login_url(provider)


@router.post("/sso/callback", response_model=LoginResponse, summary="SSO回调处理")
async def sso_callback(
    request: SSOCallbackRequest,
    req: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    处理SSO回调
    
    - **code**: 授权码
    - **state**: State参数
    - **provider**: 提供商标识
    """
    service = SSOService(db)
    
    # 添加请求信息
    request.ip_address = req.client.host
    request.user_agent = req.headers.get("user-agent")
    
    return await service.handle_callback(
        provider_id=request.provider,
        code=request.code,
        state=request.state
    )


# ============= CAS认证 =============

@router.get("/cas/login", summary="获取CAS登录URL")
async def get_cas_login_url(
    next_url: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """获取CAS登录URL"""
    from .service import CASService
    service = CASService(db)
    login_url = service.get_login_url()
    
    return success_response({
        "login_url": login_url
    })


@router.get("/cas/callback", summary="CAS登录回调")
async def cas_callback(
    ticket: str,
    req: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db)
):
    """处理CAS登录回调"""
    from .service import CASService
    service = CASService(db)
    
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent")
    
    cas_result = await service.process_cas_login(ticket, ip_address, user_agent)
    
    response.set_cookie(
        key="cas_session_id",
        value=cas_result["session_id"],
        max_age=cas_result["expires_in"],
        httponly=True,
        secure=req.url.scheme == "https",
        samesite="lax"
    )
    
    return success_response({
        "message": "CAS登录成功",
        "user": cas_result["user"],
        "expires_in": cas_result["expires_in"]
    })


@router.post("/cas/logout", summary="CAS登出")
async def cas_logout(
    response: Response,
    cas_session_id: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db)
):
    """处理CAS登出"""
    if cas_session_id:
        from sqlalchemy import select
        from .models import AuthSession
        
        stmt = select(AuthSession).where(
            AuthSession.session_id == cas_session_id,
            AuthSession.is_active == True
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session:
            session.is_active = False
            session.terminated_at = datetime.now(timezone.utc)
            session.termination_reason = "用户主动登出"
            await db.commit()
    
    response.delete_cookie("cas_session_id")
    
    from .service import CASService
    service = CASService(db)
    logout_url = service.get_logout_url()
    
    return success_response({
        "message": "登出成功",
        "logout_url": logout_url,
        "redirect_required": True
    })


# ============= 统一认证接口 =============

@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
    request: Request,
    cas_session_id: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前登录用户信息
    支持JWT和CAS两种认证方式
    """
    # 1. 检查JWT认证
    if hasattr(request.state, "current_user"):
        return success_response({
            "user": request.state.current_user,
            "auth_type": "jwt"
        })
    
    # 2. 检查CAS认证
    if cas_session_id:
        from sqlalchemy import select
        from .models import AuthSession
        from src.apps.user.models import RbacUser
        
        stmt = select(AuthSession).where(
            AuthSession.session_id == cas_session_id,
            AuthSession.is_active == True
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session and session.expires_at > datetime.now(timezone.utc):
            # 获取用户信息
            user_stmt = select(RbacUser).where(RbacUser.user_id == session.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                return success_response({
                    "user": {
                        "user_id": user.user_id,
                        "username": user.user_name,
                        "display_name": user.display_name,
                        "email": user.email
                    },
                    "auth_type": "cas"
                })
    
    raise BusinessException(
        "未登录",
        ResponseCode.UNAUTHORIZED
    )


@router.get("/check", summary="检查登录状态")
async def check_auth_status(
    request: Request,
    cas_session_id: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    检查用户登录状态
    不需要登录也能调用
    """
    # 复用get_current_user_info的逻辑，但不抛出异常
    try:
        result = await get_current_user_info(request, cas_session_id, db)
        return success_response({
            "authenticated": True,
            "auth_type": result["data"]["auth_type"],
            "user": result["data"]["user"]
        })
    except:
        return success_response({
            "authenticated": False,
            "auth_type": None,
            "user": None
        })


# ============= 密码管理 =============

@router.post("/change-password", summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """修改当前用户密码"""
    service = AuthService(db)
    await service.change_password(
        user_id=current_user["sub"],
        old_password=request.old_password,
        new_password=request.new_password
    )
    
    return {"message": "密码修改成功"}


@router.post("/forgot-password", summary="忘记密码")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    发送密码重置邮件
    
    - **email**: 注册邮箱
    """
    # TODO: 实现密码重置邮件发送
    return {"message": "如果邮箱存在，密码重置链接已发送"}


@router.post("/reset-password", summary="重置密码")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    使用重置令牌重置密码
    
    - **token**: 重置令牌
    - **new_password**: 新密码
    """
    # TODO: 实现密码重置
    return {"message": "密码重置成功"}


# ============= MFA管理 =============

@router.post("/mfa/enable", response_model=EnableMFAResponse, summary="启用MFA")
async def enable_mfa(
    request: EnableMFARequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """启用多因素认证"""
    # TODO: 实现MFA启用
    from src.apps.auth.utils import MFAUtils
    
    secret = MFAUtils.generate_secret()
    qr_uri = MFAUtils.generate_qr_uri(secret, current_user.get("email", ""))
    
    return EnableMFAResponse(
        secret=secret,
        qr_uri=qr_uri,
        backup_codes=[]  # TODO: 生成备份码
    )


@router.post("/mfa/verify", summary="验证MFA设置")
async def verify_mfa(
    request: VerifyMFARequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """验证MFA设置是否成功"""
    # TODO: 实现MFA验证
    return {"message": "MFA启用成功"}


@router.post("/mfa/disable", summary="禁用MFA")
async def disable_mfa(
    request: DisableMFARequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """禁用多因素认证"""
    # TODO: 实现MFA禁用
    return {"message": "MFA已禁用"}


# ============= API密钥管理 =============

@router.post("/api-keys", response_model=CreateAPIKeyResponse, summary="创建API密钥")
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """创建新的API密钥（管理员为指定用户创建）"""
    # TODO: 检查当前用户是否有管理员权限
    service = AuthService(db)
    return await service.create_api_key(request.user_id, request, current_user["username"])


@router.get("/api-keys", response_model=List[APIKeyInfo], summary="获取API密钥列表")
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """获取API密钥列表（管理员查看所有，普通用户只看自己的）"""
    # 先导入必要的模块
    from sqlalchemy import select, and_
    from sqlalchemy.orm import joinedload
    from src.apps.auth.models import AuthApiKey
    from src.apps.user.models import RbacUser
    
    # TODO: 检查是否是管理员，如果是管理员显示所有，否则只显示自己的
    # 暂时显示所有的（包括已禁用和已撤销的）
    stmt = select(AuthApiKey).order_by(
        AuthApiKey.create_time.desc()  # 按创建时间倒序
    )
    
    result = await db.execute(stmt)
    keys = result.scalars().all()
    
    # 获取用户信息
    users = {}
    if keys:
        user_ids = list(set(key.user_id for key in keys))
        user_stmt = select(RbacUser).where(RbacUser.user_id.in_(user_ids))
        user_result = await db.execute(user_stmt)
        users = {user.user_id: user for user in user_result.scalars().all()}
    
    return [
        APIKeyInfo(
            key_id=str(key.id),
            user_id=key.user_id,
            user_name=users.get(key.user_id).user_name if key.user_id in users else None,
            key_name=key.key_name,
            key_prefix=key.key_prefix,
            mark_comment=key.mark_comment,
            scopes=json.loads(key.scopes) if key.scopes else [],
            is_active=bool(key.is_active),
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            revoked_at=key.revoked_at,
            revoke_reason=key.revoke_reason,
            created_at=key.issued_at or key.create_time,
            allowed_ips=json.loads(key.allowed_ips) if key.allowed_ips else [],
            create_by=key.create_by,
            update_by=key.update_by
        )
        for key in keys
    ]


@router.delete("/api-keys/{key_id}", summary="撤销API密钥")
async def revoke_api_key(
    key_id: str,
    reason: str = "用户主动撤销",
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """永久撤销指定的API密钥
    
    撤销后的密钥将无法再次启用，这是一个永久性操作。
    如果只是想临时禁用，请使用禁用/启用功能。
    """
    from sqlalchemy import select, and_
    from src.apps.auth.models import AuthApiKey
    from datetime import datetime, timezone
    
    # 查询密钥
    stmt = select(AuthApiKey).where(
        AuthApiKey.id == int(key_id)
    )
    
    result = await db.execute(stmt)
    key = result.scalar_one_or_none()
    
    if not key:
        raise BusinessException(
            "API密钥不存在",
            ResponseCode.NOT_FOUND
        )
    
    # 检查是否已经撤销
    if key.revoked_at is not None:
        raise BusinessException(
            "API密钥已经被撤销",
            ResponseCode.BAD_REQUEST
        )
    
    # 永久撤销密钥
    key.revoked_at = datetime.now(timezone.utc)
    key.revoke_reason = reason
    key.is_active = 0  # 同时设置为非激活状态
    key.update_by = current_user["username"]  # 记录更新人
    
    return {"message": "API密钥已永久撤销"}


@router.put("/api-keys/{key_id}/toggle", summary="切换API密钥激活状态")
async def toggle_api_key_status(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """切换API密钥的激活状态（启用/禁用）
    
    这是一个临时性操作，可以随时切换。
    已撤销的密钥无法再次启用。
    """
    from sqlalchemy import select
    from src.apps.auth.models import AuthApiKey
    
    stmt = select(AuthApiKey).where(
        AuthApiKey.id == int(key_id)
    )
    
    result = await db.execute(stmt)
    key = result.scalar_one_or_none()
    
    if not key:
        raise BusinessException(
            "API密钥不存在",
            ResponseCode.NOT_FOUND
        )
    
    # 检查是否已经撤销
    if key.revoked_at is not None:
        raise BusinessException(
            "已撤销的API密钥无法重新启用",
            ResponseCode.BAD_REQUEST
        )
    
    # 切换激活状态
    key.is_active = 0 if key.is_active == 1 else 1
    key.update_by = current_user["username"]  # 记录更新人
    
    status = "启用" if key.is_active == 1 else "禁用"
    return {"message": f"API密钥已{status}", "is_active": bool(key.is_active)}


# ============= 会话管理 =============

@router.get("/sessions", response_model=List[SessionInfo], summary="获取活跃会话")
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户的所有活跃会话"""
    from src.apps.auth.models import AuthToken, AuthSession
    from src.apps.auth.utils import JWTUtils
    
    current_jti = JWTUtils.get_jti(credentials.credentials)
    
    # 获取所有未撤销的令牌
    tokens = db.query(AuthToken).filter(
        AuthToken.user_id == current_user["sub"],
        AuthToken.revoked == False,
        AuthToken.token_type == "refresh"  # 只显示refresh token代表的会话
    ).all()
    
    sessions = []
    for token in tokens:
        sessions.append(SessionInfo(
            session_id=token.token_jti,
            device_name=token.device_name,
            ip_address=token.ip_address,
            user_agent=token.user_agent,
            last_accessed_at=token.last_used_at or token.issued_at,
            created_at=token.issued_at,
            is_current=(token.token_jti == current_jti)
        ))
    
    return sessions


@router.post("/sessions/terminate", summary="终止会话")
async def terminate_session(
    request: TerminateSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """终止指定的会话"""
    from src.apps.auth.models import AuthToken
    from src.apps.auth.utils import TokenBlacklist
    from datetime import datetime, timezone
    
    # 查找并撤销该会话的所有令牌
    tokens = db.query(AuthToken).filter(
        AuthToken.user_id == current_user["sub"],
        AuthToken.token_jti == request.session_id
    ).all()
    
    if not tokens:
        raise BusinessException(
            "会话不存在",
            ResponseCode.NOT_FOUND
        )
    
    for token in tokens:
        token.revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        token.revoke_reason = "用户主动终止会话"
        TokenBlacklist.add(token.token_jti)
    
    # 注意：事务将由FastAPI自动提交
    
    return {"message": "会话已终止"}


# ============= 权限检查 =============

@router.post("/permissions/check", summary="检查权限")
async def check_permission(
    request: PermissionCheckRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    检查用户是否有特定权限
    
    - **resource**: 资源标识（如 /api/v1/users）
    - **action**: 操作类型（如 GET, POST, PUT, DELETE）
    - **context**: 额外的上下文信息
    """
    # TODO: 实现权限检查逻辑
    # 这里应该检查用户的角色和权限
    
    return {
        "allowed": True,
        "reason": "用户有权限"
    }


# ============= 菜单管理 =============

@router.get("/admin/menus", response_model=MenuListResponse, summary="获取菜单列表")
async def get_menus(
    show_menu_only: bool = False,
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有菜单（树形结构）"""
    menu_tree = await menu_service.get_menu_tree(db, show_menu_only)
    return MenuListResponse(
        menus=menu_tree,
        total=len(menu_tree)
    )


@router.get("/admin/menus/parent-options", summary="获取父菜单选项")
async def get_parent_menu_options(db: AsyncSession = Depends(get_async_db)):
    """获取可作为父菜单的选项（树形结构）"""
    menus = await menu_service.get_all_menus(db)
    
    def build_tree_options(parent_id, level=0):
        children = []
        for menu in menus:
            if menu.parent_id == parent_id:
                children.append({
                    "value": menu.menu_id,
                    "label": f"{'  ' * level}{menu.menu_name}",
                    "title": menu.menu_name,
                    "children": build_tree_options(menu.menu_id, level + 1)
                })
        return children
    
    options = [
        {
            "value": -1,
            "label": "根菜单",
            "title": "根菜单",
            "children": build_tree_options(-1)
        }
    ]
    
    return {"options": options}


@router.post("/admin/menus", response_model=MenuResponse, summary="创建菜单")
async def create_menu(
    menu_data: MenuCreateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """创建新菜单"""
    menu = await menu_service.create_menu(
        db, 
        menu_data.dict(exclude_unset=True),
        creator="admin"
    )
    return MenuResponse(**menu.to_dict())


@router.get("/admin/menus/{menu_id}", response_model=MenuResponse, summary="获取菜单详情")
async def get_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定菜单详情"""
    menu = await menu_service.get_menu_by_id(db, menu_id)
    if not menu:
        raise BusinessException(
            f"菜单 {menu_id} 不存在",
            ResponseCode.NOT_FOUND
        )
    return MenuResponse(**menu.to_dict())


@router.put("/admin/menus/{menu_id}", response_model=MenuResponse, summary="更新菜单")
async def update_menu(
    menu_id: int,
    menu_data: MenuUpdateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """更新菜单"""
    menu = await menu_service.update_menu(
        db, 
        menu_id, 
        menu_data.dict(exclude_unset=True),
        updater="admin"
    )
    return MenuResponse(**menu.to_dict())


@router.delete("/admin/menus/{menu_id}", summary="删除菜单")
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """删除菜单"""
    await menu_service.delete_menu(db, menu_id)
    return {"message": f"菜单 {menu_id} 删除成功"}


@router.get("/me/menus", response_model=UserMenuResponse, summary="获取当前用户菜单")
async def get_user_menus(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户有权限的菜单树"""
    user_menus = await menu_service.get_user_menus(db, current_user["sub"])
    return UserMenuResponse(menus=user_menus)


@router.put("/admin/menus/{menu_id}/sort", summary="更新菜单排序")
async def update_menu_sort(
    menu_id: int,
    sort_order: int,
    db: AsyncSession = Depends(get_async_db)
):
    """更新菜单排序顺序"""
    menu = await menu_service.update_menu(
        db, 
        menu_id, 
        {"sort_order": sort_order}
    )
    return {"message": "排序更新成功"}


# ============= 初始化相关 =============

@router.post("/init/admin", summary="初始化管理员账户", include_in_schema=False)
async def init_admin(
    password: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    初始化管理员账户（仅在没有管理员时可用）
    """
    from src.apps.user.models import RbacUser
    from src.apps.auth.utils import PasswordUtils
    from sqlalchemy import select
    
    # 检查是否已有管理员
    stmt = select(RbacUser).where(RbacUser.user_name == "admin")
    result = await db.execute(stmt)
    admin_exists = result.scalar_one_or_none()
    
    if admin_exists:
        raise BusinessException(
            "管理员账户已存在",
            ResponseCode.BAD_REQUEST
        )
    
    # 创建管理员用户
    admin_user = RbacUser(
        user_id="admin",
        user_name="admin",
        display_name="系统管理员",
        department_name="系统",
        group_name="管理组",
        email="admin@example.com",
        mobile="13800138000",
        password_hash=PasswordUtils.hash_password(password),  # 直接存储密码
        user_source=2,  # JWT本地用户
        is_active=1,
        create_by="system",
        update_by="system"
    )
    db.add(admin_user)
    
    await db.commit()
    
    return {"message": "管理员账户创建成功"}


# ============= CAS会话管理 =============

@router.get("/cas/sessions/active", summary="获取用户活跃会话")
async def get_active_sessions(
    cas_session_id: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户的所有活跃CAS会话"""
    if not cas_session_id:
        raise BusinessException("需要CAS认证", ResponseCode.UNAUTHORIZED)
    
    from sqlalchemy import select
    from .models import AuthSession
    
    # 获取当前会话
    current_session = await db.execute(
        select(AuthSession).where(
            AuthSession.session_id == cas_session_id,
            AuthSession.is_active == True
        )
    )
    current = current_session.scalar_one_or_none()
    
    if not current:
        raise BusinessException("会话无效", ResponseCode.UNAUTHORIZED)
    
    # 获取用户所有会话
    stmt = select(AuthSession).where(
        AuthSession.user_id == current.user_id,
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
            "is_current": session.session_id == cas_session_id
        })
    
    return success_response({
        "sessions": session_list,
        "total": len(session_list)
    })