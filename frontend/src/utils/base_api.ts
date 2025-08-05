/**
 * 统一API封装
 * 1. omind_fetch - 普通HTTP请求
 * 2. omind_fetch_stream - 流式请求，主要与大模型通信
 */

import { message } from 'antd';

// 获取基础URL
const getBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
};

// 请求配置接口
export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  // 新增：是否返回原始Response（默认false，返回解析后的数据）
  returnRaw?: boolean;
  // 新增：显示成功消息
  showSuccess?: boolean;
  // 新增：自定义成功消息
  successMessage?: string;
  // 新增：显示错误消息（默认true，当autoHandle为true时）
  showError?: boolean;
  // 新增：自定义错误消息
  errorMessage?: string;
}

// 流式请求配置接口
export interface StreamConfig extends RequestConfig {
  onData?: (data: string) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

/**
 * 普通HTTP请求
 * @param url 请求URL
 * @param config 请求配置
 * @returns Promise<any> 默认返回解析后的数据，如果returnRaw为true则返回Response
 */
export async function omind_fetch(url: string, config: RequestConfig = {}): Promise<any> {
  const {
    method = 'GET',
    headers = {},
    body,
    timeout = 30000,
    returnRaw = false,
    showSuccess = false,
    successMessage,
    showError = true,
    errorMessage
  } = config;

  // 构建完整URL
  const fullUrl = url.startsWith('http') ? url : `${getBaseUrl()}${url}`;

  // 默认请求头
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers
  };

  // 构建fetch配置
  const fetchConfig: RequestInit = {
    method,
    headers: defaultHeaders,
  };

  // 添加请求体（GET请求不需要）
  if (body && method !== 'GET') {
    fetchConfig.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  // 超时控制
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  fetchConfig.signal = controller.signal;

  try {
    const response = await fetch(fullUrl, fetchConfig);
    clearTimeout(timeoutId);
    
    // 如果需要原始Response，直接返回
    if (returnRaw) {
      return response;
    }
    
    // === 默认自动处理逻辑 ===
    
    // 处理非2xx响应
    if (!response.ok) {
      let errorMsg = errorMessage || `请求失败 (${response.status})`;
      
      try {
        const errorData = await response.json();
        // 优先使用后端返回的错误消息
        errorMsg = errorData.msg || errorData.message || errorData.error || errorMsg;
      } catch {
        // 如果解析JSON失败，使用默认错误消息
      }

      if (showError) {
        message.error(errorMsg);
      }
      
      throw new Error(errorMsg);
    }

    // 解析响应
    const responseData = await response.json();

    // 处理统一响应格式
    if ('status' in responseData && responseData.status === 'error') {
      const errorMsg = errorMessage || responseData.msg || responseData.error || '请求失败';
      if (showError) {
        message.error(errorMsg);
      }
      throw new Error(errorMsg);
    }

    // 成功处理
    if (showSuccess) {
      message.success(successMessage || responseData.msg || '操作成功');
    }

    // 返回数据
    if ('status' in responseData && responseData.status === 'ok') {
      return responseData.data;
    }
    
    // 兼容没有统一格式的响应
    return responseData;
    
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error instanceof Error && error.name === 'AbortError') {
      const timeoutError = new Error(`请求超时 (${timeout}ms)`);
      if (showError) {
        message.error(timeoutError.message);
      }
      throw timeoutError;
    }
    
    // 显示错误消息
    if (showError && error instanceof Error) {
      if (!error.message.includes('请求失败')) {
        message.error(error.message);
      }
    }
    
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
  return omind_fetch(url, { ...config, method: 'GET' });
};

/**
 * 便捷方法：POST请求
 */
export const omind_post = (url: string, body?: any, config: Omit<RequestConfig, 'method' | 'body'> = {}) => {
  return omind_fetch(url, { ...config, method: 'POST', body });
};

/**
 * 便捷方法：PUT请求
 */
export const omind_put = (url: string, body?: any, config: Omit<RequestConfig, 'method' | 'body'> = {}) => {
  return omind_fetch(url, { ...config, method: 'PUT', body });
};

/**
 * 便捷方法：DELETE请求
 */
export const omind_del = (url: string, config: Omit<RequestConfig, 'method'> = {}) => {
  return omind_fetch(url, { ...config, method: 'DELETE' });
};

/**
 * 便捷方法：PATCH请求
 */
export const omind_patch = (url: string, body?: any, config: Omit<RequestConfig, 'method' | 'body'> = {}) => {
  return omind_fetch(url, { ...config, method: 'PATCH', body });
};

// 默认导出
export default {
  omind_fetch,
  omind_fetch_stream,
  omind_get,
  omind_post,
  omind_put,
  omind_del,
  omind_patch
};