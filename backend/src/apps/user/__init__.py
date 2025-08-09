"""
User Management Module
用户管理模块
"""

from .endpoints import router
from .models import (
    User, UserThread, 
    RbacUser, RbacRole, RbacPermission, RbacMenu,
    RbacUsersRoles, RbacRolesPermissions
)
from .schema import (
    UserCreateRequest, UserUpdateRequest, UserResponse, UserListResponse, UserQueryParams,
    RoleCreateRequest, RoleUpdateRequest, RoleResponse, RoleListResponse, RoleQueryParams,
    PermissionCreateRequest, PermissionUpdateRequest, PermissionResponse, PermissionListResponse, PermissionQueryParams,
    MenuCreateRequest, MenuUpdateRequest, MenuResponse, MenuListResponse, MenuQueryParams,
    UserRoleCreateRequest, UserRoleResponse,
    RolePermissionCreateRequest, RolePermissionResponse
)
from .service.user_service import (
    rbac_user_service, rbac_role_service, 
    rbac_permission_service, rbac_menu_service
)

__all__ = [
    # Router
    'router',
    
    # Models
    'User', 'UserThread',
    'RbacUser', 'RbacRole', 'RbacPermission', 'RbacMenu',
    'RbacUsersRoles', 'RbacRolesPermissions',
    
    # Schemas
    'UserCreateRequest', 'UserUpdateRequest', 'UserResponse', 'UserListResponse', 'UserQueryParams',
    'RoleCreateRequest', 'RoleUpdateRequest', 'RoleResponse', 'RoleListResponse', 'RoleQueryParams',
    'PermissionCreateRequest', 'PermissionUpdateRequest', 'PermissionResponse', 'PermissionListResponse', 'PermissionQueryParams',
    'MenuCreateRequest', 'MenuUpdateRequest', 'MenuResponse', 'MenuListResponse', 'MenuQueryParams',
    'UserRoleCreateRequest', 'UserRoleResponse',
    'RolePermissionCreateRequest', 'RolePermissionResponse',
    
    # Services
    'rbac_user_service', 'rbac_role_service', 
    'rbac_permission_service', 'rbac_menu_service'
]