// RBAC API服务

import { omind_get, omind_post, omind_put, omind_del } from '@/utils/base_api';
import type {
  RbacUser, RbacRole, RbacPermission, RbacMenu,
  UserCreateRequest, UserUpdateRequest, UserQueryParams,
  RoleCreateRequest, RoleUpdateRequest, RoleQueryParams,
  PermissionCreateRequest, PermissionUpdateRequest, PermissionQueryParams,
  MenuCreateRequest, MenuUpdateRequest, MenuQueryParams,
  PaginatedResponse
} from '../types/rbac';

const API_PREFIX = '/api/v1/rbac';

// 统一响应处理函数
function handleUnifiedResponse<T>(response: any): T {
  if (response.status === 'ok') {
    return response.data;
  } else {
    throw new Error(response.msg || '请求失败');
  }
}

// ============ 用户管理API ============

export const userApi = {
  // 创建用户
  createUser: async (data: UserCreateRequest): Promise<RbacUser> => {
    const result = await omind_post(`${API_PREFIX}/users`, data);
    return handleUnifiedResponse<RbacUser>(result);
  },

  // 获取用户详情
  getUser: async (userId: string): Promise<RbacUser> => {
    const result = await omind_get(`${API_PREFIX}/users/${userId}`);
    return handleUnifiedResponse<RbacUser>(result);
  },

  // 用户列表查询
  listUsers: async (params: UserQueryParams): Promise<PaginatedResponse<RbacUser>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const url = `${API_PREFIX}/users?${searchParams.toString()}`;
    const result = await omind_get(url);
    return handleUnifiedResponse<PaginatedResponse<RbacUser>>(result);
  },

  // 更新用户
  updateUser: async (userId: string, data: UserUpdateRequest): Promise<RbacUser> => {
    const result = await omind_put(`${API_PREFIX}/users/${userId}`, data);
    return handleUnifiedResponse<RbacUser>(result);
  },

  // 删除用户
  deleteUser: async (userId: string): Promise<{ deleted_user_id: string }> => {
    const result = await omind_del(`${API_PREFIX}/users/${userId}`);
    return handleUnifiedResponse<{ deleted_user_id: string }>(result);
  },
};

// ============ 角色管理API ============

export const roleApi = {
  // 创建角色
  createRole: async (data: RoleCreateRequest): Promise<RbacRole> => {
    const result = await omind_post(`${API_PREFIX}/roles`, data);
    return handleUnifiedResponse<RbacRole>(result);
  },

  // 获取角色详情
  getRole: async (roleId: number): Promise<RbacRole> => {
    const result = await omind_get(`${API_PREFIX}/roles/${roleId}`);
    return handleUnifiedResponse<RbacRole>(result);
  },

  // 角色列表查询
  listRoles: async (params: RoleQueryParams): Promise<PaginatedResponse<RbacRole>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const url = `${API_PREFIX}/roles?${searchParams.toString()}`;
    const result = await omind_get(url);
    return handleUnifiedResponse<PaginatedResponse<RbacRole>>(result);
  },

  // 更新角色
  updateRole: async (roleId: number, data: RoleUpdateRequest): Promise<RbacRole> => {
    const result = await omind_put(`${API_PREFIX}/roles/${roleId}`, data);
    return handleUnifiedResponse<RbacRole>(result);
  },

  // 删除角色
  deleteRole: async (roleId: number): Promise<{ deleted_role_id: number }> => {
    const result = await omind_del(`${API_PREFIX}/roles/${roleId}`);
    return handleUnifiedResponse<{ deleted_role_id: number }>(result);
  },

  // 获取角色权限
  getRolePermissions: async (roleId: number): Promise<{ api_permission_ids: number[], menu_ids: number[] }> => {
    const result = await omind_get(`${API_PREFIX}/roles/${roleId}/permissions`);
    return handleUnifiedResponse<{ api_permission_ids: number[], menu_ids: number[] }>(result);
  },
};

// ============ 权限管理API ============

export const permissionApi = {
  // 创建权限
  createPermission: async (data: PermissionCreateRequest): Promise<RbacPermission> => {
    const result = await omind_post(`${API_PREFIX}/permissions`, data);
    return handleUnifiedResponse<RbacPermission>(result);
  },

  // 获取权限详情
  getPermission: async (permissionId: number): Promise<RbacPermission> => {
    const result = await omind_get(`${API_PREFIX}/permissions/${permissionId}`);
    return handleUnifiedResponse<RbacPermission>(result);
  },

  // 权限列表查询
  listPermissions: async (params: PermissionQueryParams): Promise<PaginatedResponse<RbacPermission>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const url = `${API_PREFIX}/permissions?${searchParams.toString()}`;
    const result = await omind_get(url);
    return handleUnifiedResponse<PaginatedResponse<RbacPermission>>(result);
  },

  // 更新权限
  updatePermission: async (permissionId: number, data: PermissionUpdateRequest): Promise<RbacPermission> => {
    const result = await omind_put(`${API_PREFIX}/permissions/${permissionId}`, data);
    return handleUnifiedResponse<RbacPermission>(result);
  },

  // 删除权限
  deletePermission: async (permissionId: number): Promise<{ deleted_permission_id: number }> => {
    const result = await omind_del(`${API_PREFIX}/permissions/${permissionId}`);
    return handleUnifiedResponse<{ deleted_permission_id: number }>(result);
  },

  // 扫描API权限
  scanPermissions: async (): Promise<{ added: number; skipped: number; updated: number }> => {
    const result = await omind_post(`${API_PREFIX}/permissions/scan`, {});
    return handleUnifiedResponse<{ added: number; skipped: number; updated: number }>(result);
  },
};

// ============ 菜单管理API ============

export const menuApi = {
  // 创建菜单
  createMenu: async (data: MenuCreateRequest): Promise<RbacMenu> => {
    const result = await omind_post(`${API_PREFIX}/menus`, data);
    return handleUnifiedResponse<RbacMenu>(result);
  },

  // 获取菜单详情
  getMenu: async (menuId: number): Promise<RbacMenu> => {
    const result = await omind_get(`${API_PREFIX}/menus/${menuId}`);
    return handleUnifiedResponse<RbacMenu>(result);
  },

  // 菜单列表查询
  listMenus: async (params: MenuQueryParams): Promise<PaginatedResponse<RbacMenu>> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const url = `${API_PREFIX}/menus?${searchParams.toString()}`;
    const result = await omind_get(url);
    return handleUnifiedResponse<PaginatedResponse<RbacMenu>>(result);
  },

  // 更新菜单
  updateMenu: async (menuId: number, data: MenuUpdateRequest): Promise<RbacMenu> => {
    const result = await omind_put(`${API_PREFIX}/menus/${menuId}`, data);
    return handleUnifiedResponse<RbacMenu>(result);
  },

  // 删除菜单
  deleteMenu: async (menuId: number): Promise<{ deleted_menu_id: number }> => {
    const result = await omind_del(`${API_PREFIX}/menus/${menuId}`);
    return handleUnifiedResponse<{ deleted_menu_id: number }>(result);
  },
};