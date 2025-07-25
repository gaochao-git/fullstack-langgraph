import { Routes, Route, Link } from "react-router-dom";
import { Layout, Menu, Drawer, ConfigProvider, App as AntdApp } from "antd";
import {
  RobotOutlined,
  UserOutlined,
  FileTextOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LinkOutlined,
  ApiOutlined,
  SettingOutlined,
  AppstoreOutlined,
  BookOutlined,
  CustomerServiceOutlined,
  CloseOutlined,
} from "@ant-design/icons";
import { useState, useEffect } from "react";
import ResearchAgent from "./agents/research_agent/ResearchAgent";
import DiagnosticAgent from "./agents/diagnostic_agent/DiagnosticAgent";
import SOPManagementSimple from "./pages/SOPManagementSimple";
import MCPManagement from "./pages/MCPManagement";
import AgentManagement from "./pages/AgentManagement";
import ModelsManagement from "./pages/ModelsManagement";
import AgentMarketplace from "./pages/AgentMarketplace";
import GenericAgentChat from "./pages/GenericAgentChat";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
import { ThemeToggleSimple } from "./components/ThemeToggle";

const { Sider, Content } = Layout;

// 主应用组件（包装在主题提供者内部）
function AppContent() {
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const { antdTheme, isDark } = useTheme();
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

  const menuItems = [
    {
      key: 'user-service',
      icon: <CustomerServiceOutlined />,
      label: '用户服务',
      children: [
        {
          key: '1',
          icon: <AppstoreOutlined />,
          label: <Link to="/">智能体广场</Link>,
        },
        {
          key: 'knowledge',
          icon: <BookOutlined />,
          label: <Link to="/knowledge">知识中心</Link>,
        },
      ],
    },
    {
      key: 'management',
      icon: <SettingOutlined />,
      label: '系统管理',
      children: [
        {
          key: '2',
          icon: <UserOutlined />,
          label: <Link to="/agents">智能体管理</Link>,
        },
        {
          key: '3',
          icon: <FileTextOutlined />,
          label: <Link to="/sop">SOP管理</Link>,
        },
        {
          key: '4',
          icon: <LinkOutlined />,
          label: <Link to="/mcp">MCP管理</Link>,
        },
        {
          key: '5',
          icon: <ApiOutlined />,
          label: <Link to="/models">模型管理</Link>,
        },
      ],
    },
  ];

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
          <Menu
            theme={isDark ? "dark" : "light"}
            mode="inline"
            defaultSelectedKeys={['1']}
            items={menuItems}
          />
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
            background: 'rgba(22,119,255,0.08)',
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
                color: '#1677ff'
              }}
            >
              <MenuUnfoldOutlined style={{ fontSize: 16 }} />
            </button>
            <span style={{ color: '#1677ff', fontWeight: 600, fontSize: 16 }}>
              智能运维平台
            </span>
            {/* 移动端主题切换按钮 */}
            <div style={{ marginLeft: 'auto' }}>
              <ThemeToggleSimple />
            </div>
          </div>
          <Menu
            mode="inline"
            defaultSelectedKeys={['1']}
            items={menuItems}
            onClick={() => setMobileMenuVisible(false)}
            style={{
              fontSize: '16px',
              border: 'none'
            }}
            className="mobile-menu-optimized"
          />
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
              <Route path="/" element={<AgentMarketplace />} />
              <Route path="/agents/research_agent" element={<ResearchAgent />} />
              <Route path="/agents/diagnostic_agent" element={<DiagnosticAgent />} />
              <Route path="/agents/:agentId" element={<GenericAgentChat />} />
              <Route path="/agents" element={<AgentManagement />} />
              <Route path="/sop" element={<SOPManagementSimple />} />
              <Route path="/mcp" element={<MCPManagement />} />
              <Route path="/models" element={<ModelsManagement />} />
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
