/**
 * 基础fetch封装
 * 统一API基础配置，简化fetch调用
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * 封装的fetch函数
 * @param url - API端点路径（不包含base URL）
 * @param options - fetch选项
 * @returns Promise<Response>
 */
export const baseFetch = async (url: string, options?: RequestInit): Promise<Response> => {
  return fetch(`${API_BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
};