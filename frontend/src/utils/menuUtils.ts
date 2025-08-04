/**
 * 菜单工具函数
 * 处理菜单相关的辅助功能
 */

import { MenuTreeNode } from '../types/menu';
import * as Icons from '@ant-design/icons';
import * as LucideIcons from 'lucide-react';
import { createElement } from 'react';
import { Link } from 'react-router-dom';
import iconConfig from '../icons/icon-config.json';

/**
 * 根据图标名称获取图标组件（支持 Ant Design 和 Lucide 图标）
 */
export const getAntdIcon = (iconName: string) => {
  if (!iconName) return null;
  
  // 处理 lucide: 前缀的图标
  if (iconName.startsWith('lucide:')) {
    const lucideIconName = iconName.replace('lucide:', '');
    
    // 将 kebab-case 转换为 PascalCase
    const pascalCaseName = lucideIconName
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join('');
    
    console.log(`尝试加载 Lucide 图标: ${iconName} -> ${pascalCaseName}`);
    
    // 检查图标是否在配置文件中定义
    if (iconConfig.icons[iconName]) {
      const LucideIconComponent = (LucideIcons as any)[pascalCaseName];
      
      if (LucideIconComponent) {
        console.log(`✅ 成功加载 Lucide 图标: ${pascalCaseName}`);
        return createElement(LucideIconComponent, { size: 16 });
      }
    }
    
    console.log(`❌ 找不到 Lucide 图标: ${pascalCaseName}，使用默认图标`);
    return createElement(Icons.AppstoreOutlined);
  }
  
  // 处理 Ant Design 图标
  console.log(`尝试加载 Ant Design 图标: ${iconName}`);
  const IconComponent = (Icons as any)[iconName];
  
  if (IconComponent) {
    console.log(`✅ 成功加载 Ant Design 图标: ${iconName}`);
    return createElement(IconComponent);
  }
  
  console.log(`❌ 找不到 Ant Design 图标: ${iconName}，使用默认图标`);
  return createElement(Icons.AppstoreOutlined);
};

/**
 * 将菜单树转换为 Ant Design Menu 组件所需的格式
 */
export const transformMenusForAntd = (menus: MenuTreeNode[]): any[] => {
  const result: any[] = [];
  
  menus.forEach(menu => {
    // 如果是首页菜单，跳过该层级，直接添加其子菜单到结果中
    if (menu.menu_name === '首页' || menu.route_path === '/') {
      if (menu.children && menu.children.length > 0) {
        result.push(...transformMenusForAntd(menu.children));
      }
      return;
    }

    const menuItem: any = {
      key: menu.key,
      icon: getAntdIcon(menu.menu_icon),
      label: menu.menu_name,
    };

    // 如果有重定向路径，添加链接；如果没有子菜单且有路由路径，也添加链接
    const hasChildren = menu.children && menu.children.length > 0;
    const path = menu.redirect_path || (!hasChildren ? menu.route_path : null);
    
    if (path) {
      menuItem.label = createElement(Link, { to: path }, menu.menu_name);
    } else {
      menuItem.label = menu.menu_name;
    }

    // 递归处理子菜单
    if (menu.children && menu.children.length > 0) {
      menuItem.children = transformMenusForAntd(menu.children);
    }

    result.push(menuItem);
  });
  
  return result;
};

/**
 * 扁平化菜单树，获取所有菜单项
 */
export const flattenMenus = (menus: MenuTreeNode[]): MenuTreeNode[] => {
  const result: MenuTreeNode[] = [];
  
  const flatten = (menuList: MenuTreeNode[]) => {
    menuList.forEach(menu => {
      result.push(menu);
      if (menu.children && menu.children.length > 0) {
        flatten(menu.children);
      }
    });
  };
  
  flatten(menus);
  return result;
};

/**
 * 根据路径查找菜单项
 */
export const findMenuByPath = (menus: MenuTreeNode[], path: string): MenuTreeNode | null => {
  for (const menu of menus) {
    // 精确匹配
    if (menu.route_path === path) {
      return menu;
    }
    
    // 前缀匹配（用于动态路由）
    if (path.startsWith(menu.route_path) && menu.route_path !== '/') {
      return menu;
    }
    
    // 递归搜索子菜单
    if (menu.children && menu.children.length > 0) {
      const found = findMenuByPath(menu.children, path);
      if (found) return found;
    }
  }
  
  return null;
};

/**
 * 获取菜单的父级路径
 */
export const getMenuParentPaths = (menus: MenuTreeNode[], targetPath: string): string[] => {
  const paths: string[] = [];
  
  const findParents = (menuList: MenuTreeNode[], target: string, parents: string[] = []): boolean => {
    for (const menu of menuList) {
      const currentParents = [...parents, menu.route_path];
      
      if (menu.route_path === target) {
        paths.push(...currentParents);
        return true;
      }
      
      if (menu.children && menu.children.length > 0) {
        const found = findParents(menu.children, target, currentParents);
        if (found) return true;
      }
    }
    
    return false;
  };
  
  findParents(menus, targetPath);
  return paths.filter(Boolean);
};

/**
 * 检查菜单是否应该显示
 */
export const shouldShowMenu = (menu: MenuTreeNode): boolean => {
  return menu.show_menu === 1;
};

/**
 * 过滤隐藏的菜单项
 */
export const filterVisibleMenus = (menus: MenuTreeNode[]): MenuTreeNode[] => {
  return menus
    .filter(shouldShowMenu)
    .map(menu => ({
      ...menu,
      children: menu.children ? filterVisibleMenus(menu.children) : undefined,
    }));
};

/**
 * 验证路由路径格式
 */
export const isValidRoutePath = (path: string): boolean => {
  if (!path) return false;
  
  // 路径应该以 / 开头
  if (!path.startsWith('/')) return false;
  
  // 检查是否包含非法字符
  const invalidChars = /[<>:"|?*]/;
  if (invalidChars.test(path)) return false;
  
  return true;
};

/**
 * 标准化路由路径
 */
export const normalizeRoutePath = (path: string): string => {
  if (!path) return '/';
  
  // 确保以 / 开头
  let normalizedPath = path.startsWith('/') ? path : `/${path}`;
  
  // 移除末尾的 /（除非是根路径）
  if (normalizedPath.length > 1 && normalizedPath.endsWith('/')) {
    normalizedPath = normalizedPath.slice(0, -1);
  }
  
  return normalizedPath;
};

/**
 * 获取菜单的层级深度
 */
export const getMenuDepth = (menus: MenuTreeNode[]): number => {
  if (!menus || menus.length === 0) return 0;
  
  let maxDepth = 1;
  
  menus.forEach(menu => {
    if (menu.children && menu.children.length > 0) {
      const childDepth = getMenuDepth(menu.children) + 1;
      maxDepth = Math.max(maxDepth, childDepth);
    }
  });
  
  return maxDepth;
};

/**
 * 生成菜单统计信息
 */
export const getMenuStats = (menus: MenuTreeNode[]) => {
  const stats = {
    total: 0,
    visible: 0,
    hidden: 0,
    withChildren: 0,
    leafNodes: 0,
    maxDepth: 0,
  };
  
  const analyze = (menuList: MenuTreeNode[], depth = 1) => {
    stats.maxDepth = Math.max(stats.maxDepth, depth);
    
    menuList.forEach(menu => {
      stats.total++;
      
      if (menu.show_menu === 1) {
        stats.visible++;
      } else {
        stats.hidden++;
      }
      
      if (menu.children && menu.children.length > 0) {
        stats.withChildren++;
        analyze(menu.children, depth + 1);
      } else {
        stats.leafNodes++;
      }
    });
  };
  
  analyze(menus);
  return stats;
};