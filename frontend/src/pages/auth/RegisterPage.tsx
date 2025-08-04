import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Card, message, Space, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useTheme } from '../../hooks/ThemeContext';
import { authApi } from '../../services/authApi';
import './LoginPage.css';

interface RegisterFormValues {
  username: string;
  password: string;
  confirmPassword: string;
  email: string;
  display_name: string;
  agreement: boolean;
}

export function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [form] = Form.useForm();

  const handleRegister = async (values: RegisterFormValues) => {
    try {
      setLoading(true);
      
      // 调用注册API
      await authApi.register({
        username: values.username,
        password: values.password,
        email: values.email,
        display_name: values.display_name
      });
      
      message.success('注册成功！请登录');
      navigate('/login');
    } catch (error: any) {
      message.error(error.message || '注册失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 验证密码一致性
  const validatePassword = (_: any, value: string) => {
    if (!value || form.getFieldValue('password') === value) {
      return Promise.resolve();
    }
    return Promise.reject(new Error('两次输入的密码不一致'));
  };

  return (
    <div className={`login-container ${isDark ? 'dark' : ''}`}>
      <div className="login-content">
        <Card className="login-card" bordered={false}>
          <div className="login-header">
            <h1 className="login-title">用户注册</h1>
            <p className="login-subtitle">创建新账号以访问系统</p>
          </div>

          <Form
            form={form}
            name="register"
            className="login-form"
            onFinish={handleRegister}
            size="large"
            scrollToFirstError
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
                { max: 20, message: '用户名最多20个字符' },
                { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
              ]}
            >
              <Input 
                prefix={<UserOutlined />} 
                placeholder="用户名"
                autoComplete="username"
              />
            </Form.Item>

            <Form.Item
              name="display_name"
              rules={[
                { required: true, message: '请输入显示名称' },
                { max: 50, message: '显示名称最多50个字符' }
              ]}
            >
              <Input 
                prefix={<UserOutlined />} 
                placeholder="显示名称"
              />
            </Form.Item>

            <Form.Item
              name="email"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input 
                prefix={<MailOutlined />} 
                placeholder="邮箱"
                autoComplete="email"
              />
            </Form.Item>
            
            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
                { 
                  pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{6,}$/,
                  message: '密码必须包含大小写字母和数字'
                }
              ]}
              hasFeedback
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                autoComplete="new-password"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              dependencies={['password']}
              hasFeedback
              rules={[
                { required: true, message: '请确认密码' },
                { validator: validatePassword }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="确认密码"
                autoComplete="new-password"
              />
            </Form.Item>

            <Form.Item
              name="agreement"
              valuePropName="checked"
              rules={[
                {
                  validator: (_, value) =>
                    value ? Promise.resolve() : Promise.reject(new Error('请同意服务协议')),
                },
              ]}
            >
              <Checkbox>
                我已阅读并同意 <a href="#">服务协议</a> 和 <a href="#">隐私政策</a>
              </Checkbox>
            </Form.Item>

            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit" 
                className="login-button"
                loading={loading}
                block
              >
                注册
              </Button>
            </Form.Item>

            <Form.Item>
              <Space style={{ width: '100%', justifyContent: 'center' }}>
                已有账号？
                <Link to="/login">立即登录</Link>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      </div>
    </div>
  );
}