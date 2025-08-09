import { message } from 'antd';
import { tokenManager } from '@/utils/tokenManager';

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
      // 尝试刷新token
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
        message.error('登录已过期，请重新登录');
        
        if (config.onUnauthorized) {
          config.onUnauthorized();
        } else {
          window.location.href = '/login';
        }
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