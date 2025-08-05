import { omind_fetch, omind_post, omind_get } from '../utils/base_api';

// 开发环境使用模拟API
const isDevelopment = import.meta.env.MODE === 'development';
import { mockAuthApi } from './mockAuthApi';

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: {
    id: string;
    username: string;
    display_name: string;
    email: string;
    roles?: string[];
  };
}

interface SSOUrlResponse {
  url: string;
}

interface SSOCallbackRequest {
  code: string;
  state?: string;
}

interface RegisterRequest {
  username: string;
  password: string;
  email: string;
  display_name: string;
}

interface RegisterResponse {
  success: boolean;
  message: string;
  user?: {
    id: string;
    username: string;
    email: string;
  };
}

class AuthApi {
  private baseUrl = '/api/v1/auth';

  /**
   * JWT登录
   */
  async login(data: LoginRequest): Promise<LoginResponse> {
    // 直接调用后端API，不使用mock
    // omind_post 现在默认返回解析后的数据
    const result = await omind_post(`${this.baseUrl}/login`, data);
    
    // 如果返回的是统一格式，数据已经被自动提取
    // 如果不是统一格式，返回整个结果
    return result;
  }

  /**
   * 登出
   */
  async logout(): Promise<void> {
    await omind_post(`${this.baseUrl}/logout`);
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<LoginResponse['user']> {
    // 直接调用后端API，不使用mock
    return await omind_get(`${this.baseUrl}/me`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
  }

  /**
   * 刷新token
   */
  async refreshToken(): Promise<{ token: string }> {
    return await omind_post(`${this.baseUrl}/refresh`, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
  }

  /**
   * 获取SSO登录URL
   */
  async getSSOUrl(): Promise<SSOUrlResponse> {
    // 开发环境使用模拟API
    if (isDevelopment) {
      return mockAuthApi.getSSOUrl();
    }
    
    return await omind_get(`${this.baseUrl}/sso/url`);
  }

  /**
   * SSO回调处理
   */
  async ssoCallback(data: SSOCallbackRequest): Promise<LoginResponse> {
    return await omind_post(`${this.baseUrl}/sso/callback`, data);
  }

  /**
   * 验证token是否有效
   */
  async verifyToken(token: string): Promise<boolean> {
    try {
      const result = await omind_get(`${this.baseUrl}/verify`, {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        showError: false  // 验证失败不显示错误消息
      });
      return result.valid;
    } catch {
      return false;
    }
  }

  /**
   * 用户注册
   */
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    // 直接调用后端API，不使用mock
    return await omind_post(`${this.baseUrl}/register`, data);
  }
}

export const authApi = new AuthApi();