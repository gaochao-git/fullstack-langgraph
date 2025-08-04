"""
认证相关的依赖项
用于FastAPI路由的认证和授权
"""

from typing import Optional, List, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.shared.db.config import get_async_db
from src.apps.auth.utils import JWTUtils, TokenBlacklist, APIKeyUtils
from src.apps.auth.models import AuthToken, AuthApiKey
from src.apps.user.rbac_models import RbacUser, RbacUsersRoles, RbacRole


# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[dict]:
    """
    获取当前用户（可选）
    支持JWT Token和API Key两种认证方式
    """
    try:
        # 优先尝试JWT认证
        if credentials:
            token = credentials.credentials
            
            # 检查token是否在黑名单中
            jti = JWTUtils.get_jti(token)
            if jti and TokenBlacklist.is_blacklisted(jti):
                return None
            
            # 解码token
            payload = JWTUtils.decode_token(token)
            
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
                    "token_type": "jwt"
                }
        
        # 尝试API Key认证
        if api_key:
            # TODO: 实现API Key认证逻辑
            pass
            
    except Exception:
        # 认证失败时返回None而不是抛出异常
        pass
    
    return None


async def get_current_user(
    user: Optional[dict] = Depends(get_current_user_optional)
) -> dict:
    """
    获取当前用户（必需）
    如果未认证则抛出401错误
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> RbacUser:
    """
    获取当前活跃用户的完整信息
    """
    # TODO: 实现异步查询
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能未实现"
    )


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
    暂时简化实现
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        # TODO: 实现角色检查
        return True
    
    return role_checker


def require_permissions(*required_permissions: str):
    """
    依赖项工厂：要求特定权限
    暂时简化实现
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user),
        request: Request = None,
        db: AsyncSession = Depends(get_async_db)
    ):
        # TODO: 实现权限检查
        return True
    
    return permission_checker


# 简化的类实现，先保证能启动
class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: dict = Depends(get_current_user)):
        # TODO: 实现角色检查
        return True


class PermissionChecker:
    def __init__(self, required_permission: str, check_method: bool = True):
        self.required_permission = required_permission
        self.check_method = check_method
    
    def __call__(self, current_user: dict = Depends(get_current_user)):
        # TODO: 实现权限检查
        return True


# 预定义的角色检查器
is_admin = RoleChecker(["admin", "super_admin"])
is_user = RoleChecker(["user", "admin", "super_admin"])


# 类型别名，方便使用
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentActiveUser = Annotated[RbacUser, Depends(get_current_active_user)]
OptionalUser = Annotated[Optional[dict], Depends(get_current_user_optional)]


# 导入json（在使用前）
import json