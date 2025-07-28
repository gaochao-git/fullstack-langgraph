/**
 * 统一API客户端 - 处理新的响应格式
 */

import { baseFetch } from './baseFetch';
import { UnifiedResponse, ApiError, ResponseCode } from '../types/api';

/**
 * 统一API客户端类
 */
export class ApiClient {
  /**
   * 发送请求并处理统一响应格式
   */
  static async request<T>(
    url: string, 
    options?: RequestInit
  ): Promise<T> {
    try {
      const response = await baseFetch(url, options);
      
      // 解析响应数据
      const result: UnifiedResponse<T> = await response.json();
      
      // 检查响应状态
      if (result.status === "ok") {
        return result.data as T;
      } else {
        // 抛出业务异常
        throw new ApiError(
          result.msg || "请求失败",
          result.code || ResponseCode.INTERNAL_ERROR,
          result.status
        );
      }
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // 处理网络错误或其他异常
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new ApiError("网络连接失败", ResponseCode.SERVICE_UNAVAILABLE);
      }
      
      throw new ApiError(
        error instanceof Error ? error.message : "未知错误",
        ResponseCode.INTERNAL_ERROR
      );
    }
  }

  /**
   * GET请求
   */
  static async get<T>(url: string, params?: Record<string, any>): Promise<T> {
    let requestUrl = url;
    
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      
      if (searchParams.toString()) {
        requestUrl += `?${searchParams.toString()}`;
      }
    }
    
    return this.request<T>(requestUrl, {
      method: 'GET',
    });
  }

  /**
   * POST请求
   */
  static async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT请求
   */
  static async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE请求
   */
  static async delete<T>(url: string): Promise<T> {
    return this.request<T>(url, {
      method: 'DELETE',
    });
  }

  /**
   * 处理分页请求的便捷方法
   */
  static async getPaginated<T>(
    url: string, 
    params?: Record<string, any>
  ): Promise<{ items: T[]; pagination: any }> {
    return this.get(url, params);
  }
}

/**
 * 错误处理工具函数
 */
export class ErrorHandler {
  /**
   * 统一错误处理
   */
  static handle(error: unknown): string {
    if (error instanceof ApiError) {
      return error.message;
    }
    
    if (error instanceof Error) {
      return error.message;
    }
    
    return "未知错误";
  }

  /**
   * 获取错误代码
   */
  static getErrorCode(error: unknown): number {
    if (error instanceof ApiError) {
      return error.code;
    }
    
    return ResponseCode.INTERNAL_ERROR;
  }

  /**
   * 检查是否为特定错误类型
   */
  static isNotFoundError(error: unknown): boolean {
    return error instanceof ApiError && error.code === ResponseCode.NOT_FOUND;
  }

  static isValidationError(error: unknown): boolean {
    return error instanceof ApiError && error.code === ResponseCode.VALIDATION_ERROR;
  }

  static isUnauthorizedError(error: unknown): boolean {
    return error instanceof ApiError && error.code === ResponseCode.UNAUTHORIZED;
  }
}