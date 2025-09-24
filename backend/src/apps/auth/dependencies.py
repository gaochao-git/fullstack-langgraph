"""
认证相关的依赖项
用于FastAPI路由的认证和授权
"""

import os
from typing import Optional, List, Annotated
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.shared.db.config import get_async_db
from src.apps.user.models import RbacUser, RbacUsersRoles, RbacRole
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode


async def get_current_user_optional(
    request: Request
) -> Optional[dict]:
    """
    获取当前用户（可选）
    只从中间件认证结果中获取用户信息
    """
    # 从中间件获取认证信息
    return getattr(request.state, "current_user", None)


async def get_current_user(
    user: Optional[dict] = Depends(get_current_user_optional)
) -> dict:
    """
    获取当前用户（必需）
    如果未认证则抛出401错误
    """
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


# API密钥权限检查
async def check_api_key_permission(
    current_user: CurrentUser,
    required_permission_id: int
) -> bool:
    """
    检查API密钥是否有特定权限
    仅对API密钥认证有效
    """
    # 只对API密钥认证进行权限检查
    if current_user.get("auth_type") != "api_key":
        return True  # 其他认证方式默认通过
    
    # 获取API密钥的权限范围
    scopes = current_user.get("api_key_scopes", [])
    
    # 检查是否有所需权限
    return required_permission_id in scopes