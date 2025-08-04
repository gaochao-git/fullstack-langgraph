import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, Card, Tabs, message, Divider, Space } from 'antd';
import { UserOutlined, LockOutlined, GlobalOutlined } from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/ThemeContext';
import './LoginPage.css';

const { TabPane } = Tabs;

export function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'jwt' | 'sso'>('jwt');
  const navigate = useNavigate();
  const location = useLocation();
  const { login, ssoLogin } = useAuth();
  const { isDark } = useTheme();
  
  const from = location.state?.from?.pathname || '/';

  const handleJWTLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      await login(values.username, values.password);
      message.success('登录成功');
      navigate(from, { replace: true });
    } catch (error: any) {
      message.error(error.message || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  const handleSSOLogin = async () => {
    try {
      setLoading(true);
      await ssoLogin();
      // SSO登录通常会重定向到SSO提供商页面
    } catch (error: any) {
      message.error(error.message || 'SSO登录失败');
      setLoading(false);
    }
  };

  return (
    <div className={`login-container ${isDark ? 'dark' : ''}`}>
      <div className="login-content">
        <Card className="login-card" bordered={false}>
          <div className="login-header">
            <h1 className="login-title">智能运维平台</h1>
            <p className="login-subtitle">请登录以继续访问系统</p>
          </div>

          <Tabs 
            activeKey={activeTab} 
            onChange={(key) => setActiveTab(key as 'jwt' | 'sso')}
            centered
          >
            <TabPane tab="账号密码登录" key="jwt">
              <Form
                name="jwt-login"
                className="login-form"
                onFinish={handleJWTLogin}
                size="large"
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                >
                  <Input 
                    prefix={<UserOutlined />} 
                    placeholder="用户名"
                    autoComplete="username"
                  />
                </Form.Item>
                
                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                >
                  <Input.Password
                    prefix={<LockOutlined />}
                    placeholder="密码"
                    autoComplete="current-password"
                  />
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    className="login-button"
                    loading={loading}
                    block
                  >
                    登录
                  </Button>
                </Form.Item>
              </Form>
            </TabPane>

            <TabPane tab="SSO单点登录" key="sso">
              <div className="sso-login-container">
                <div className="sso-description">
                  <GlobalOutlined className="sso-icon" />
                  <p>使用企业SSO账号登录</p>
                  <p className="sso-hint">您将被重定向到SSO认证页面</p>
                </div>
                
                <Button
                  type="primary"
                  size="large"
                  icon={<GlobalOutlined />}
                  onClick={handleSSOLogin}
                  loading={loading}
                  block
                  className="sso-button"
                >
                  SSO 登录
                </Button>
              </div>
            </TabPane>
          </Tabs>

          <Divider className="login-divider">或</Divider>

          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div className="login-tips">
              <p>提示：</p>
              <ul>
                <li>JWT登录：使用系统内置账号密码</li>
                <li>SSO登录：使用企业统一身份认证</li>
              </ul>
            </div>
          </Space>
        </Card>
      </div>
    </div>
  );
}