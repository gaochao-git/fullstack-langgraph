// RBAC相关类型定义

export interface RbacUser {
  id: number;
  user_id: string;
  user_name: string;
  display_name: string;
  department_name: string;
  group_name: string;
  email: string;
  mobile: string;
  user_source: number;
  is_active: number;
  create_time: string;
  update_time: string;
  create_by: string;
  update_by: string;
  roles?: RbacRole[];
}

export interface RbacRole {
  id: number;
  role_id: number;
  role_name: string;
  description: string;
  create_time: string;
  update_time: string;
  create_by: string;
  update_by: string;
  permission_count?: number;
  user_count?: number;
  permissions?: RbacPermission[];
}

export interface RbacPermission {
  id: number;
  permission_id: number;
  permission_description: string;
  permission_name: string;
  http_method: string;
  release_disable: string;
  permission_allow_client?: string;
  is_deleted: number;
  create_time: string;
  update_time: string;
  create_by: string;
  update_by: string;
}

export interface RbacMenu {
  id: number;
  menu_id: number;
  menu_name: string;
  menu_icon: string;
  parent_id: number;
  route_path: string;
  redirect_path: string;
  menu_component: string;
  show_menu: number;
  create_time: string;
  update_time: string;
  create_by: string;
  update_by: string;
}

export interface UserCreateRequest {
  user_id: string;
  user_name: string;
  display_name: string;
  department_name: string;
  group_name: string;
  email: string;
  mobile: string;
  user_source?: number;
  is_active?: number;
  role_ids?: number[];
  password?: string;
  auth_type?: string;
}

export interface UserUpdateRequest {
  user_name?: string;
  display_name?: string;
  department_name?: string;
  group_name?: string;
  email?: string;
  mobile?: string;
  user_source?: number;
  is_active?: number;
  role_ids?: number[];
}

export interface RoleCreateRequest {
  role_id: number;
  role_name: string;
  description: string;
  permission_ids?: number[];
  menu_ids?: number[];
}

export interface RoleUpdateRequest {
  role_name?: string;
  description?: string;
  permission_ids?: number[];
  menu_ids?: number[];
}

export interface PermissionCreateRequest {
  permission_id: number;
  permission_description: string;
  permission_name: string;
  http_method?: string;
  release_disable?: string;
  permission_allow_client?: string;
}

export interface PermissionUpdateRequest {
  permission_description?: string;
  permission_name?: string;
  http_method?: string;
  release_disable?: string;
  permission_allow_client?: string;
}

export interface MenuCreateRequest {
  menu_id: number;
  menu_name: string;
  menu_icon: string;
  parent_id?: number;
  route_path: string;
  redirect_path: string;
  menu_component: string;
  show_menu?: number;
}

export interface MenuUpdateRequest {
  menu_name?: string;
  menu_icon?: string;
  parent_id?: number;
  route_path?: string;
  redirect_path?: string;
  menu_component?: string;
  show_menu?: number;
}

export interface PaginationParams {
  page: number;
  page_size: number;
  search?: string;
}

export interface UserQueryParams extends PaginationParams {
  is_active?: number;
  department_name?: string;
  group_name?: string;
  user_source?: number;
}

export interface RoleQueryParams extends PaginationParams {
  role_id?: number;
}

export interface PermissionQueryParams extends PaginationParams {
  permission_id?: number;
  release_disable?: string;
  http_method?: string;
}

export interface MenuQueryParams extends PaginationParams {
  parent_id?: number;
  show_menu?: number;
  menu_id?: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  pagination: {
    page: number;
    size: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}