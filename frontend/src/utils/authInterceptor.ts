import { message } from 'antd';
import { tokenManager } from '@/utils/tokenManager';
import { useAuth } from '@/hooks/useAuth';

// 存储原始fetch
const originalFetch = window.fetch;

// 拦截器配置
interface InterceptorConfig {
  onUnauthorized?: () => void;
}

let config: InterceptorConfig = {};

// 配置拦截器
export function configureAuthInterceptor(interceptorConfig: InterceptorConfig) {
  config = interceptorConfig;
}

// 重写fetch以添加认证头和处理401错误
window.fetch = async function(...args) {
  let [resource, init] = args;

  // 如果有token，先检查是否需要刷新
  const token = localStorage.getItem('token');
  if (token) {
    // 在请求前检查并刷新token（如果需要）
    await tokenManager.checkAndRefreshIfNeeded();
    
    // 获取可能已更新的token
    const currentToken = localStorage.getItem('token');
    init = init || {};
    init.headers = {
      ...init.headers,
      'Authorization': `Bearer ${currentToken}`
    };
  }

  try {
    // 发起请求
    let response = await originalFetch(resource, init);

    // 处理401未授权错误
    const isRetry = init && init.headers && (init.headers as any)['X-No-Retry'];
    if (response.status === 401 && !isRetry) {
      const authState = useAuth.getState();
      
      // 根据认证类型处理
      if (authState.authType === 'cas') {
        // CAS认证失败：会话过期
        message.warning('CAS会话已过期，请重新登录');
        // CAS不清除本地状态，保留用户信息以便重新登录
        if (config.onUnauthorized) {
          config.onUnauthorized();
        } else {
          // 跳转到登录页，用户可以选择SSO登录
          window.location.href = '/login';
        }
      } else if (authState.authType === 'jwt') {
        // JWT认证失败：尝试刷新token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          try {
            await tokenManager.refreshAccessToken();
            
            // 用新token重试原请求
            const newToken = localStorage.getItem('token');
            if (newToken) {
              init = init || {};
              init.headers = {
                ...init.headers,
                'Authorization': `Bearer ${newToken}`,
                'X-No-Retry': 'true' // 标记避免递归重试
              };
              response = await originalFetch(resource, init);
            }
          } catch (refreshError) {
            // refresh失败，tokenManager已经处理了清理和跳转
            return response;
          }
        } else {
          // 没有refresh token，直接清理并跳转
          tokenManager.clearTokens();
          authState.updateAuthState(null, null);
          message.error('登录已过期，请重新登录');
          
          if (config.onUnauthorized) {
            config.onUnauthorized();
          } else {
            window.location.href = '/login';
          }
        }
      } else {
        // 无认证信息
        message.error('请先登录');
        window.location.href = '/login';
      }
    }

    // 处理token刷新（如果响应头中有新token）
    const newToken = response.headers.get('X-New-Token');
    if (newToken) {
      tokenManager.saveTokens(newToken);
    }

    return response;
  } catch (error) {
    // 网络错误等
    throw error;
  }
};

// 恢复原始fetch（如需要）
export function restoreOriginalFetch() {
  window.fetch = originalFetch;
}

// 从JWT token或SSO用户信息中获取用户名
export function getCurrentUsername(): string {
  try {
    // 首先检查认证类型
    const authType = localStorage.getItem('auth_type');
    
    // SSO/CAS认证：从localStorage的user字段获取
    if (authType === 'cas') {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr);
        return user.username || 'anonymous';
      }
    }
    
    // JWT认证：从token中解析
    const token = localStorage.getItem('token');
    if (token) {
      // 解析JWT token
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(jsonPayload);
      return payload.username || 'anonymous';
    }
    
    // 如果都没有，返回anonymous
    return 'anonymous';
  } catch (error) {
    console.error('Failed to get username:', error);
    return 'anonymous';
  }
}