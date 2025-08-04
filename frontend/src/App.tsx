import { Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider, App as AntdApp } from "antd";
import { useEffect } from "react";
import { SOPList } from "./pages/sop";
import { MCPManagement } from "./pages/mcp";
import { AgentManagement, AgentMarketplace, AgentChat } from "./pages/agent";
import { ModelsManagement } from "./pages/ai_model";
import { TasksManagement } from "./pages/scheduled_task";
import { UserManagement, RoleManagement, PermissionManagement, MenuManagement } from "./pages/user";
import TenantManagement from "./pages/tenant/TenantManagement";
import KnowledgeManagement from "./pages/kb";
import { ThemeProvider, useTheme } from "./hooks/ThemeContext";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { SSOCallback } from "./pages/auth/SSOCallback";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { useAuth } from "./hooks/useAuth";
import { configureAuthInterceptor } from "./utils/authInterceptor";
import MenuLayout from "./components/MenuLayout";


// 主应用组件（包装在主题提供者内部）
function AppContent() {
  const { antdTheme } = useTheme();
  const { checkAuth, logout } = useAuth();

  // 初始化认证检查和拦截器
  useEffect(() => {
    checkAuth();
    configureAuthInterceptor({
      onUnauthorized: () => {
        logout();
      }
    });
  }, []);

  return (
    <ConfigProvider theme={antdTheme}>
      <AntdApp>
        <Routes>
          {/* 公开路由 */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/sso/callback" element={<SSOCallback />} />
          
          {/* 受保护的路由 - 使用 MenuLayout 包裹 */}
          <Route element={
            <ProtectedRoute>
              <MenuLayout />
            </ProtectedRoute>
          }>
            <Route path="/" element={<Navigate to="/service/agents" replace />} />
            
            {/* 用户服务模块 */}
            <Route path="/service/agents" element={<AgentMarketplace />} />
            <Route path="/service/agents/:agentId" element={<AgentChat />} />
            <Route path="/service/knowledge" element={<KnowledgeManagement />} />
            
            {/* 系统管理模块 */}
            <Route path="/system/agents" element={<AgentManagement />} />
            <Route path="/system/agents/:agentId" element={<AgentChat />} />
            <Route path="/system/kb/sop" element={<SOPList />} />
            <Route path="/system/userRole" element={<MCPManagement />} />
            <Route path="/system/models" element={<ModelsManagement />} />
            <Route path="/system/tasks" element={<TasksManagement />} />
            <Route path="/system/permission" element={<UserManagement />} />
            <Route path="/system/userPermission/userRole" element={<RoleManagement />} />
            <Route path="/system/userPermission/permission" element={<PermissionManagement />} />
            <Route path="/system/userPermission/menu" element={<MenuManagement />} />
            <Route path="/system/tenant" element={<TenantManagement />} />
          </Route>
          
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
      </AntdApp>
    </ConfigProvider>
  );
}

// 导出的主应用组件（包装主题提供者）
export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
