import React, { lazy, Suspense, useMemo } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { MenuTreeNode } from '../types/menu';
import { useMenus } from '../hooks/useMenus';

// 动态导入组件的辅助函数
// 统一从模块的 index 文件导入，所有模块都应该有 index.ts/tsx 文件
const loadComponent = (componentPath: string): React.LazyExoticComponent<React.FC> => {
  const [, module, componentName] = componentPath.split('/');
  
  return lazy(() => 
    import(`../pages/${module}`)
      .then(m => {
        // 尝试获取命名导出的组件
        if (m[componentName]) {
          return { default: m[componentName] };
        }
        // 如果没有命名导出，尝试默认导出
        if (m.default) {
          return { default: m.default };
        }
        throw new Error(`Component ${componentName} not found in module ${module}`);
      })
      .catch(error => {
        console.error(`Failed to load component: ${componentPath}`, error);
        return { default: () => <div>组件加载失败: {componentPath}</div> };
      })
  );
};

// 组件映射表 - 使用动态加载函数
const componentMap: Record<string, React.LazyExoticComponent<React.FC>> = {
  // Agent模块
  'pages/agent/AgentManagement': loadComponent('pages/agent/AgentManagement'),
  'pages/agent/AgentMarketplace': loadComponent('pages/agent/AgentMarketplace'),
  'pages/agent/AgentChat': loadComponent('pages/agent/AgentChat'),
  
  // User模块
  'pages/user/UserManagement': loadComponent('pages/user/UserManagement'),
  'pages/user/RoleManagement': loadComponent('pages/user/RoleManagement'),
  'pages/user/PermissionManagement': loadComponent('pages/user/PermissionManagement'),
  'pages/user/MenuManagement': loadComponent('pages/user/MenuManagement'),
  
  // KB模块
  'pages/kb/KnowledgeManagement': loadComponent('pages/kb/KnowledgeManagement'),
  
  // SOP模块
  'pages/sop/SOPList': loadComponent('pages/sop/SOPList'),
  
  // MCP模块
  'pages/mcp/MCPManagement': loadComponent('pages/mcp/MCPManagement'),
  
  // AI模型模块
  'pages/ai_model/ModelsManagement': loadComponent('pages/ai_model/ModelsManagement'),
  
  // 任务调度模块
  'pages/scheduled_task/TasksManagement': loadComponent('pages/scheduled_task/TasksManagement'),
  
  // 租户管理模块
  'pages/tenant/TenantManagement': loadComponent('pages/tenant/TenantManagement'),
};

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
        // 优先使用预定义的组件映射，如果没有则动态加载
        let Component = componentMap[menu.menu_component];
        
        if (!Component) {
          // 动态加载未预定义的组件
          Component = loadComponent(menu.menu_component);
        }
        
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
                    {React.createElement(componentMap['pages/agent/AgentChat'])}
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