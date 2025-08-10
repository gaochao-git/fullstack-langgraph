// RBAC用户权限管理系统统一导出

// 页面组件
export { UserManagement } from './pages/UserManagement';
export { RoleManagement } from './pages/RoleManagement';
export { PermissionManagement } from './pages/PermissionManagement';
export { MenuManagement } from './pages/MenuManagement';
export { APIKeyManagement } from './APIKeyManagement';

// API服务
export { userApi, roleApi, permissionApi, menuApi } from './services/rbacApi';

// 类型定义
export type {
  RbacUser, RbacRole, RbacPermission, RbacMenu,
  UserCreateRequest, UserUpdateRequest, UserQueryParams,
  RoleCreateRequest, RoleUpdateRequest, RoleQueryParams,
  PermissionCreateRequest, PermissionUpdateRequest, PermissionQueryParams,
  MenuCreateRequest, MenuUpdateRequest, MenuQueryParams,
  ApiResponse, PaginatedResponse
} from './types/rbac';