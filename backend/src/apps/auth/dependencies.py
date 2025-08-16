"""
认证相关的依赖项
用于FastAPI路由的认证和授权
"""

import os
import json
import traceback
import jwt
from datetime import datetime, timezone
from typing import Optional, List, Annotated
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.shared.db.config import get_async_db
from src.apps.auth.utils import JWTUtils, TokenBlacklist, APIKeyUtils, SECRET_KEY, ALGORITHM
from src.apps.auth.models import AuthToken, AuthApiKey
from src.apps.user.models import RbacUser, RbacUsersRoles, RbacRole
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode


# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[dict]:
    """
    获取当前用户（可选）
    支持四种认证方式：
    1. 中间件认证（优先）
    2. CAS Session认证（SSO用户）
    3. JWT Token认证（本地用户）  
    4. API Key认证（系统集成）
    """
    try:
        # 0. 优先从中间件获取（如果启用了认证中间件）
        if hasattr(request.state, "current_user"):
            return request.state.current_user
        # 1. 首先尝试CAS Session认证
        cas_session_id = request.cookies.get("cas_session_id")
        if cas_session_id:
            from src.apps.auth.models import AuthSession
            # 查询session
            stmt = select(AuthSession).where(
                AuthSession.session_id == cas_session_id,
                AuthSession.expires_at > datetime.now(timezone.utc)
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session and session.is_active:
                # 查询用户信息
                stmt = select(RbacUser).where(RbacUser.user_id == session.user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user and user.is_active:
                    return {
                        "sub": user.user_id,
                        "username": user.user_name,
                        "email": user.email,
                        "display_name": user.display_name,
                        "auth_type": "cas"
                    }
        
        # 2. 尝试Bearer Token认证
        if credentials:
            token = credentials.credentials
            
            # 检查是否是API Key（以omind_ak_开头）
            if token.startswith("omind_ak_"):
                # API Key认证
                key_hash = APIKeyUtils.hash_api_key(token)
                
                # 查询API Key记录
                stmt = select(AuthApiKey).where(
                    AuthApiKey.key_hash == key_hash,
                    AuthApiKey.is_active == 1,  # MySQL使用1表示True
                    AuthApiKey.revoked_at.is_(None)  # 未被撤销
                )
                result = await db.execute(stmt)
                api_key_record = result.scalar_one_or_none()
                
                if not api_key_record:
                    return None
                
                # 检查是否过期
                if api_key_record.expires_at and api_key_record.expires_at < datetime.now(timezone.utc):
                    return None
                
                # 检查IP白名单
                if api_key_record.allowed_ips:
                    allowed_ips = json.loads(api_key_record.allowed_ips)
                    client_ip = request.client.host if request.client else None
                    if allowed_ips and client_ip not in allowed_ips:
                        return None
                
                # 更新最后使用时间
                api_key_record.last_used_at = datetime.now(timezone.utc)
                # 注意：依赖项中的更新将由FastAPI的请求生命周期自动提交
                
                # 查询用户信息
                stmt = select(RbacUser).where(RbacUser.user_id == api_key_record.user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user and user.is_active:
                    # 获取权限范围
                    scopes = []
                    if api_key_record.scopes:
                        scopes = json.loads(api_key_record.scopes)
                    
                    return {
                        "sub": user.user_id,
                        "username": user.user_name,
                        "email": user.email,
                        "display_name": user.display_name,
                        "token_type": "api_key",
                        "api_key_name": api_key_record.key_name,
                        "scopes": scopes
                    }
            else:
                # 本地用户的JWT Token认证
                # 解码token
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                
                # 检查token是否在黑名单中
                jti = payload.get("jti")
                if jti and TokenBlacklist.is_blacklisted(jti):
                    return None
                
                # 验证token类型
                if payload.get("type") != "access":
                    return None
                
                # 查询用户是否存在且活跃
                stmt = select(RbacUser).where(RbacUser.user_id == payload.get("sub"))
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user and user.is_active:
                    return {
                        "sub": user.user_id,
                        "username": user.user_name,
                        "email": user.email,
                        "display_name": user.display_name,
                        "auth_type": "local"
                    }
        
            
    except Exception as e:
        # 认证失败时返回None而不是抛出异常，但打印错误用于调试
        print(f"认证异常: {e}")
        traceback.print_exc()
        pass
    
    return None


async def get_current_user(
    user: Optional[dict] = Depends(get_current_user_optional)
) -> dict:
    """
    获取当前用户（必需）
    如果未认证则抛出401错误
    
    🔧 开发模式：临时返回mock admin用户
    """
    # 🔧 临时Mock：开发模式下返回gaochao用户，跳过认证
    if os.getenv("AUTH_MOCK", "").lower() == "true":
        print("🔧 开发模式：使用Mock gaochao用户")
        return {
            "sub": "gaochao",
            "username": "gaochao", 
            "email": "gaochao@example.com",
            "display_name": "高超",
            "auth_type": "mock",
            "roles": ["admin"],  # 管理员权限
            "permissions": ["*"]  # 所有权限
        }
    
    # 原有的认证逻辑
    if not user:
        raise BusinessException(
            "未认证",
            ResponseCode.UNAUTHORIZED
        )
    
    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> RbacUser:
    """
    获取当前活跃用户的完整信息（包含角色和权限）
    """
    stmt = select(RbacUser).where(
        RbacUser.user_id == current_user["sub"],
        RbacUser.is_active == 1
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise BusinessException(
            "用户不存在或已禁用",
            ResponseCode.NOT_FOUND
        )
    
    return user


def require_auth(func):
    """
    装饰器：要求认证
    """
    async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    
    return wrapper


def require_roles(*required_roles: str):
    """
    依赖项工厂：要求特定角色
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        # 查询用户角色
        stmt = select(RbacRole).join(
            RbacUsersRoles, RbacUsersRoles.role_id == RbacRole.role_id
        ).where(
            RbacUsersRoles.user_id == current_user["sub"],
            RbacRole.is_active == 1
        )
        result = await db.execute(stmt)
        user_roles = result.scalars().all()
        
        # 检查是否有所需角色
        user_role_codes = {role.role_code for role in user_roles}
        if not user_role_codes.intersection(set(required_roles)):
            raise BusinessException(
                f"需要角色: {', '.join(required_roles)}",
                ResponseCode.FORBIDDEN
            )
        
        return True
    
    return role_checker


def require_permissions(*required_permissions: str):
    """
    依赖项工厂：要求特定权限
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user),
        request: Request = None,
        db: AsyncSession = Depends(get_async_db)
    ):
        from src.apps.user.models import RbacPermission, RbacRolesPermissions
        
        # 查询用户的所有权限（通过角色）
        stmt = select(RbacPermission).join(
            RbacRolesPermissions, RbacRolesPermissions.permission_id == RbacPermission.permission_id
        ).join(
            RbacRole, RbacRole.role_id == RbacRolesPermissions.role_id
        ).join(
            RbacUsersRoles, RbacUsersRoles.role_id == RbacRole.role_id
        ).where(
            RbacUsersRoles.user_id == current_user["sub"],
            RbacRole.is_active == 1,
            RbacPermission.is_active == 1
        )
        result = await db.execute(stmt)
        user_permissions = result.scalars().all()
        
        # 检查是否有所需权限
        user_permission_codes = {perm.permission_code for perm in user_permissions}
        missing_permissions = set(required_permissions) - user_permission_codes
        
        if missing_permissions:
            raise BusinessException(
                f"缺少权限: {', '.join(missing_permissions)}",
                ResponseCode.FORBIDDEN
            )
        
        return True
    
    return permission_checker


class RoleChecker:
    """角色检查器类"""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self, 
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        # 复用require_roles的逻辑
        checker = require_roles(*self.allowed_roles)
        return await checker(current_user, db)


class PermissionChecker:
    """权限检查器类"""
    def __init__(self, required_permission: str, check_method: bool = True):
        self.required_permission = required_permission
        self.check_method = check_method
    
    async def __call__(
        self,
        current_user: dict = Depends(get_current_user),
        request: Request = None,
        db: AsyncSession = Depends(get_async_db)
    ):
        # 如果需要检查HTTP方法，构造权限代码
        if self.check_method and request:
            permission_code = f"{request.method}:{self.required_permission}"
        else:
            permission_code = self.required_permission
            
        checker = require_permissions(permission_code)
        return await checker(current_user, request, db)


# 预定义的角色检查器
is_admin = RoleChecker(["admin"])
is_user = RoleChecker(["user", "admin"])


# 类型别名，方便使用
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentActiveUser = Annotated[RbacUser, Depends(get_current_active_user)]
OptionalUser = Annotated[Optional[dict], Depends(get_current_user_optional)]