/**
 * 组件注册表
 * 将数据库中的组件名映射到实际的组件
 */

import React, { lazy } from 'react';

// 组件映射表 - 与数据库 menu_component 字段对应
export const componentRegistry = {
  // 页面组件
  'UserManagement': lazy(() => import('../pages/user').then(m => ({ default: m.UserManagement }))),
  'MenuManagement': lazy(() => import('../pages/user').then(m => ({ default: m.MenuManagement }))),
  'RoleManagement': lazy(() => import('../pages/user').then(m => ({ default: m.RoleManagement }))),
  'PermissionManagement': lazy(() => import('../pages/user').then(m => ({ default: m.PermissionManagement }))),
  
  'AgentManagement': lazy(() => import('../pages/agent/AgentManagement')),
  'AgentMarketplace': lazy(() => import('../pages/agent/AgentMarketplace')),
  'AgentChat': lazy(() => import('../pages/agent/AgentChat')),
  'DiagnosticChatView': lazy(() => import('../pages/agent/DiagnosticChatView').then(m => ({ default: m.DiagnosticChatView }))),
  
  'ModelsManagement': lazy(() => import('../pages/ai_model').then(m => ({ default: m.ModelsManagement }))),
  'KnowledgeManagement': lazy(() => import('../pages/kb').then(m => ({ default: m.KnowledgeManagement }))),
  
  'SOPManagement': lazy(() => import('../pages/sop').then(m => ({ default: m.SOPManagement }))),
  'SOPList': lazy(() => import('../pages/sop').then(m => ({ default: m.SOPList }))),
  
  'MCPManagement': lazy(() => import('../pages/mcp').then(m => ({ default: m.MCPManagement }))),
  
  'APIKeyManagement': lazy(() => import('../pages/user').then(m => ({ default: m.APIKeyManagement }))),
  
  // 待开发的页面
  'HomePage': lazy(() => Promise.resolve({ 
    default: () => React.createElement('div', { style: { padding: '20px', textAlign: 'center' } }, '首页 - 待开发')
  })),
  'TasksManagement': lazy(() => import('../pages/scheduled_task').then(m => ({ default: m.TasksManagement }))),
};

// 获取组件
export function getComponent(componentName: string): React.LazyExoticComponent<React.ComponentType<any>> | null {
  const component = componentRegistry[componentName as keyof typeof componentRegistry];
  if (component) {
    // 为懒加载组件设置 displayName，帮助调试
    (component as any).displayName = `Lazy(${componentName})`;
  }
  return component || null;
}