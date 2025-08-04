import { Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import { Layout, Menu, Drawer, ConfigProvider, App as AntdApp, Breadcrumb, Spin } from "antd";
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CloseOutlined,
  HomeOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import { useState, useEffect } from "react";
import { SOPList } from "./pages/sop";
import { MCPManagement } from "./pages/mcp";
import { AgentManagement, AgentMarketplace, AgentChat } from "./pages/agent";
import { ModelsManagement } from "./pages/ai_model";
import { TasksManagement } from "./pages/scheduled_task";
import { UserManagement, RoleManagement, PermissionManagement, MenuManagement } from "./pages/user";
import TenantManagement from "./pages/tenant/TenantManagement";
import KnowledgeManagement from "./pages/kb";
import { ThemeProvider, useTheme } from "./hooks/ThemeContext";
import { ThemeToggleSimple } from "./components/ThemeToggle";
import { useMenus } from "./hooks/useMenus";
import { transformMenusForAntd } from "./utils/menuUtils";
import { LoginPage } from "./pages/auth/LoginPage";
import { SSOCallback } from "./pages/auth/SSOCallback";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { useAuth } from "./hooks/useAuth";
import { configureAuthInterceptor } from "./utils/authInterceptor";

const { Sider, Content } = Layout;

// 组件映射表（用于动态路由渲染）
const ComponentMap: Record<string, React.ComponentType> = {
  'AgentMarketplace': AgentMarketplace,
  'KnowledgeManagement': KnowledgeManagement,
  'AgentManagement': AgentManagement,
  'SOPManagement': SOPList,
  'MCPManagement': MCPManagement,
  'ModelsManagement': ModelsManagement,
  'TasksManagement': TasksManagement,
  'UserManagement': UserManagement,
  'RoleManagement': RoleManagement,
  'PermissionManagement': PermissionManagement,
  'TenantManagement': TenantManagement,
};

// 主应用组件（包装在主题提供者内部）
function AppContent() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const { antdTheme, isDark } = useTheme();
  const { isAuthenticated, checkAuth, logout, user } = useAuth();
  
  // 使用新的菜单系统
  const { 
    menus, 
    loading: menuLoading, 
    error: menuError, 
    selectedKeys, 
    openKeys, 
    breadcrumb,
    hasPermission,
    onOpenChange
  } = useMenus();
  
  // Theme token removed as not used

  // 初始化认证检查和拦截器
  useEffect(() => {
    checkAuth();
    configureAuthInterceptor({
      onUnauthorized: () => {
        logout();
      }
    });
  }, []);

  // 检测屏幕尺寸
  useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth;
      setIsMobile(width < 768);
      if (width < 768) {
        setCollapsed(true);
      }
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  // 转换菜单数据为 Ant Design 格式
  const menuItems = transformMenusForAntd(menus);

  // 判断是否为公开页面（不需要显示菜单的页面）
  const isPublicPage = ['/login', '/sso/callback'].includes(location.pathname);

  return (
    <ConfigProvider theme={antdTheme}>
      <AntdApp>
        <Layout style={{ minHeight: "100vh" }}>
      {/* 桌面端侧边栏 - 只在已登录且非公开页面时显示 */}
      {!isMobile && isAuthenticated && !isPublicPage && (
        <Sider trigger={null} collapsible collapsed={collapsed} theme={isDark ? "dark" : "light"}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            height: 48,
            padding: '0 12px',
            background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.03)',
            margin: 0
          }}>
            {!collapsed && (
              <span style={{ color: isDark ? '#fff' : '#000', fontWeight: 600, fontSize: 16 }}>
                智能运维平台
              </span>
            )}
            {/* 主题切换和用户信息 */}
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
              {user && !collapsed && (
                <span style={{ color: isDark ? '#fff' : '#000', fontSize: 14 }}>
                  {user.display_name || user.username}
                </span>
              )}
              <ThemeToggleSimple />
              <button
                type="button"
                onClick={() => setCollapsed(!collapsed)}
                style={{
                  fontSize: '16px',
                  width: 36,
                  height: 36,
                  border: 'none',
                  background: 'none',
                  cursor: 'pointer',
                  marginLeft: '8px',
                  color: isDark ? '#fff' : '#000'
                }}
              >
                {collapsed ? <MenuUnfoldOutlined style={{ fontSize: 16 }} /> : <MenuFoldOutlined style={{ fontSize: 16 }} />}
              </button>
            </div>
          </div>
          {menuLoading ? (
            <div style={{ padding: '20px', textAlign: 'center' }}>
              <Spin size="small" />
            </div>
          ) : (
            <Menu
              theme={isDark ? "dark" : "light"}
              mode="inline"
              selectedKeys={selectedKeys}
              openKeys={openKeys}
              items={menuItems}
              onClick={(e) => {
                // 处理菜单点击事件
                const menuItem = menuItems.find(item => item.key === e.key);
                if (menuItem && menuItem.label && typeof menuItem.label !== 'string') {
                  // 菜单标签已包含Link组件，路由会自动处理
                  console.log('菜单点击:', e.key, menuItem);
                }
              }}
              onOpenChange={onOpenChange}
              style={{ border: 'none' }}
            />
          )}
          {/* 登出按钮 */}
          {isAuthenticated && (
            <div style={{ 
              padding: '0 16px 16px', 
              borderTop: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.06)',
              marginTop: 'auto'
            }}>
              <button
                onClick={logout}
                style={{
                  width: '100%',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: 6,
                  background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)',
                  color: isDark ? '#fff' : '#000',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  gap: 8,
                  fontSize: 14
                }}
              >
                <LogoutOutlined />
                {!collapsed && '退出登录'}
              </button>
            </div>
          )}
        </Sider>
      )}

      {/* 移动端抽屉菜单 - 只在已登录且非公开页面时显示 */}
      {isMobile && isAuthenticated && !isPublicPage && (
        <Drawer
          title={null}
          placement="left"
          closable={false}
          onClose={() => setMobileMenuVisible(false)}
          open={mobileMenuVisible}
          bodyStyle={{ padding: 0 }}
          width={Math.min(280, window.innerWidth * 0.85)}
          closeIcon={<CloseOutlined style={{ fontSize: 16 }} />}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            height: 48,
            padding: '0 12px',
            background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(22,119,255,0.08)',
            margin: 0
          }}>
            <button
              type="button"
              onClick={() => setMobileMenuVisible(false)}
              style={{
                fontSize: '16px',
                width: 36,
                height: 36,
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                marginRight: '8px',
                color: isDark ? '#60A5FA' : '#1677ff'
              }}
            >
              <MenuUnfoldOutlined style={{ fontSize: 16 }} />
            </button>
            <span style={{ color: isDark ? '#60A5FA' : '#1677ff', fontWeight: 600, fontSize: 16 }}>
              智能运维平台
            </span>
            {/* 移动端主题切换按钮 */}
            <div style={{ marginLeft: 'auto' }}>
              <ThemeToggleSimple />
            </div>
          </div>
          {menuLoading ? (
            <div style={{ padding: '20px', textAlign: 'center' }}>
              <Spin size="small" />
            </div>
          ) : (
            <Menu
              mode="inline"
              selectedKeys={selectedKeys}
              openKeys={openKeys}
              items={menuItems}
              onClick={(e) => {
                setMobileMenuVisible(false);
                // 处理菜单点击事件
                const menuItem = menuItems.find(item => item.key === e.key);
                if (menuItem && menuItem.label && typeof menuItem.label !== 'string') {
                  // 菜单标签已包含Link组件，路由会自动处理
                  console.log('移动端菜单点击:', e.key, menuItem);
                }
              }}
              onOpenChange={onOpenChange}
              style={{
                fontSize: '16px',
                border: 'none'
              }}
              className="mobile-menu-optimized"
            />
          )}
        </Drawer>
      )}
      <Layout>
        {/* 删除Header，主内容区直接顶到顶部 */}
        <Layout style={{ height: '100vh' }}>
          <Content 
            className={`${isDark ? 'bg-slate-800' : 'bg-gray-50'} transition-colors duration-300`}
            style={{ 
              padding: isMobile ? '12px' : '16px',
              overflow: 'auto',
              height: '100%',
              paddingTop: isMobile ? 56 : undefined // 预留头部空间
            }}
          >
            {/* 面包屑导航 - 只在已登录且非公开页面时显示，智能体聊天页面不显示 */}
            {!isMobile && isAuthenticated && !isPublicPage && breadcrumb.length > 0 && !location.pathname.match(/^\/service\/agents\/[^\/]+$/) && (
              <Breadcrumb 
                style={{ 
                  marginBottom: '16px',
                  padding: '8px 0'
                }}
                items={[
                  {
                    href: '/',
                    title: <HomeOutlined />,
                  },
                  ...breadcrumb.map(crumb => ({
                    title: crumb.path ? (
                      <Link to={crumb.path}>{crumb.title}</Link>
                    ) : (
                      crumb.title
                    ),
                  }))
                ]}
              />
            )}
            {/* 移动端自定义头部 - 只在已登录且非公开页面时显示 */}
            {isMobile && isAuthenticated && !isPublicPage && (
              <div
                style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  width: '100vw',
                  height: 48,
                  background: isDark ? '#1f1f1f' : '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  borderBottom: isDark ? '1px solid #333' : '1px solid #f0f0f0',
                  zIndex: 1001,
                  boxSizing: 'border-box',
                  padding: '0 12px',
                  fontWeight: 600
                }}
              >
                <button
                  type="button"
                  onClick={() => setMobileMenuVisible(true)}
                  style={{
                    fontSize: 16,
                    background: 'none',
                    border: 'none',
                    color: '#1677ff',
                    padding: '8px',
                    borderRadius: 6,
                    marginRight: 8,
                    minWidth: 44,
                    minHeight: 44,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  aria-label="打开菜单"
                >
                  <MenuFoldOutlined style={{ fontSize: 16 }} />
                </button>
                <span style={{ flex: 1, textAlign: 'center', color: isDark ? '#fff' : '#222', fontSize: 18, fontWeight: 600 }}>
                  智能运维平台
                </span>
                {/* 右侧可加更多按钮 */}
              </div>
            )}
            <Routes>
              {/* 公开路由 */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/sso/callback" element={<SSOCallback />} />
              
              {/* 受保护的路由 */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Navigate to="/service/agents" replace />
                </ProtectedRoute>
              } />
              <Route path="/service/agents" element={
                <ProtectedRoute>
                  <AgentMarketplace />
                </ProtectedRoute>
              } />
              <Route path="/service/agents/:agentId" element={
                <ProtectedRoute>
                  <AgentChat />
                </ProtectedRoute>
              } />
              <Route path="/service/knowledge" element={
                <ProtectedRoute>
                  <KnowledgeManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/agents/:agentId" element={
                <ProtectedRoute>
                  <AgentChat />
                </ProtectedRoute>
              } />
              <Route path="/system/agents" element={
                <ProtectedRoute>
                  <AgentManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/sop" element={
                <ProtectedRoute>
                  <SOPList />
                </ProtectedRoute>
              } />
              <Route path="/system/mcp" element={
                <ProtectedRoute>
                  <MCPManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/models" element={
                <ProtectedRoute>
                  <ModelsManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/tasks" element={
                <ProtectedRoute>
                  <TasksManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/user" element={
                <ProtectedRoute>
                  <UserManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/userRole" element={
                <ProtectedRoute>
                  <RoleManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/permission" element={
                <ProtectedRoute>
                  <PermissionManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/menu" element={
                <ProtectedRoute>
                  <MenuManagement />
                </ProtectedRoute>
              } />
              <Route path="/system/tenant" element={
                <ProtectedRoute>
                  <TenantManagement />
                </ProtectedRoute>
              } />
              <Route
                path="*"
                element={
                  <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
                    <h1 className="text-4xl font-bold text-red-400">404 - 页面不存在</h1>
                    <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>您访问的页面不存在。</p>
                    <Link to="/">
                      <button className={`px-4 py-2 border rounded-md transition-colors duration-200 ${
                        isDark 
                          ? 'border-gray-600 text-gray-300 hover:bg-gray-700' 
                          : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}>
                        返回首页
                      </button>
                    </Link>
              </div>
                }
              />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
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
