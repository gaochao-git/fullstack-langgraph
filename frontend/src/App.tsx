import { Routes, Route, Link } from "react-router-dom";
import { Layout, Menu, Typography, theme, Drawer } from "antd";
import {
  RobotOutlined,
  ToolOutlined,
  ApiOutlined,
  BookOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from "@ant-design/icons";
import { useState, useEffect } from "react";
import ResearchAgent from "./agents/research_agent/ResearchAgent";
import DiagnosticAgent from "./agents/diagnostic_agent/DiagnosticAgent";

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

export default function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  // 检测屏幕尺寸
  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth < 768) {
        setCollapsed(true);
      }
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  const menuItems = [
    {
      key: '1',
      icon: <RobotOutlined />,
      label: <Link to="/">智能体</Link>,
    },
    {
      key: '2',
      icon: <ToolOutlined />,
      label: <Link to="/tools">工具</Link>,
    },
    {
      key: '3',
      icon: <ApiOutlined />,
      label: <Link to="/models">模型</Link>,
    },
    {
      key: '4',
      icon: <BookOutlined />,
      label: <Link to="/knowledge">知识库</Link>,
    },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {/* 桌面端侧边栏 */}
      {!isMobile && (
        <Sider trigger={null} collapsible collapsed={collapsed} theme="dark">
          <div style={{
            display: 'flex',
            alignItems: 'center',
            height: 48,
            padding: '0 12px',
            background: 'rgba(255,255,255,0.08)',
            margin: 0
          }}>
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
                marginRight: '8px',
                color: '#fff'
              }}
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </button>
            {!collapsed && (
              <span style={{ color: '#fff', fontWeight: 600, fontSize: 16 }}>
                智能运维平台
              </span>
            )}
          </div>
          <Menu
            theme="dark"
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
          width={250}
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
              <MenuUnfoldOutlined />
            </button>
            <span style={{ color: '#1677ff', fontWeight: 600, fontSize: 16 }}>
              运维平台
            </span>
          </div>
          <Menu
            mode="inline"
            defaultSelectedKeys={['1']}
            items={menuItems}
            onClick={() => setMobileMenuVisible(false)}
          />
        </Drawer>
      )}
      <Layout>
        {/* 删除Header，主内容区直接顶到顶部 */}
        <Layout style={{ height: '100vh' }}>
          <Content 
            style={{ 
              padding: isMobile ? '12px' : '16px',
              overflow: 'auto',
              backgroundColor: '#f5f5f5',
              height: '100%'
            }}
          >
            <Routes>
              <Route
                path="/"
                element={
                  <div className={`grid gap-4 ${isMobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}`}>
                    <Link to="/agents/research_agent" className="block">
                      <div className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow ${isMobile ? 'p-4' : 'p-6'}`}>
                        <RobotOutlined className={`text-blue-500 mb-3 ${isMobile ? 'text-xl' : 'text-2xl'}`} />
                        <h2 className={`font-semibold mb-2 ${isMobile ? 'text-lg' : 'text-xl'}`}>研究助手</h2>
                        <p className={`text-gray-600 ${isMobile ? 'text-sm' : 'text-base'}`}>
                          强大的研究助手，可以帮助你进行网络搜索、信息整理和深度分析。
                        </p>
                      </div>
                    </Link>
                    <Link to="/agents/diagnostic_agent" className="block">
                      <div className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow ${isMobile ? 'p-4' : 'p-6'}`}>
                        <RobotOutlined className={`text-green-500 mb-3 ${isMobile ? 'text-xl' : 'text-2xl'}`} />
                        <h2 className={`font-semibold mb-2 ${isMobile ? 'text-lg' : 'text-xl'}`}>故障诊断助手</h2>
                        <p className={`text-gray-600 ${isMobile ? 'text-sm' : 'text-base'}`}>
                          智能系统监控与故障诊断，实时分析系统性能指标。
                        </p>
                      </div>
                    </Link>
                  </div>
                }
              />
              <Route path="/agents/research_agent" element={<ResearchAgent />} />
              <Route path="/agents/diagnostic_agent" element={<DiagnosticAgent />} />
              <Route
                path="*"
                element={
                  <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
                    <h1 className="text-4xl font-bold text-red-400">404 - 页面不存在</h1>
                    <p className="text-gray-600">您访问的页面不存在。</p>
                    <Link to="/">
                      <button className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
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
  );
}
