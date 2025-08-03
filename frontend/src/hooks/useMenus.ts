/**
 * 菜单状态管理 Hook
 * 处理菜单数据获取、缓存和状态管理
 */

import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { MenuTreeNode, UserMenuPermission } from '../types/menu';
import { MenuApiService } from '../services/menuApi';

interface UseMenusReturn {
  menus: MenuTreeNode[];
  loading: boolean;
  error: string | null;
  selectedKeys: string[];
  openKeys: string[];
  breadcrumb: { title: string; path?: string }[];
  hasPermission: (path: string) => boolean;
  refreshMenus: () => Promise<void>;
  onOpenChange: (keys: string[]) => void;
}

export const useMenus = (): UseMenusReturn => {
  const location = useLocation();
  const [userMenus, setUserMenus] = useState<UserMenuPermission | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 获取菜单数据
  const fetchMenus = async () => {
    try {
      setLoading(true);
      setError(null);
      const menuData = await MenuApiService.getUserMenus();
      setUserMenus(menuData);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取菜单失败');
      console.error('Failed to fetch menus:', err);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载菜单
  useEffect(() => {
    fetchMenus();
  }, []);

  // 计算当前选中的菜单项
  const selectedKeys = useMemo(() => {
    if (!userMenus?.menus) return [];
    
    const findMenuAndParentsByPath = (menus: MenuTreeNode[], path: string): MenuTreeNode[] => {
      const result: MenuTreeNode[] = [];
      
      const findMenu = (menus: MenuTreeNode[], path: string, parents: MenuTreeNode[] = []): boolean => {
        for (const menu of menus) {
          const currentParents = [...parents, menu];
          
          // 精确匹配
          if (menu.route_path === path) {
            result.push(...currentParents);
            return true;
          }
          
          // 处理动态路由（如 /agents/:agentId）
          if (menu.route_path !== '/' && path.startsWith(menu.route_path)) {
            // 检查是否是动态路由
            const isDynamicRoute = menu.route_path.includes('/:') || 
                                  menu.route_path.split('/').length === path.split('/').length;
            if (isDynamicRoute || path === menu.route_path || path.startsWith(menu.route_path + '/')) {
              result.push(...currentParents);
              
              // 如果有子菜单，继续查找以确保包含所有相关父菜单
              if (menu.children) {
                findMenu(menu.children, path, currentParents);
              }
              return true;
            }
          }
          
          // 递归查找子菜单
          if (menu.children) {
            const found = findMenu(menu.children, path, currentParents);
            if (found) return true;
          }
        }
        return false;
      };

      findMenu(menus, path);
      return result;
    };

    const matchedMenus = findMenuAndParentsByPath(userMenus.menus, location.pathname);
    return matchedMenus.map(menu => menu.key);
  }, [userMenus?.menus, location.pathname]);

  // 计算需要展开的菜单项
  const [persistentOpenKeys, setPersistentOpenKeys] = useState<string[]>(() => {
    const saved = localStorage.getItem('menuOpenKeys');
    return saved ? JSON.parse(saved) : [];
  });

  const findMenuByKey = (menu: MenuTreeNode, targetKey: string): boolean => {
    if (menu.key === targetKey) return true;
    if (menu.children) {
      return menu.children.some(child => findMenuByKey(child, targetKey));
    }
    return false;
  };

  const openKeys = useMemo(() => {
    if (!userMenus?.menus) return [];
    
    const keys: string[] = [];
    
    const findParentKeys = (menus: MenuTreeNode[], targetPath: string): boolean => {
      for (const menu of menus) {
        if (menu.route_path === targetPath || 
            (targetPath.startsWith(menu.route_path) && menu.route_path !== '/')) {
          return true;
        }
        
        if (menu.children) {
          const found = findParentKeys(menu.children, targetPath);
          if (found) {
            keys.push(menu.key);
            return true;
          }
        }
      }
      return false;
    };

    findParentKeys(userMenus.menus, location.pathname);
    
    // 合并自动展开和持久化的展开状态
    const autoOpenKeys = keys;
    const manualOpenKeys = persistentOpenKeys.filter(key => 
      userMenus.menus?.some(menu => findMenuByKey(menu, key))
    );
    
    return [...new Set([...autoOpenKeys, ...manualOpenKeys])];
  }, [userMenus?.menus, location.pathname, persistentOpenKeys]);

  // 持久化展开的菜单项
  const handleOpenChange = (keys: string[]) => {
    setPersistentOpenKeys(keys);
    localStorage.setItem('menuOpenKeys', JSON.stringify(keys));
  };

  // 生成面包屑导航
  const breadcrumb = useMemo(() => {
    if (!userMenus?.menus) return [];
    
    const crumbs: { title: string; path?: string }[] = [];
    
    const buildBreadcrumb = (menus: MenuTreeNode[], targetPath: string, parents: MenuTreeNode[] = []): boolean => {
      for (const menu of menus) {
        const currentParents = [...parents, menu];

        // 先检查子菜单
        if (menu.children) {
          const foundInChildren = buildBreadcrumb(menu.children, targetPath, currentParents);
          if (foundInChildren) return true;
        }

        // 再检查当前菜单
        if (menu.route_path === targetPath || 
            (targetPath.startsWith(menu.route_path) && menu.route_path !== '/')) {
          // 找到匹配的菜单，构建面包屑
          currentParents.forEach(parent => {
            let path = parent.redirect_path || parent.route_path || undefined;

            // 如果当前菜单有子菜单但没有自己的路由和重定向路径，跳转到第一个子菜单
            if (parent.children && parent.children.length > 0 && !path) {
              path = parent.children[0].route_path;
            }
            
            crumbs.push({
              title: parent.menu_name,
              path: path,
            });
          });
          return true;
        }
      }
      
      return false;
    };

    buildBreadcrumb(userMenus.menus, location.pathname);
    return crumbs;
  }, [userMenus?.menus, location.pathname]);

  // 权限检查
  const hasPermission = (path: string): boolean => {
    if (!userMenus?.permissions) return false;
    return userMenus.permissions.includes(path);
  };

  return {
    menus: userMenus?.menus || [],
    loading,
    error,
    selectedKeys,
    openKeys,
    breadcrumb,
    hasPermission,
    refreshMenus: fetchMenus,
    onOpenChange: handleOpenChange,
  };
};