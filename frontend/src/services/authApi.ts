import { omind_fetch, omind_post, omind_get } from '../utils/base_api';

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

class AuthApi {
  private baseUrl = '/api/v1/auth';

  /**
   * JWT登录
   */
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await omind_post(`${this.baseUrl}/login`, data);
    return response.json();
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
    const response = await omind_get(`${this.baseUrl}/me`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    return response.json();
  }

  /**
   * 刷新token
   */
  async refreshToken(): Promise<{ token: string }> {
    const response = await omind_post(`${this.baseUrl}/refresh`, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    return response.json();
  }

  /**
   * 获取SSO登录URL
   */
  async getSSOUrl(): Promise<SSOUrlResponse> {
    const response = await omind_get(`${this.baseUrl}/sso/url`);
    return response.json();
  }

  /**
   * SSO回调处理
   */
  async ssoCallback(data: SSOCallbackRequest): Promise<LoginResponse> {
    const response = await omind_post(`${this.baseUrl}/sso/callback`, data);
    return response.json();
  }

  /**
   * 验证token是否有效
   */
  async verifyToken(token: string): Promise<boolean> {
    try {
      const response = await omind_get(`${this.baseUrl}/verify`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const result = await response.json();
      return result.valid;
    } catch {
      return false;
    }
  }
}

export const authApi = new AuthApi();