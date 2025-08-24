import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Spin } from 'antd';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <Spin size="large" />
        <div style={{ color: '#666' }}>加载用户信息...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // 保存当前位置，登录后可以返回
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}