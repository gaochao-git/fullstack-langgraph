import { InfoCircleOutlined } from '@ant-design/icons';

export function DevLoginHint() {
  const isDevelopment = import.meta.env.MODE === 'development';
  
  if (!isDevelopment) return null;
  
  return (
    <div style={{
      position: 'fixed',
      bottom: 20,
      right: 20,
      background: '#1890ff',
      color: 'white',
      padding: '12px 20px',
      borderRadius: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      fontSize: 14,
      zIndex: 1000
    }}>
      <InfoCircleOutlined />
      <span>开发模式：用户名 admin / 密码 admin123</span>
    </div>
  );
}