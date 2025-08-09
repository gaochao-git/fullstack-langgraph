import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Spin, message } from 'antd';
import { useAuth } from '@/hooks/useAuth';
import { authApi } from '@/services/authApi';
import { tokenManager } from '@/utils/tokenManager';

export function SSOCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const auth = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');

      if (error) {
        setError(`SSO登录失败: ${searchParams.get('error_description') || error}`);
        message.error('SSO登录失败');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      if (!code) {
        setError('SSO回调缺少授权码');
        message.error('SSO回调参数错误');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      try {
        // 使用授权码换取token
        const response = await authApi.ssoCallback({ code, state: state || undefined });
        const { token, refresh_token, user } = response;
        
        // 使用tokenManager保存tokens
        tokenManager.saveTokens(token, refresh_token);
        auth.user = user;
        auth.token = token;
        auth.isAuthenticated = true;
        
        message.success('SSO登录成功');
        navigate('/', { replace: true });
      } catch (err: any) {
        setError(err.message || 'SSO登录处理失败');
        message.error('SSO登录失败');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, auth]);

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
    }}>
      {error ? (
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: '#ff4d4f', marginBottom: 16 }}>登录失败</h2>
          <p style={{ color: '#666', marginBottom: 24 }}>{error}</p>
          <p style={{ color: '#999' }}>3秒后将跳转到登录页...</p>
        </div>
      ) : (
        <div style={{ textAlign: 'center' }}>
          <Spin size="large" />
          <h2 style={{ marginTop: 24, color: '#333' }}>正在处理SSO登录...</h2>
          <p style={{ color: '#666' }}>请稍候，正在验证您的身份</p>
        </div>
      )}
    </div>
  );
}