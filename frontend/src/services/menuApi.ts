/**
 * 菜单 API 服务
 * 处理菜单数据的获取和权限验证
 */

import { MenuInfo, MenuApiResponse, UserMenuPermission } from '@/types/menu';
import { omind_get } from '@/utils/base_api';

export class MenuApiService {
  /**
   * 获取用户菜单权限
   * @param userId 用户ID，可选，默认获取当前用户
   */
  static async getUserMenus(userId?: string): Promise<UserMenuPermission> {
    try {
      const url = userId 
        ? `/api/v1/auth/admin/menus/user/${userId}`
        : `/api/v1/auth/me/menus`;
        
      const result = await omind_get(url);
      
      console.log('🔍 getUserMenus 原始响应:', result);
      
      // 后端直接返回 {menus: [...]} 格式，不是标准的 ApiResponse
      const menusData = result.menus || result.data || result;
      
      if (Array.isArray(menusData)) {
        // 扁平化嵌套的菜单数据
        const flattenedMenus = this.flattenNestedMenus(menusData);
        
        // 转换为菜单权限格式
        return this.transformToUserMenuPermission(flattenedMenus);
      } else {
        console.warn('菜单数据格式不正确:', result);
        throw new Error('菜单数据格式错误');
      }
    } catch (error) {
      console.error('Error fetching user menus:', error);
      // 返回空菜单
      return {
        menus: [],
        routes: [],
        permissions: []
      };
    }
  }

  /**
   * 扁平化嵌套的菜单数据
   */
  private static flattenNestedMenus(nestedMenus: any[]): MenuInfo[] {
    const result: MenuInfo[] = [];
    
    const flatten = (menus: any[]) => {
      menus.forEach(menu => {
        // 提取菜单信息（去掉children字段）
        const { children, ...menuInfo } = menu;
        result.push(menuInfo);
        
        // 递归处理子菜单
        if (children && Array.isArray(children)) {
          flatten(children);
        }
      });
    };
    
    flatten(nestedMenus);
    return result;
  }

  /**
   * 获取所有菜单（管理员用）
   */
  static async getAllMenus(): Promise<MenuInfo[]> {
    try {
      const result: MenuApiResponse = await omind_get('/api/v1/auth/admin/menus');
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to get all menus');
      }

      return result.data;
    } catch (error) {
      console.error('Error fetching all menus:', error);
      return [];
    }
  }

  /**
   * 将菜单数据转换为用户菜单权限格式
   */
  private static transformToUserMenuPermission(menus: MenuInfo[]): UserMenuPermission {
    // 过滤显示的菜单
    const visibleMenus = menus.filter(menu => menu.show_menu === 1);
    
    // 构建菜单树
    const menuTree = this.buildMenuTree(visibleMenus);
    
    // 生成路由配置
    const routes = this.generateRoutes(visibleMenus);
    
    // 提取权限列表
    const permissions = visibleMenus.map(menu => menu.route_path).filter(Boolean);

    return {
      menus: menuTree,
      routes,
      permissions,
    };
  }

  /**
   * 构建菜单树结构
   */
  private static buildMenuTree(menus: MenuInfo[]): import('../types/menu').MenuTreeNode[] {
    const menuMap = new Map<number, import('../types/menu').MenuTreeNode>();
    const rootMenus: import('../types/menu').MenuTreeNode[] = [];

    // 转换为 MenuTreeNode 并建立映射
    menus.forEach(menu => {
      const treeNode: import('../types/menu').MenuTreeNode = {
        ...menu,
        key: `menu-${menu.menu_id}`,
        level: 0,
        children: [],
      };
      menuMap.set(menu.menu_id, treeNode);
    });

    // 构建树结构
    menus.forEach(menu => {
      const currentNode = menuMap.get(menu.menu_id);
      if (!currentNode) return;

      if (menu.parent_id === -1) {
        // 根节点
        currentNode.level = 1;
        rootMenus.push(currentNode);
      } else {
        // 子节点
        const parentNode = menuMap.get(menu.parent_id);
        if (parentNode) {
          currentNode.level = parentNode.level + 1;
          if (!parentNode.children) {
            parentNode.children = [];
          }
          parentNode.children.push(currentNode);
        }
      }
    });

    // 排序菜单
    this.sortMenuTree(rootMenus);
    
    return rootMenus;
  }

  /**
   * 递归排序菜单树
   */
  private static sortMenuTree(menus: import('../types/menu').MenuTreeNode[]) {
    // 按 sort_order 排序，如果没有 sort_order 则默认为 0
    menus.sort((a, b) => {
      const aOrder = a.sort_order || 0;
      const bOrder = b.sort_order || 0;
      return aOrder - bOrder;
    });
    
    // 递归排序子菜单
    menus.forEach(menu => {
      if (menu.children && menu.children.length > 0) {
        this.sortMenuTree(menu.children);
      }
    });
  }

  /**
   * 生成路由配置
   */
  private static generateRoutes(menus: MenuInfo[]): import('../types/menu').MenuRoute[] {
    const routes: import('../types/menu').MenuRoute[] = [];
    
    menus.forEach(menu => {
      if (menu.route_path && menu.menu_component) {
        const route: import('../types/menu').MenuRoute = {
          path: menu.route_path,
          component: menu.menu_component,
          meta: {
            title: menu.menu_name,
            icon: menu.menu_icon,
            hideInMenu: menu.show_menu === 0,
          },
        };

        if (menu.redirect_path) {
          route.redirect = menu.redirect_path;
        }

        routes.push(route);
      }
    });

    return routes;
  }

}