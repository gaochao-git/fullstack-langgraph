import React, { useState, useEffect } from 'react';
import { useLocation, Link, Outlet, useNavigate } from 'react-router-dom';
import { Layout, Menu, theme, Breadcrumb, Spin, Drawer, Dropdown, Avatar, Space, Select } from 'antd';
import { HomeOutlined, MenuFoldOutlined, MenuUnfoldOutlined, LogoutOutlined, UserOutlined, SwapOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useMenus } from '../hooks/useMenus';
import { transformMenusForAntd } from '../utils/menuUtils';
import { useAuth } from '../hooks/useAuth';
import { ThemeToggleSimple } from './ThemeToggle';
import { useTheme } from '../hooks/ThemeContext';

const { Header, Content, Sider } = Layout;

const MenuLayout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { menus, loading: menuLoading, breadcrumb } = useMenus();
  const { user, logout, switchRole, checkAuth } = useAuth();
  const { isDark } = useTheme();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();
  
  const [collapsed, setCollapsed] = useState(false);
  const [selectedTopMenu, setSelectedTopMenu] = useState<string>('');
  const [sideMenuItems, setSideMenuItems] = useState<MenuProps['items']>([]);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const [openKeys, setOpenKeys] = useState<string[]>([]);

  // 组件挂载时检查用户状态
  useEffect(() => {
    // 如果用户信息不存在，尝试重新获取
    if (!user) {
      checkAuth();
    }
  }, [user, checkAuth]);

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

  // 获取当前路径的第一级路径
  const getFirstLevelPath = (pathname: string): string => {
    const parts = pathname.split('/').filter(Boolean);
    return parts[0] || '';
  };

  // 从菜单数据中获取顶部菜单项
  const getTopMenuItems = (): MenuProps['items'] => {
    if (!menus || menus.length === 0) return [];
    
    // 查找首页菜单
    const homeMenu = menus.find(menu => menu.route_path === '/');
    
    // 如果首页有子菜单，使用子菜单作为顶部导航
    if (homeMenu?.children && homeMenu.children.length > 0) {
      return homeMenu.children.map(menu => ({
        key: menu.route_path?.split('/')[1] || menu.menu_id.toString(),
        label: menu.menu_name,
      }));
    }
    
    // 否则找到非首页的根菜单项作为顶部导航
    return menus
      .filter(menu => menu.route_path !== '/' && menu.parent_id === -1)
      .map(menu => ({
        key: menu.route_path?.split('/')[1] || menu.menu_id.toString(),
        label: menu.menu_name,
      }));
  };

  // 根据选中的顶部菜单获取侧边栏菜单
  const getSideMenuItems = (topMenuKey: string): MenuProps['items'] => {
    if (!menus || !topMenuKey) return [];
    
    // 首先检查首页的子菜单
    const homeMenu = menus.find(menu => menu.route_path === '/');
    if (homeMenu?.children) {
      const topMenu = homeMenu.children.find(menu => 
        menu.route_path?.split('/')[1] === topMenuKey
      );
      
      if (topMenu?.children) {
        return transformMenusForAntd(topMenu.children);
      }
    }
    
    // 如果没找到，尝试在根菜单中查找
    const topMenu = menus.find(menu => 
      menu.route_path?.split('/')[1] === topMenuKey || 
      menu.menu_id.toString() === topMenuKey
    );
    
    if (!topMenu || !topMenu.children) return [];
    
    // 转换子菜单为 Ant Design 格式
    return transformMenusForAntd(topMenu.children);
  };

  // 监听路径变化，更新选中的顶部菜单和侧边栏
  useEffect(() => {
    const firstLevel = getFirstLevelPath(location.pathname);
    setSelectedTopMenu(firstLevel);
    setSideMenuItems(getSideMenuItems(firstLevel));
    
    // 计算需要展开的父级菜单
    const pathParts = location.pathname.split('/').filter(Boolean);
    const parentPaths: string[] = [];
    
    // 从第二级开始，到倒数第二级为止，都是需要展开的父级菜单
    for (let i = 2; i < pathParts.length; i++) {
      const parentPath = '/' + pathParts.slice(0, i).join('/');
      parentPaths.push(parentPath);
    }
    
    // 合并现有的展开项和新的父级路径，避免覆盖用户手动展开的菜单
    setOpenKeys(prevKeys => {
      const newKeys = new Set([...prevKeys, ...parentPaths]);
      return Array.from(newKeys);
    });
  }, [location.pathname, menus]); // 添加 menus 依赖，确保菜单数据加载后更新

  // 获取侧边栏选中的菜单项
  const getSelectedKeys = (): string[] => {
    // 使用完整路径作为选中项
    return [location.pathname];
  };

  // 获取侧边栏展开的菜单项
  const getOpenKeys = (): string[] => {
    const keys: string[] = [];
    const pathParts = location.pathname.split('/').filter(Boolean);
    
    // 构建所有父级路径（不包含当前路径）
    for (let i = 2; i < pathParts.length; i++) {
      keys.push('/' + pathParts.slice(0, i).join('/'));
    }
    
    return keys;
  };

  const topMenuItems = getTopMenuItems();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 桌面端头部导航 */}
      {!isMobile && (
        <Header style={{ 
          display: 'flex', 
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          background: isDark ? '#141414' : '#fff',
          borderBottom: `1px solid ${isDark ? '#303030' : '#f0f0f0'}`,
          position: 'sticky',
          top: 0,
          zIndex: 100
        }}>
          {/* 左侧：Logo */}
          <div style={{ 
            width: 200,
            fontSize: 18,
            fontWeight: 600,
            color: isDark ? '#fff' : '#000'
          }}>
            智能运维平台
          </div>
          
          {/* 中间：导航菜单 */}
          <div style={{ 
            flex: 1,
            display: 'flex',
            justifyContent: 'flex-start',
            paddingLeft: '24px'
          }}>
            {menuLoading ? (
              <Spin size="small" />
            ) : (
              <Menu
                theme={isDark ? "dark" : "light"}
                mode="horizontal"
                selectedKeys={[selectedTopMenu]}
                items={topMenuItems}
                style={{ 
                  background: 'transparent',
                  borderBottom: 'none',
                  minWidth: 'auto'
                }}
                onClick={({ key }) => {
                  // 导航到对应模块的默认页面
                  let targetMenu = null;
                  
                  // 首先在首页的子菜单中查找
                  const homeMenu = menus.find(m => m.route_path === '/');
                  if (homeMenu?.children) {
                    targetMenu = homeMenu.children.find(m => 
                      m.route_path?.split('/')[1] === key
                    );
                  }
                  
                  // 如果没找到，在根菜单中查找
                  if (!targetMenu) {
                    targetMenu = menus.find(m => 
                      m.route_path?.split('/')[1] === key || 
                      m.menu_id.toString() === key
                    );
                  }
                  
                  if (targetMenu) {
                    // 优先使用重定向路径
                    if (targetMenu.redirect_path) {
                      navigate(targetMenu.redirect_path);
                    } else if (targetMenu.children?.[0]?.route_path) {
                      // 如果没有重定向路径，使用第一个子菜单
                      navigate(targetMenu.children[0].route_path);
                    }
                  }
                }}
              />
            )}
          </div>
          
          {/* 右侧：用户信息 */}
          <div style={{ 
            width: 200,
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'flex-end',
            gap: 16 
          }}>
            <ThemeToggleSimple />
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'userInfo',
                    label: (
                      <div style={{ padding: '4px 0' }}>
                        <Space direction="vertical" size={4} style={{ width: '100%' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <UserOutlined />
                            <span style={{ fontWeight: 500 }}>{user?.display_name || user?.username || '未获取'}</span>
                          </div>
                          <div style={{ paddingLeft: 24, fontSize: 12, color: '#666' }}>
                            <div>用户名：{user?.username || '未获取'}</div>
                            <div>邮箱：{user?.email || '未设置'}</div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                              <span>角色：</span>
                              {user?.roles && Array.isArray(user.roles) && user.roles.length > 1 ? (
                                <Select
                                  size="small"
                                  style={{ fontSize: 12, minWidth: 100 }}
                                  value={user.current_role ? (typeof user.current_role === 'string' ? user.current_role : user.current_role.role_id) : undefined}
                                  onChange={(roleId) => switchRole(roleId)}
                                  placeholder="选择角色"
                                  suffixIcon={<SwapOutlined />}
                                >
                                  {user.roles.map(role => {
                                    const roleId = typeof role === 'string' ? role : role.role_id;
                                    const roleName = typeof role === 'string' ? role : role.role_name;
                                    return (
                                      <Select.Option key={roleId} value={roleId}>
                                        {roleName}
                                      </Select.Option>
                                    );
                                  })}
                                </Select>
                              ) : (
                                <span>
                                  {user?.roles ? (
                                    Array.isArray(user.roles) ? 
                                      user.roles.map(r => typeof r === 'string' ? r : r.role_name).join(', ') : 
                                      user.roles
                                  ) : '未分配'}
                                </span>
                              )}
                            </div>
                            <div>部门：{user?.department_name || user?.department || '未分配'}</div>
                            <div>团队：{user?.group_name || user?.team || '未分配'}</div>
                          </div>
                        </Space>
                      </div>
                    ),
                    disabled: true,
                    style: { cursor: 'default' }
                  },
                  {
                    type: 'divider',
                  },
                  {
                    key: 'logout',
                    label: (
                      <Space>
                        <LogoutOutlined />
                        <span>退出登录</span>
                      </Space>
                    ),
                    onClick: logout
                  },
                ],
              }}
              placement="bottomRight"
              arrow
            >
              <Avatar 
                size="default" 
                icon={<UserOutlined />} 
                style={{ 
                  cursor: 'pointer',
                  backgroundColor: isDark ? '#1677ff' : '#1677ff'
                }}
              >
                {user?.display_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
              </Avatar>
            </Dropdown>
          </div>
        </Header>
      )}
      
      {/* 移动端头部 */}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ThemeToggleSimple />
          </div>
        </div>
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
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: 48,
            padding: '0 16px',
            background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(22,119,255,0.08)',
            marginBottom: 8
          }}>
            <span style={{ color: isDark ? '#60A5FA' : '#1677ff', fontWeight: 600, fontSize: 16 }}>
              导航菜单
            </span>
            <button
              type="button"
              onClick={() => setMobileMenuVisible(false)}
              style={{
                fontSize: '16px',
                width: 32,
                height: 32,
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                color: isDark ? '#60A5FA' : '#1677ff'
              }}
            >
              <MenuUnfoldOutlined style={{ fontSize: 16 }} />
            </button>
          </div>
          
          {/* 移动端顶级菜单 */}
          <div style={{ padding: '0 16px', marginBottom: 16 }}>
            <div style={{ fontSize: 14, color: isDark ? '#999' : '#666', marginBottom: 8 }}>模块</div>
            {menuLoading ? (
              <Spin size="small" />
            ) : (
              topMenuItems?.map((item: any) => (
                <button
                  key={item.key}
                  onClick={() => {
                    setSelectedTopMenu(item.key);
                    let targetMenu = null;
                    
                    // 首先在首页的子菜单中查找
                    const homeMenu = menus.find(m => m.route_path === '/');
                    if (homeMenu?.children) {
                      targetMenu = homeMenu.children.find(m => 
                        m.route_path?.split('/')[1] === item.key
                      );
                    }
                    
                    // 如果没找到，在根菜单中查找
                    if (!targetMenu) {
                      targetMenu = menus.find(m => 
                        m.route_path?.split('/')[1] === item.key || 
                        m.menu_id.toString() === item.key
                      );
                    }
                    
                    if (targetMenu) {
                      // 优先使用重定向路径
                      if (targetMenu.redirect_path) {
                        navigate(targetMenu.redirect_path);
                        setMobileMenuVisible(false);
                      } else if (targetMenu.children?.[0]?.route_path) {
                        // 如果没有重定向路径，使用第一个子菜单
                        navigate(targetMenu.children[0].route_path);
                        setMobileMenuVisible(false);
                      }
                    }
                  }}
                  style={{
                    width: '100%',
                    padding: '10px 16px',
                    marginBottom: 8,
                    border: 'none',
                    borderRadius: 6,
                    background: selectedTopMenu === item.key 
                      ? (isDark ? 'rgba(96,165,250,0.2)' : 'rgba(22,119,255,0.1)')
                      : (isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)'),
                    color: selectedTopMenu === item.key
                      ? (isDark ? '#60A5FA' : '#1677ff')
                      : (isDark ? '#fff' : '#000'),
                    cursor: 'pointer',
                    textAlign: 'left',
                    fontSize: 16,
                    fontWeight: selectedTopMenu === item.key ? 600 : 400
                  }}
                >
                  {item.label}
                </button>
              ))
            )}
          </div>
          
          {/* 移动端子菜单 */}
          {sideMenuItems && sideMenuItems.length > 0 && (
            <div style={{ borderTop: isDark ? '1px solid #333' : '1px solid #f0f0f0', paddingTop: 16 }}>
              <div style={{ fontSize: 14, color: isDark ? '#999' : '#666', marginBottom: 8, paddingLeft: 16 }}>菜单</div>
              <Menu
                mode="inline"
                theme={isDark ? "dark" : "light"}
                selectedKeys={getSelectedKeys()}
                defaultOpenKeys={getOpenKeys()}
                items={sideMenuItems}
                onClick={({ key }) => {
                  navigate(key);
                  setMobileMenuVisible(false);
                }}
                style={{
                  border: 'none',
                  background: 'transparent'
                }}
              />
            </div>
          )}
          
          {/* 移动端用户信息和登出 */}
          <div style={{ 
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            padding: '16px',
            borderTop: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.06)',
            background: isDark ? '#141414' : '#fff'
          }}>
            <div style={{ marginBottom: 16 }}>
              <div style={{ marginBottom: 8, fontSize: 16, fontWeight: 500, color: isDark ? '#fff' : '#000' }}>
                {user?.display_name || user?.username || '未获取'}
              </div>
              <div style={{ fontSize: 12, color: isDark ? 'rgba(255,255,255,0.65)' : 'rgba(0,0,0,0.65)', lineHeight: 1.6 }}>
                <div>角色：{user?.roles ? (Array.isArray(user.roles) ? user.roles.map(r => typeof r === 'string' ? r : r.role_name).join(', ') : user.roles) : '未获取'}</div>
                <div>部门：{user?.department || '未获取'}</div>
                <div>团队：{user?.team || '未获取'}</div>
              </div>
            </div>
            <button
              onClick={() => {
                setMobileMenuVisible(false);
                logout();
              }}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                borderRadius: 6,
                background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)',
                color: isDark ? '#fff' : '#000',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                fontSize: 16
              }}
            >
              <LogoutOutlined />
              退出登录
            </button>
          </div>
        </Drawer>
      )}
      
      <Layout>
        {/* 桌面端侧边栏 */}
        {!isMobile && sideMenuItems && sideMenuItems.length > 0 && (
          <Sider 
            width={200} 
            style={{ 
              background: colorBgContainer,
              height: 'calc(100vh - 64px)', // 减去头部高度
              position: 'sticky',
              top: 64,
              left: 0
            }}
            collapsible
            collapsed={collapsed}
            onCollapse={setCollapsed}
            trigger={
              <div style={{ 
                background: colorBgContainer,
                color: isDark ? '#fff' : '#000',
                borderTop: `1px solid ${isDark ? '#303030' : '#f0f0f0'}`,
                height: 48,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              </div>
            }
          >
            <div style={{
              height: 'calc(100% - 48px)', // 减去折叠按钮高度
              overflowY: 'auto',
              overflowX: 'hidden'
            }}>
              <Menu
                mode="inline"
                theme={isDark ? "dark" : "light"}
                selectedKeys={getSelectedKeys()}
                openKeys={openKeys}
                onOpenChange={setOpenKeys}
                style={{ 
                  borderInlineEnd: 0,
                  minHeight: '100%'
                }}
                items={sideMenuItems}
                onClick={({ key }) => {
                  // 导航到对应的路径
                  navigate(key);
                }}
              />
            </div>
          </Sider>
        )}
        
        <Layout style={{ 
          padding: 0,
          overflow: 'hidden',
          height: isMobile ? '100vh' : 'calc(100vh - 64px)', // 移动端使用全高，桌面端减去头部高度
          paddingTop: isMobile ? 48 : 0, // 移动端添加顶部内边距避免被固定头部遮挡
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* 桌面端面包屑 */}
          {!isMobile && breadcrumb.length > 0 && (
            <div style={{ 
              padding: '5px 24px 0 24px',
              background: isDark ? '#141414' : '#f0f0f0'
            }}>
              <Breadcrumb
                items={[
                  { 
                    href: '/', 
                    title: <HomeOutlined /> 
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
            </div>
          )}
          
          <Content
            style={{
              flex: 1,
              paddingLeft: 5,
              paddingRight: 5,
              paddingTop: 5,
              paddingBottom: 5,
              margin: isMobile ? 0 : 24,
              marginTop: 5,
              marginBottom: 5,
              background: colorBgContainer,
              borderRadius: isMobile ? 0 : borderRadiusLG,
              overflow: 'auto'
            }}
          >
            {children || <Outlet />}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MenuLayout;