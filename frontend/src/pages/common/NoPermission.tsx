import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export const NoPermission: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f0f2f5'
    }}>
      <Result
        status="403"
        title="403"
        subTitle="抱歉，您暂无访问权限，请联系管理员分配权限。"
        extra={[
          <Button key="back" onClick={handleGoBack}>
            返回上一页
          </Button>,
          <Button key="logout" type="primary" onClick={handleLogout}>
            重新登录
          </Button>
        ]}
      />
    </div>
  );
};