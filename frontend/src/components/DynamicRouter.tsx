import React, { lazy, Suspense, useMemo } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { MenuTreeNode } from '../types/menu';
import { useMenus } from '../hooks/useMenus';

// 动态导入组件的辅助函数
const loadComponent = (componentPath: string): React.LazyExoticComponent<React.FC> => {
  // 使用缓存避免重复创建
  if (componentCache[componentPath]) {
    return componentCache[componentPath];
  }

  // 如果路径不是 pages/xxx/ComponentName 格式，直接返回错误组件
  if (!componentPath.startsWith('pages/') || componentPath.split('/').length !== 3) {
    return lazy(() => Promise.resolve({ 
      default: () => <div>无效的组件路径: {componentPath}</div> 
    }));
  }
  
  const pathParts = componentPath.trim().split('/');
  const [, module, componentName] = pathParts.map(part => part.trim());
  
  const component = lazy(() => 
    import(`../pages/${module}`)
      .then(m => {
        // 直接使用命名导出
        if (m[componentName]) {
          return { default: m[componentName] };
        }
        throw new Error(`Component ${componentName} not found in module ${module}`);
      })
      .catch(error => {
        console.error(`Failed to load component: ${componentPath}`, error);
        return { default: () => <div>组件加载失败: {componentPath}</div> };
      })
  );

  // 缓存组件
  componentCache[componentPath] = component;
  return component;
};

// 组件缓存，避免重复创建相同的懒加载组件
const componentCache: Record<string, React.LazyExoticComponent<React.FC>> = {};

// 加载中组件
const LoadingComponent = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    minHeight: '400px' 
  }}>
    <Spin size="large" />
  </div>
);

// 根据菜单生成路由
const generateRoutes = (menus: MenuTreeNode[]): React.ReactElement[] => {
  const routes: React.ReactElement[] = [];
  
  const processMenu = (menuList: MenuTreeNode[]) => {
    menuList.forEach(menu => {
      // 跳过隐藏的菜单
      if (menu.show_menu === 0) return;
      
      // 如果有组件路径，尝试加载组件
      if (menu.menu_component && menu.route_path) {
        // 直接使用动态加载
        const Component = loadComponent(menu.menu_component);
        
        if (Component) {
          // 为动态路由（如 /service/agents/:agentId）生成额外的路由
          // 只为 /service/agents 路径生成动态路由，不为 /system/ai/agents 生成
          if (menu.route_path === '/service/agents') {
            routes.push(
              <Route 
                key={`${menu.route_path}/:agentId`}
                path={`${menu.route_path}/:agentId`}
                element={
                  <Suspense fallback={<LoadingComponent />}>
                    {React.createElement(loadComponent('pages/agent/AgentChat'))}
                  </Suspense>
                }
              />
            );
          }
          
          // 主路由
          routes.push(
            <Route 
              key={menu.route_path}
              path={menu.route_path}
              element={
                <Suspense fallback={<LoadingComponent />}>
                  <Component />
                </Suspense>
              }
            />
          );
        }
      }
      
      // 递归处理子菜单
      if (menu.children && menu.children.length > 0) {
        processMenu(menu.children);
      }
    });
  };
  
  processMenu(menus);
  return routes;
};

export const DynamicRouter: React.FC = () => {
  const { menus, loading } = useMenus();
  
  // 使用 useMemo 缓存路由，避免每次渲染都重新生成
  const dynamicRoutes = useMemo(() => {
    if (!menus || menus.length === 0) return [];
    return generateRoutes(menus);
  }, [menus]);
  
  if (loading) {
    return <LoadingComponent />;
  }
  
  return (
    <Routes>
      {/* 默认路由 */}
      <Route path="/" element={<Navigate to="/service/agents" replace />} />
      
      {/* 动态生成的路由 */}
      {dynamicRoutes}
      
      {/* 404 页面 */}
      <Route path="*" element={
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
          <h1 className="text-4xl font-bold text-red-400">404 - 页面不存在</h1>
          <p className="text-gray-600">您访问的页面不存在。</p>
          <a href="/">
            <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors duration-200">
              返回首页
            </button>
          </a>
        </div>
      } />
    </Routes>
  );
};