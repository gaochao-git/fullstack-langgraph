/**
 * 统一API封装
 * 1. omind_axios - 普通HTTP请求（使用 axios）
 * 2. omind_fetch_stream - 流式请求，主要与大模型通信（使用 fetch）
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { tokenManager } from './tokenManager';
import { useAuth } from '@/hooks/useAuth';
import { message } from 'antd';

// 移除 antd 依赖，让组件自己处理消息提示

// 全局请求计数器
let activeRequests = 0;

// 全局loading控制器
export const globalLoadingController = {
  show: () => {},
  hide: () => {},
  setHandler: (handler: { show: () => void; hide: () => void }) => {
    globalLoadingController.show = handler.show;
    globalLoadingController.hide = handler.hide;
  }
};

// 获取基础URL - 导出以供其他模块使用
export const getBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || '';
};

// 扩展 Axios 配置类型
declare module 'axios' {
  export interface AxiosRequestConfig {
    showLoading?: boolean;
    returnRaw?: boolean;
  }
}

// 创建 axios 实例
const axiosInstance: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 包含Cookie，支持CAS session认证
});

// 请求拦截器
axiosInstance.interceptors.request.use(
  async (config) => {
    // 添加认证头
    const token = localStorage.getItem('token');
    if (token) {
      // 检查并刷新 token
      await tokenManager.checkAndRefreshIfNeeded();
      const currentToken = localStorage.getItem('token');
      config.headers.Authorization = `Bearer ${currentToken}`;
    }
    
    // 显示全局loading
    if (config.showLoading !== false) {
      activeRequests++;
      if (activeRequests === 1) {
        globalLoadingController.show();
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
axiosInstance.interceptors.response.use(
  (response) => {
    // 隐藏全局loading
    if (response.config.showLoading !== false) {
      activeRequests--;
      if (activeRequests === 0) {
        globalLoadingController.hide();
      }
    }
    
    // 处理新 token
    const newToken = response.headers['x-new-token'];
    if (newToken) {
      tokenManager.saveTokens(newToken);
    }
    
    // 处理业务错误（200状态码但包含错误）
    const data = response.data;
    if (data && typeof data === 'object' && data.status === 'error' && (data.code === 401 || data.msg?.includes('认证凭据'))) {
      const authState = useAuth.getState();
      
      // 清理认证状态
      tokenManager.clearTokens();
      authState.updateAuthState(null, null);
      
      // 显示错误消息
      message.error(data.msg || '请先登录');
      
      // 跳转到登录页
      setTimeout(() => {
        window.location.href = '/login';
      }, 1500);
      
      return Promise.reject(new Error(data.msg || '认证失败'));
    }
    
    // 如果配置了 returnRaw，返回完整响应
    if (response.config.returnRaw) {
      return response;
    }
    
    // 默认返回数据部分
    return response.data;
  },
  async (error: AxiosError) => {
    // 隐藏全局loading
    if (error.config?.showLoading !== false) {
      activeRequests--;
      if (activeRequests === 0) {
        globalLoadingController.hide();
      }
    }
    
    // 处理 401 错误
    if (error.response?.status === 401) {
      const authState = useAuth.getState();
      const originalRequest = error.config!;
      
      // 避免无限重试
      if (!(originalRequest as any)._retry) {
        (originalRequest as any)._retry = true;
        
        if (authState.authType === 'cas') {
          message.warning('CAS会话已过期，请重新登录');
          setTimeout(() => {
            window.location.href = '/login';
          }, 1500);
        } else if (authState.authType === 'jwt') {
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              await tokenManager.refreshAccessToken();
              
              // 使用新 token 重试
              const newToken = localStorage.getItem('token');
              originalRequest.headers!.Authorization = `Bearer ${newToken}`;
              return axiosInstance(originalRequest);
            } catch (refreshError) {
              // refresh失败，tokenManager已经处理了清理和跳转
              tokenManager.clearTokens();
              authState.updateAuthState(null, null);
              message.error('登录已过期，请重新登录');
              setTimeout(() => {
                window.location.href = '/login';
              }, 1500);
            }
          } else {
            // 没有refresh token，直接清理并跳转
            tokenManager.clearTokens();
            authState.updateAuthState(null, null);
            message.error('登录已过期，请重新登录');
            setTimeout(() => {
              window.location.href = '/login';
            }, 1500);
          }
        } else {
          // 无认证信息
          message.error('请先登录');
          window.location.href = '/login';
        }
      }
    }
    
    // 处理超时
    if (error.code === 'ECONNABORTED') {
      const timeoutError = new Error(`请求超时 (${error.config?.timeout}ms)`);
      return Promise.reject(timeoutError);
    }
    
    // 提取错误信息
    let errorMsg = error.message || '请求失败';
    
    if (error.response?.data) {
      const data = error.response.data as any;
      errorMsg = data.msg || data.message || data.error || errorMsg;
    }
    
    if (error.response?.status) {
      errorMsg = `${errorMsg} (${error.response.status})`;
    }
    
    return Promise.reject(new Error(errorMsg));
  }
);

// 请求配置接口
export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  // 新增：是否返回原始Response（默认false，返回解析后的数据）
  returnRaw?: boolean;
  // 新增：是否显示全局loading（默认true）
  showLoading?: boolean;
  // 新增：上传进度回调
  onUploadProgress?: (progressEvent: any) => void;
}

// 流式请求配置接口
export interface StreamConfig extends RequestConfig {
  onData?: (data: string) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

/**
 * 普通HTTP请求（使用 axios）
 * @param url 请求URL
 * @param config 请求配置
 * @returns Promise<any> 默认返回解析后的数据，如果returnRaw为true则返回完整响应
 */
export async function omind_axios(url: string, config: RequestConfig = {}): Promise<any> {
  const {
    method = 'GET',
    headers = {},
    body,
    timeout = 30000,
    returnRaw = false,
    showLoading = true,
    onUploadProgress
  } = config;

  // 构建 axios 配置
  const axiosConfig: AxiosRequestConfig = {
    url,
    method: method as any,
    headers,
    timeout,
    showLoading,
    returnRaw,
  };

  // 添加上传进度回调
  if (onUploadProgress) {
    axiosConfig.onUploadProgress = onUploadProgress;
  }

  // 添加请求体
  if (body) {
    if (method === 'GET') {
      axiosConfig.params = body;
    } else {
      axiosConfig.data = body;
    }
  }

  try {
    const response = await axiosInstance.request(axiosConfig);
    return response;
  } catch (error) {
    // 错误已经在拦截器中处理，直接抛出
    throw error;
  }
}

/**
 * 流式请求，主要与大模型通信
 * @param url 请求URL
 * @param config 流式请求配置
 * @returns Promise<void>
 */
export async function omind_fetch_stream(url: string, config: StreamConfig = {}): Promise<void> {
  const {
    method = 'POST',
    headers = {},
    body,
    timeout = 300000, // 流式请求默认5分钟超时
    onData,
    onError,
    onComplete
  } = config;

  // 构建完整URL
  const fullUrl = url.startsWith('http') ? url : `${getBaseUrl()}${url}`;

  // 默认请求头（流式请求）
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
    'Cache-Control': 'no-cache',
    ...headers
  };

  // 构建fetch配置
  const fetchConfig: RequestInit = {
    method,
    headers: defaultHeaders,
    credentials: 'include', // 包含Cookie，支持CAS session认证
  };

  // 添加请求体
  if (body) {
    fetchConfig.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  // 超时控制
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  fetchConfig.signal = controller.signal;

  try {
    const response = await fetch(fullUrl, fetchConfig);
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    // 检查是否支持流式响应
    if (!response.body) {
      throw new Error('响应不支持流式读取');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          onComplete?.();
          break;
        }

        // 解码数据
        const chunk = decoder.decode(value, { stream: true });
        
        // 处理Server-Sent Events格式
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.trim()) {
            // 移除 'data: ' 前缀（如果存在）
            const data = line.startsWith('data: ') ? line.slice(6) : line;
            if (data.trim() && data !== '[DONE]') {
              onData?.(data);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error instanceof Error && error.name === 'AbortError') {
      const timeoutError = new Error(`流式请求超时 (${timeout}ms)`);
      onError?.(timeoutError);
      throw timeoutError;
    }
    
    onError?.(error as Error);
    throw error;
  }
}

/**
 * 便捷方法：GET请求
 */
export const omind_get = (url: string, config: Omit<RequestConfig, 'method'> = {}) => {
  return omind_axios(url, { ...config, method: 'GET' });
};

/**
 * 便捷方法：POST请求
 */
export const omind_post = (url: string, body?: any, config: Omit<RequestConfig, 'method' | 'body'> = {}) => {
  return omind_axios(url, { ...config, method: 'POST', body });
};

/**
 * 便捷方法：PUT请求
 */
export const omind_put = (url: string, body?: any, config: Omit<RequestConfig, 'method' | 'body'> = {}) => {
  return omind_axios(url, { ...config, method: 'PUT', body });
};

/**
 * 便捷方法：DELETE请求
 */
export const omind_del = (url: string, config: Omit<RequestConfig, 'method'> = {}) => {
  return omind_axios(url, { ...config, method: 'DELETE' });
};

/**
 * 便捷方法：PATCH请求
 */
export const omind_patch = (url: string, body?: any, config: Omit<RequestConfig, 'method' | 'body'> = {}) => {
  return omind_axios(url, { ...config, method: 'PATCH', body });
};

/**
 * 聊天专用流式请求
 * 处理 LangGraph 的 SSE 事件格式
 */
export interface ChatStreamConfig {
  method?: 'POST';
  body?: any;
  signal?: AbortSignal;
  onEvent?: (eventType: string, eventData: any) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export async function omind_chat_stream(url: string, config: ChatStreamConfig = {}): Promise<void> {
  const {
    method = 'POST',
    body,
    signal,
    onEvent,
    onError,
    onComplete
  } = config;

  // 添加认证token
  const token = localStorage.getItem('token');
  if (token) {
    await tokenManager.checkAndRefreshIfNeeded();
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
    ...(token && { 'Authorization': `Bearer ${localStorage.getItem('token')}` })
  };

  try {
    const response = await fetch(url.startsWith('http') ? url : `${getBaseUrl()}${url}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal,
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw { 
        code: response.status, 
        message: error.message || `请求失败: ${response.status}`,
        status: response.status 
      };
    }

    // 处理 SSE 流
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let currentEvent = '';

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line === '') continue;
        
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          try {
            const eventData = JSON.parse(line.slice(6));
            onEvent?.(currentEvent || 'data', eventData);
          } catch (e) {
            console.error('Failed to parse SSE data:', e, line);
          }
        }
      }
    }

    onComplete?.();
  } catch (error: any) {
    if (error.name !== 'AbortError') {
      onError?.(error);
    }
    throw error;
  }
}

// 导出 axios 实例，供需要自定义配置的场景使用
export { axiosInstance };

// 默认导出
export default {
  omind_axios,
  omind_fetch_stream,
  omind_chat_stream,
  omind_get,
  omind_post,
  omind_put,
  omind_del,
  omind_patch
};