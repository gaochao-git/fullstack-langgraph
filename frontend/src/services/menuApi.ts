/**
 * 菜单 API 服务
 * 处理菜单数据的获取和权限验证
 */

import { MenuInfo, MenuApiResponse, UserMenuPermission } from '../types/menu';
import { defaultMenusData } from '../data/defaultMenus';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class MenuApiService {
  /**
   * 获取用户菜单权限
   * @param userId 用户ID，可选，默认获取当前用户
   */
  static async getUserMenus(userId?: string): Promise<UserMenuPermission> {
    try {
      const url = userId 
        ? `${API_BASE_URL}/api/v1/menus/user/${userId}`
        : `${API_BASE_URL}/api/v1/menus/current-user`;
        
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // TODO: 添加认证头
          // 'Authorization': `Bearer ${getToken()}`
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user menus');
      }

      const result: MenuApiResponse = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Failed to get menu data');
      }

      // 转换为菜单权限格式
      return this.transformToUserMenuPermission(result.data);
    } catch (error) {
      console.error('Error fetching user menus:', error);
      // 返回默认菜单或空菜单
      return this.getDefaultMenus();
    }
  }

  /**
   * 获取所有菜单（管理员用）
   */
  static async getAllMenus(): Promise<MenuInfo[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/menus`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result: MenuApiResponse = await response.json();
      
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

      if (menu.parent_id === 0) {
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
    menus.sort((a, b) => a.menu_id - b.menu_id);
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

  /**
   * 获取默认菜单（当API失败时的备用方案）
   */
  private static getDefaultMenus(): UserMenuPermission {
    // 基于你当前的菜单结构，创建默认菜单
    const defaultMenuData: MenuInfo[] = [
      {
        id: 1,
        menu_id: 1,
        menu_name: '用户服务',
        menu_icon: 'CustomerServiceOutlined',
        parent_id: 0,
        route_path: '/user-service',
        redirect_path: '/',
        menu_component: '',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
      {
        id: 2,
        menu_id: 2,
        menu_name: '智能体广场',
        menu_icon: 'AppstoreOutlined',
        parent_id: 1,
        route_path: '/',
        redirect_path: '',
        menu_component: 'AgentMarketplace',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
      {
        id: 3,
        menu_id: 3,
        menu_name: '知识中心',
        menu_icon: 'BookOutlined',
        parent_id: 1,
        route_path: '/knowledge',
        redirect_path: '',
        menu_component: 'KnowledgeManagement',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
      {
        id: 4,
        menu_id: 4,
        menu_name: '系统管理',
        menu_icon: 'SettingOutlined',
        parent_id: 0,
        route_path: '/system',
        redirect_path: '/agents',
        menu_component: '',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
      {
        id: 5,
        menu_id: 5,
        menu_name: '智能体管理',
        menu_icon: 'UserOutlined',
        parent_id: 4,
        route_path: '/agents',
        redirect_path: '',
        menu_component: 'AgentManagement',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
      {
        id: 6,
        menu_id: 6,
        menu_name: 'SOP管理',
        menu_icon: 'FileTextOutlined',
        parent_id: 4,
        route_path: '/sop',
        redirect_path: '',
        menu_component: 'SOPManagement',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
      {
        id: 7,
        menu_id: 7,
        menu_name: 'MCP管理',
        menu_icon: 'LinkOutlined',
        parent_id: 4,
        route_path: '/mcp',
        redirect_path: '',
        menu_component: 'MCPManagement',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
      {
        id: 8,
        menu_id: 8,
        menu_name: '模型管理',
        menu_icon: 'ApiOutlined',
        parent_id: 4,
        route_path: '/models',
        redirect_path: '',
        menu_component: 'ModelsManagement',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
      {
        id: 9,
        menu_id: 9,
        menu_name: '任务管理',
        menu_icon: 'ClockCircleOutlined',
        parent_id: 4,
        route_path: '/tasks',
        redirect_path: '',
        menu_component: 'TasksManagement',
        show_menu: 1,
        create_time: '',
        update_time: '',
        create_by: 'system',
        update_by: 'system',
      },
    ];

    return this.transformToUserMenuPermission(defaultMenuData);
  }
}