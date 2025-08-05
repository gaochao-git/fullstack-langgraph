"""RBAC API端点 - 用户权限管理"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.apps.user.rbac_schema import (
    UserCreateRequest, UserUpdateRequest, UserQueryParams, UserResponse,
    RoleCreateRequest, RoleUpdateRequest, RoleQueryParams, RoleResponse,
    PermissionCreateRequest, PermissionUpdateRequest, PermissionQueryParams, PermissionResponse,
    MenuCreateRequest, MenuUpdateRequest, MenuQueryParams, MenuResponse,
    UserRoleCreateRequest, RolePermissionCreateRequest,
    ApiResponse
)
from src.apps.user.service.rbac_service import (
    rbac_user_service, rbac_role_service, rbac_permission_service, rbac_menu_service
)
from src.apps.user.rbac_models import RbacRolesPermissions, RbacUsersRoles
from src.shared.core.logging import get_logger
from src.shared.schemas.response import (UnifiedResponse, success_response, paginated_response, ResponseCode)
from src.shared.core.exceptions import BusinessException

logger = get_logger(__name__)

# 创建路由器
user_router = APIRouter(prefix="/rbac/users", tags=["RBAC用户管理"])
role_router = APIRouter(prefix="/rbac/roles", tags=["RBAC角色管理"])
permission_router = APIRouter(prefix="/rbac/permissions", tags=["RBAC权限管理"])
menu_router = APIRouter(prefix="/rbac/menus", tags=["RBAC菜单管理"])


# ============ 用户管理接口 ============

@user_router.post("", response_model=UnifiedResponse)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """创建用户"""
    user = await rbac_user_service.create_user(db, user_data)
    return success_response(
        data=user.to_dict(),
        msg="用户创建成功",
        code=ResponseCode.CREATED
    )


@user_router.get("/{user_id}", response_model=UnifiedResponse)
async def get_user(
    user_id: str = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取用户详情"""
    user = await rbac_user_service.get_user_by_id(db, user_id)
    if not user:
        raise BusinessException(f"用户 {user_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=user.to_dict(),
        msg="获取用户成功"
    )


@user_router.get("", response_model=UnifiedResponse)
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页大小"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    is_active: Optional[int] = Query(None, description="激活状态: 1激活 0禁用"),
    department_name: Optional[str] = Query(None, description="部门筛选"),
    group_name: Optional[str] = Query(None, description="组筛选"),
    user_source: Optional[int] = Query(None, description="用户来源筛选"),
    db: AsyncSession = Depends(get_async_db)
):
    """用户列表查询"""
    params = UserQueryParams(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        department_name=department_name,
        group_name=group_name,
        user_source=user_source
    )
    
    users, total = await rbac_user_service.list_users(db, params)
    
    # 转换为字典格式
    from src.shared.db.models import BaseModel
    user_data = BaseModel.bulk_to_dict(users)
    
    return paginated_response(
        items=user_data,
        total=total,
        page=page,
        size=page_size,
        msg="查询用户列表成功"
    )


@user_router.put("/{user_id}", response_model=UnifiedResponse)
async def update_user(
    user_id: str = Path(..., description="用户ID"),
    user_data: UserUpdateRequest = None,
    db: AsyncSession = Depends(get_async_db)
):
    """更新用户"""
    updated_user = await rbac_user_service.update_user(db, user_id, user_data)
    if not updated_user:
        raise BusinessException(f"用户 {user_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_user.to_dict(),
        msg="用户更新成功"
    )


@user_router.delete("/{user_id}", response_model=UnifiedResponse)
async def delete_user(
    user_id: str = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """删除用户"""
    success = await rbac_user_service.delete_user(db, user_id)
    if not success:
        raise BusinessException(f"用户 {user_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_user_id": user_id},
        msg="用户删除成功"
    )


# ============ 角色管理接口 ============

@role_router.post("", response_model=UnifiedResponse)
async def create_role(
    role_data: RoleCreateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """创建角色"""
    role = await rbac_role_service.create_role(db, role_data)
    return success_response(
        data=role.to_dict(),
        msg="角色创建成功",
        code=ResponseCode.CREATED
    )


@role_router.get("/{role_id}", response_model=UnifiedResponse)
async def get_role(
    role_id: int = Path(..., description="角色ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取角色详情"""
    role = await rbac_role_service.get_role_by_id(db, role_id)
    if not role:
        raise BusinessException(f"角色 {role_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=role.to_dict(),
        msg="获取角色成功"
    )


@role_router.get("", response_model=UnifiedResponse)
async def list_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页大小"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    role_id: Optional[int] = Query(None, description="角色ID筛选"),
    db: AsyncSession = Depends(get_async_db)
):
    """角色列表查询"""
    params = RoleQueryParams(
        page=page,
        page_size=page_size,
        search=search,
        role_id=role_id
    )
    
    roles, total = await rbac_role_service.list_roles(db, params)
    
    # 转换为字典格式
    from src.shared.db.models import BaseModel
    role_data = BaseModel.bulk_to_dict(roles)
    
    return paginated_response(
        items=role_data,
        total=total,
        page=page,
        size=page_size,
        msg="查询角色列表成功"
    )


@role_router.put("/{role_id}", response_model=UnifiedResponse)
async def update_role(
    role_id: int = Path(..., description="角色ID"),
    role_data: RoleUpdateRequest = None,
    db: AsyncSession = Depends(get_async_db)
):
    """更新角色"""
    updated_role = await rbac_role_service.update_role(db, role_id, role_data)
    if not updated_role:
        raise BusinessException(f"角色 {role_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_role.to_dict(),
        msg="角色更新成功"
    )


@role_router.delete("/{role_id}", response_model=UnifiedResponse)
async def delete_role(
    role_id: int = Path(..., description="角色ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """删除角色"""
    success = await rbac_role_service.delete_role(db, role_id)
    if not success:
        raise BusinessException(f"角色 {role_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_role_id": role_id},
        msg="角色删除成功"
    )


@role_router.get("/{role_id}/permissions", response_model=UnifiedResponse)
async def get_role_permissions(
    role_id: int = Path(..., description="角色ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取角色的权限和菜单"""
    role = await rbac_role_service.get_role_by_id(db, role_id)
    if not role:
        raise BusinessException(f"角色 {role_id} 不存在", ResponseCode.NOT_FOUND)
    
    permissions_data = await rbac_role_service.get_role_permissions_and_menus(db, role_id)
    
    return success_response(
        data=permissions_data,
        msg="获取角色权限成功"
    )



# ============ 权限管理接口 ============

@permission_router.post("", response_model=UnifiedResponse)
async def create_permission(
    permission_data: PermissionCreateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """创建权限"""
    permission = await rbac_permission_service.create_permission(db, permission_data)
    return success_response(
        data=permission.to_dict(),
        msg="权限创建成功",
        code=ResponseCode.CREATED
    )


@permission_router.get("/{permission_id}", response_model=UnifiedResponse)
async def get_permission(
    permission_id: int = Path(..., description="权限ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取权限详情"""
    permission = await rbac_permission_service.get_permission_by_id(db, permission_id)
    if not permission:
        raise BusinessException(f"权限 {permission_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=permission.to_dict(),
        msg="获取权限成功"
    )


@permission_router.get("", response_model=UnifiedResponse)
async def list_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页大小"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    permission_id: Optional[int] = Query(None, description="权限ID筛选"),
    release_disable: Optional[str] = Query(None, description="发布状态筛选"),
    db: AsyncSession = Depends(get_async_db)
):
    """权限列表查询"""
    params = PermissionQueryParams(
        page=page,
        page_size=page_size,
        search=search,
        permission_id=permission_id,
        release_disable=release_disable
    )
    
    permissions, total = await rbac_permission_service.list_permissions(db, params)
    
    # 转换为字典格式
    from src.shared.db.models import BaseModel
    permission_data = BaseModel.bulk_to_dict(permissions)
    
    return paginated_response(
        items=permission_data,
        total=total,
        page=page,
        size=page_size,
        msg="查询权限列表成功"
    )


@permission_router.put("/{permission_id}", response_model=UnifiedResponse)
async def update_permission(
    permission_id: int = Path(..., description="权限ID"),
    permission_data: PermissionUpdateRequest = None,
    db: AsyncSession = Depends(get_async_db)
):
    """更新权限"""
    updated_permission = await rbac_permission_service.update_permission(db, permission_id, permission_data)
    if not updated_permission:
        raise BusinessException(f"权限 {permission_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_permission.to_dict(),
        msg="权限更新成功"
    )


@permission_router.delete("/{permission_id}", response_model=UnifiedResponse)
async def delete_permission(
    permission_id: int = Path(..., description="权限ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """删除权限"""
    success = await rbac_permission_service.delete_permission(db, permission_id)
    if not success:
        raise BusinessException(f"权限 {permission_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_permission_id": permission_id},
        msg="权限删除成功"
    )


# ============ 菜单管理接口 ============

@menu_router.post("", response_model=UnifiedResponse)
async def create_menu(
    menu_data: MenuCreateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """创建菜单"""
    menu = await rbac_menu_service.create_menu(db, menu_data)
    return success_response(
        data=menu.to_dict(),
        msg="菜单创建成功",
        code=ResponseCode.CREATED
    )


@menu_router.get("/{menu_id}", response_model=UnifiedResponse)
async def get_menu(
    menu_id: int = Path(..., description="菜单ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取菜单详情"""
    menu = await rbac_menu_service.get_menu_by_id(db, menu_id)
    if not menu:
        raise BusinessException(f"菜单 {menu_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=menu.to_dict(),
        msg="获取菜单成功"
    )


@menu_router.get("", response_model=UnifiedResponse)
async def list_menus(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页大小"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    parent_id: Optional[int] = Query(None, description="父菜单筛选"),
    show_menu: Optional[int] = Query(None, description="显示状态筛选: 1显示 0隐藏"),
    menu_id: Optional[int] = Query(None, description="菜单ID筛选"),
    db: AsyncSession = Depends(get_async_db)
):
    """菜单列表查询"""
    params = MenuQueryParams(
        page=page,
        page_size=page_size,
        search=search,
        parent_id=parent_id,
        show_menu=show_menu,
        menu_id=menu_id
    )
    
    menus, total = await rbac_menu_service.list_menus(db, params)
    
    # 转换为字典格式
    from src.shared.db.models import BaseModel
    menu_data = BaseModel.bulk_to_dict(menus)
    
    return paginated_response(
        items=menu_data,
        total=total,
        page=page,
        size=page_size,
        msg="查询菜单列表成功"
    )


@menu_router.put("/{menu_id}", response_model=UnifiedResponse)
async def update_menu(
    menu_id: int = Path(..., description="菜单ID"),
    menu_data: MenuUpdateRequest = None,
    db: AsyncSession = Depends(get_async_db)
):
    """更新菜单"""
    updated_menu = await rbac_menu_service.update_menu(db, menu_id, menu_data)
    if not updated_menu:
        raise BusinessException(f"菜单 {menu_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_menu.to_dict(),
        msg="菜单更新成功"
    )


@menu_router.delete("/{menu_id}", response_model=UnifiedResponse)
async def delete_menu(
    menu_id: int = Path(..., description="菜单ID"),
    db: AsyncSession = Depends(get_async_db)
):
    """删除菜单"""
    success = await rbac_menu_service.delete_menu(db, menu_id)
    if not success:
        raise BusinessException(f"菜单 {menu_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_menu_id": menu_id},
        msg="菜单删除成功"
    )


# 合并所有路由器
rbac_router = APIRouter(prefix="/v1")
rbac_router.include_router(user_router)
rbac_router.include_router(role_router)
rbac_router.include_router(permission_router)
rbac_router.include_router(menu_router)