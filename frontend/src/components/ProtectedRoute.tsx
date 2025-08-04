import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Spin } from 'antd';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <Spin 
        size="large" 
        tip="验证中..." 
        spinning={true}
        style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh' 
        }}
      >
        <div style={{ minHeight: '100vh' }} />
      </Spin>
    );
  }

  if (!isAuthenticated) {
    // 保存当前位置，登录后可以返回
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}