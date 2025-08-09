import { Routes, Route } from "react-router-dom";
import { ConfigProvider, App as AntdApp } from "antd";
import { useEffect } from "react";
import { ThemeProvider, useTheme } from "@/hooks/ThemeContext";
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { SSOCallback } from "@/pages/auth/SSOCallback";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/hooks/useAuth";
import { configureAuthInterceptor } from "@/utils/authInterceptor";
import MenuLayout from "@/components/MenuLayout";
import { DynamicRouter } from "@/components/DynamicRouter";
import GlobalLoading from "@/components/GlobalLoading";


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
    
    // 不再需要启动定时器
  }, []);

  return (
    <ConfigProvider theme={antdTheme}>
      <AntdApp>
        <GlobalLoading />
        <Routes>
          {/* 公开路由 */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/sso/callback" element={<SSOCallback />} />
          
          {/* 受保护的路由 - 使用 MenuLayout 包裹 */}
          <Route path="/*" element={
            <ProtectedRoute>
              <MenuLayout>
                <DynamicRouter />
              </MenuLayout>
            </ProtectedRoute>
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
