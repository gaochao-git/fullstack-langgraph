"""
认证相关的API路由
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.apps.auth.service import AuthService
from src.apps.auth.sso_service import SSOService
from src.apps.auth.schemas import (
    LoginRequest, LoginResponse, RefreshTokenRequest, LogoutRequest,
    RegisterRequest, RegisterResponse,
    SSOLoginUrlResponse, SSOCallbackRequest,
    UserProfile, ChangePasswordRequest, ResetPasswordRequest, ForgotPasswordRequest,
    EnableMFARequest, EnableMFAResponse, VerifyMFARequest, DisableMFARequest,
    CreateAPIKeyRequest, CreateAPIKeyResponse, APIKeyInfo,
    SessionInfo, TerminateSessionRequest,
    TokenValidationResponse, PermissionCheckRequest
)
from src.apps.auth.dependencies import get_current_user, require_auth, require_roles


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
    
    - **username**: 用户名或邮箱
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
    - **password**: 密码（至少6个字符，需包含大小写字母和数字）
    - **email**: 邮箱地址
    - **display_name**: 显示名称
    """
    service = AuthService(db)
    
    # 添加请求信息
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent")
    
    return await service.register_user(request, ip_address, user_agent)


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
    return service.get_permission_tree(current_user["sub"])


@router.get("/me/menus", summary="获取当前用户菜单")
async def get_current_user_menus(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户可访问的菜单树"""
    from src.apps.auth.rbac_service import get_user_menu_tree
    
    return get_user_menu_tree(current_user["sub"], db)


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
    """创建新的API密钥"""
    service = AuthService(db)
    return await service.create_api_key(current_user["sub"], request)


@router.get("/api-keys", response_model=List[APIKeyInfo], summary="获取API密钥列表")
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """获取当前用户的API密钥列表"""
    from src.apps.auth.models import AuthApiKey
    
    keys = db.query(AuthApiKey).filter(
        AuthApiKey.user_id == current_user["sub"],
        AuthApiKey.is_active == True
    ).all()
    
    return [
        APIKeyInfo(
            id=key.id,
            key_name=key.key_name,
            key_prefix=key.key_prefix,
            scopes=json.loads(key.scopes) if key.scopes else [],
            is_active=key.is_active,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            created_at=key.create_time
        )
        for key in keys
    ]


@router.delete("/api-keys/{key_id}", summary="撤销API密钥")
async def revoke_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """撤销指定的API密钥"""
    from src.apps.auth.models import AuthApiKey
    from datetime import datetime, timezone
    
    key = db.query(AuthApiKey).filter(
        AuthApiKey.id == key_id,
        AuthApiKey.user_id == current_user["sub"]
    ).first()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    key.is_active = False
    key.revoked_at = datetime.now(timezone.utc)
    key.revoke_reason = "用户主动撤销"
    
    db.commit()
    
    return {"message": "API密钥已撤销"}


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    for token in tokens:
        token.revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        token.revoke_reason = "用户主动终止会话"
        TokenBlacklist.add(token.token_jti)
    
    db.commit()
    
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


# ============= 初始化相关 =============

@router.post("/init/admin", summary="初始化管理员账户", include_in_schema=False)
async def init_admin(
    password: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    初始化管理员账户（仅在没有管理员时可用）
    """
    from src.apps.user.rbac_models import RbacUser
    from src.apps.auth.models import AuthUser
    from src.apps.auth.utils import PasswordUtils
    
    # 检查是否已有管理员
    admin_exists = db.query(RbacUser).filter(
        RbacUser.user_name == "admin"
    ).first()
    
    if admin_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="管理员账户已存在"
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
        user_source=1,
        is_active=1,
        create_by="system",
        update_by="system"
    )
    db.add(admin_user)
    
    # 创建认证信息
    auth_user = AuthUser(
        user_id="admin",
        password_hash=PasswordUtils.hash_password(password)
    )
    db.add(auth_user)
    
    db.commit()
    
    return {"message": "管理员账户创建成功"}