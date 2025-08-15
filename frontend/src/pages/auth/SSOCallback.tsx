import { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Spin, message } from 'antd';
import { useAuth } from '@/hooks/useAuth';
import { authApi } from '@/services/authApi';
import { tokenManager } from '@/utils/tokenManager';
import { MenuApiService } from '@/services/menuApi';

export function SSOCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const auth = useAuth();
  const isProcessing = useRef(false);

  useEffect(() => {
    const handleCallback = async () => {
      // 防止重复处理
      if (isProcessing.current) return;
      isProcessing.current = true;
      // 检查是否是CAS回调（有ticket参数）
      const ticket = searchParams.get('ticket');
      if (ticket) {
        // 处理CAS回调
        try {
          const response = await authApi.casCallback(ticket);
          
          // CAS使用session认证，不返回JWT token
          if (response?.data?.user) {
            // 使用统一的updateAuthState方法更新状态
            const { updateAuthState } = useAuth.getState();
            updateAuthState(response.data.user, 'cas');
            
            message.success(response.data.message || 'CAS登录成功');
            
            // 获取用户首个可访问的页面路径
            const getFirstAccessiblePath = async () => {
              try {
                // 获取用户菜单
                const userMenuPermission = await MenuApiService.getUserMenus();
                const menus = userMenuPermission.menus || [];
                
                // 递归查找第一个有路径的菜单
                const findFirstPath = (menuList: any[]): string | null => {
                  for (const menu of menuList) {
                    if (menu.route_path && menu.show_menu === 1 && menu.menu_component) {
                      return menu.route_path;
                    }
                    if (menu.children && menu.children.length > 0) {
                      const childPath = findFirstPath(menu.children);
                      if (childPath) return childPath;
                    }
                  }
                  return null;
                };
                
                const firstPath = findFirstPath(menus);
                if (!firstPath) {
                  // 如果用户没有任何可访问的菜单，跳转到一个无权限页面
                  message.warning('您暂无可访问的页面，请联系管理员分配权限');
                  return '/no-permission';
                }
                return firstPath;
              } catch (error) {
                console.error('Failed to get user menus:', error);
                message.error('获取用户菜单失败');
                return '/';
              }
            };
            
            // 延迟跳转，确保状态更新完成
            setTimeout(async () => {
              const targetPath = await getFirstAccessiblePath();
              navigate(targetPath, { replace: true });
            }, 100);
          } else {
            throw new Error('CAS响应格式错误');
          }
        } catch (err: any) {
          setError(err.message || 'CAS登录处理失败');
          message.error('CAS登录失败');
          setTimeout(() => navigate('/login'), 3000);
        }
        return;
      }

      // 处理其他SSO回调（OAuth2等）
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
  }, []); // 空依赖数组，只在组件挂载时执行一次

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