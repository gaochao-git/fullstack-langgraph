"""
认证相关的依赖项
用于FastAPI路由的认证和授权
"""

from typing import Optional, List, Annotated
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.shared.db.config import get_async_db
from src.apps.auth.utils import JWTUtils, TokenBlacklist, APIKeyUtils
from src.apps.auth.models import AuthToken, AuthApiKey
from src.apps.user.rbac_models import RbacUser, RbacUsersRoles, RbacRole
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode


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
    from src.apps.auth.utils import SECRET_KEY, ALGORITHM
    import jwt
    
    try:
        # 优先尝试JWT认证
        if credentials:
            token = credentials.credentials
            
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
                    "token_type": "jwt"
                }
        
        # 尝试API Key认证
        if api_key:
            # TODO: 实现API Key认证逻辑
            pass
            
    except Exception as e:
        # 认证失败时返回None而不是抛出异常，但打印错误用于调试
        print(f"认证异常: {e}")
        import traceback
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
    import os
    if os.getenv("AUTH_MOCK", "").lower() == "true":
        print("🔧 开发模式：使用Mock gaochao用户")
        return {
            "sub": "gaochao",
            "username": "gaochao", 
            "email": "gaochao@example.com",
            "display_name": "高超",
            "token_type": "mock",
            "roles": ["super_admin"],  # 所有权限
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
    获取当前活跃用户的完整信息
    """
    # TODO: 实现异步查询
    raise BusinessException(
        "功能未实现",
        ResponseCode.NOT_IMPLEMENTED
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