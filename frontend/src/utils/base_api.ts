/**
 * 统一API封装
 * 1. omind_fetch - 普通HTTP请求
 * 2. omind_fetch_stream - 流式请求，主要与大模型通信
 */

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
 * @returns Promise<Response>
 */
export async function omind_fetch(url: string, config: RequestConfig = {}): Promise<Response> {
  const {
    method = 'GET',
    headers = {},
    body,
    timeout = 30000
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
    
    // 检查响应状态
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`请求超时 (${timeout}ms)`);
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