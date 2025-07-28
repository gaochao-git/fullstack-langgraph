/**
 * 全局统一API响应格式类型定义
 */

// 响应状态枚举
export type ResponseStatus = "ok" | "error";

// 统一响应格式
export interface UnifiedResponse<T = any> {
  status: ResponseStatus;
  msg: string;
  data?: T;
  code: number;
}

// 分页数据格式
export interface PaginatedData<T> {
  items: T[];
  pagination: {
    page: number;
    size: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// API响应状态码
export enum ResponseCode {
  // 成功状态码
  SUCCESS = 200,
  CREATED = 201,
  
  // 客户端错误
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  METHOD_NOT_ALLOWED = 405,
  CONFLICT = 409,
  VALIDATION_ERROR = 422,
  
  // 服务器错误
  INTERNAL_ERROR = 500,
  NOT_IMPLEMENTED = 501,
  BAD_GATEWAY = 502,
  SERVICE_UNAVAILABLE = 503,
}

// API异常类
export class ApiError extends Error {
  constructor(
    public message: string,
    public code: number,
    public status: ResponseStatus = "error"
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// 分页查询参数
export interface PaginationParams {
  page?: number;
  size?: number;
}