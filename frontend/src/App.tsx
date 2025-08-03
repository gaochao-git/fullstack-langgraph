import { Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import { Layout, Menu, Drawer, ConfigProvider, App as AntdApp, Breadcrumb, Spin } from "antd";
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CloseOutlined,
  HomeOutlined,
} from "@ant-design/icons";
import { useState, useEffect } from "react";
import { SOPList } from "./pages/sop";
import { MCPManagement } from "./pages/mcp";
import { AgentManagement, AgentMarketplace, AgentChat } from "./pages/agent";
import { ModelsManagement } from "./pages/ai_model";
import { TasksManagement } from "./pages/scheduled_task";
import { UserManagement, RoleManagement, PermissionManagement } from "./pages/user";
import TenantManagement from "./pages/tenant/TenantManagement";
import KnowledgeManagement from "./pages/KnowledgeManagement";
import { ThemeProvider, useTheme } from "./hooks/ThemeContext";
import { ThemeToggleSimple } from "./components/ThemeToggle";
import { useMenus } from "./hooks/useMenus";
import { transformMenusForAntd } from "./utils/menuUtils";

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

  return (
    <ConfigProvider theme={antdTheme}>
      <AntdApp>
        <Layout style={{ minHeight: "100vh" }}>
      {/* 桌面端侧边栏 */}
      {!isMobile && (
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
            {/* 主题切换按钮 */}
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
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
        </Sider>
      )}

      {/* 移动端抽屉菜单 */}
      {isMobile && (
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
            {/* 面包屑导航 */}
            {!isMobile && breadcrumb.length > 0 && (
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
            {/* 移动端自定义头部 */}
            {isMobile && (
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
              <Route path="/" element={<Navigate to="/service/agents" replace />} />
              <Route path="/service/agents" element={<AgentMarketplace />} />
              <Route path="/service/agents/:agentId" element={<AgentChat />} />
              <Route path="/service/knowledge" element={<KnowledgeManagement />} />
              <Route path="/system/agents/:agentId" element={<AgentChat />} />
              <Route path="/system/agents" element={<AgentManagement />} />
              <Route path="/system/sop" element={<SOPList />} />
              <Route path="/system/mcp" element={<MCPManagement />} />
              <Route path="/system/models" element={<ModelsManagement />} />
              <Route path="/system/tasks" element={<TasksManagement />} />
              <Route path="/system/user" element={<UserManagement />} />
              <Route path="/system/userRole" element={<RoleManagement />} />
              <Route path="/system/permission" element={<PermissionManagement />} />
              <Route path="/system/tenant" element={<TenantManagement />} />
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
