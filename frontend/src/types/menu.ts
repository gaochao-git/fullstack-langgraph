/**
 * 菜单系统类型定义
 * 基于 rbac_menus 表结构
 */

export interface MenuInfo {
  id: number;
  menu_id: number;
  menu_name: string;
  menu_icon: string;
  parent_id: number;
  route_path: string;
  redirect_path: string;
  menu_component: string;
  show_menu: number; // 0: 隐藏, 1: 显示
  sort_order?: number; // 排序顺序
  create_time: string;
  update_time: string;
  create_by: string;
  update_by: string;
}

export interface MenuTreeNode extends MenuInfo {
  children?: MenuTreeNode[];
  key: string; // 用于 Ant Design Menu 组件
  level: number; // 菜单层级
}

export interface MenuRoute {
  path: string;
  component: string;
  redirect?: string;
  meta: {
    title: string;
    icon?: string;
    activeMenu?: string;
    hideInMenu?: boolean;
    keepAlive?: boolean;
  };
  children?: MenuRoute[];
}

// 当前用户的菜单权限
export interface UserMenuPermission {
  menus: MenuTreeNode[];
  routes: MenuRoute[];
  permissions: string[]; // 权限码列表
}

// API 响应类型
export interface MenuApiResponse {
  success: boolean;
  data: MenuInfo[];
  message?: string;
}