import { message } from 'antd';

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

  // 如果有token，自动添加到请求头
  const token = localStorage.getItem('token');
  if (token) {
    init = init || {};
    init.headers = {
      ...init.headers,
      'Authorization': `Bearer ${token}`
    };
  }

  try {
    // 发起请求
    const response = await originalFetch(resource, init);

    // 处理401未授权错误
    if (response.status === 401) {
      localStorage.removeItem('token');
      message.error('登录已过期，请重新登录');
      
      if (config.onUnauthorized) {
        config.onUnauthorized();
      } else {
        // 默认跳转到登录页
        window.location.href = '/login';
      }
    }

    // 处理token刷新（如果响应头中有新token）
    const newToken = response.headers.get('X-New-Token');
    if (newToken) {
      localStorage.setItem('token', newToken);
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