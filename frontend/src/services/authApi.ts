import { omind_fetch, omind_post, omind_get } from '@/utils/base_api';

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
  expires_in?: number;
  user: {
    id: string;
    user_id?: string;
    username: string;
    display_name: string;
    email: string;
    roles?: any[];
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
  async login(data: LoginRequest) {
    // 直接透传，返回原始响应结构
    return await omind_post(`${this.baseUrl}/login`, data);
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
    const response = await omind_get(`${this.baseUrl}/me`, { showLoading: false });
    
    // 处理统一响应格式
    if (response.status === 'ok' && response.data) {
      // 返回 data.user 而不是 data
      return response.data.user || response.data;
    } else if (response.status === 'error') {
      throw new Error(response.msg || '获取用户信息失败');
    }
    
    // 兼容直接返回用户数据的情况
    return response;
  }

  /**
   * 刷新token
   */
  async refreshToken(refreshToken: string) {
    return await omind_post(`${this.baseUrl}/refresh`, {
      refresh_token: refreshToken
    });
  }

  /**
   * 获取SSO登录URL
   */
  async getSSOUrl(): Promise<SSOUrlResponse> {
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
        showLoading: false,  // 验证token不需要显示loading
      });
      return result.valid;
    } catch {
      return false;
    }
  }

  /**
   * 用户注册
   */
  async register(data: RegisterRequest) {
    // 直接透传，返回原始响应结构
    return await omind_post(`${this.baseUrl}/register`, data);
  }

  /**
   * 获取密码策略
   */
  async getPasswordPolicy(): Promise<{
    min_length: number;
    require_uppercase: boolean;
    require_lowercase: boolean;
    require_digits: boolean;
    require_special_chars: boolean;
    requirements_text: string[];
    special_chars: string;
  }> {
    return await omind_get(`${this.baseUrl}/password-policy`);
  }

  /**
   * 获取CAS登录URL
   */
  async getCASLoginUrl(): Promise<{ url: string }> {
    return await omind_get(`${this.baseUrl}/cas/login`);
  }

  /**
   * 获取CAS登出URL
   */
  async getCASLogoutUrl(redirectUrl?: string): Promise<{ url: string }> {
    const params = redirectUrl ? `?redirect_url=${encodeURIComponent(redirectUrl)}` : '';
    return await omind_get(`${this.baseUrl}/cas/logout${params}`);
  }

  /**
   * 处理CAS回调
   */
  async casCallback(ticket: string): Promise<LoginResponse> {
    return await omind_get(`${this.baseUrl}/cas/callback?ticket=${ticket}`);
  }

  /**
   * CAS登出
   */
  async casLogout(): Promise<{ logout_url: string }> {
    return await omind_get(`${this.baseUrl}/cas/logout`);
  }
}

export const authApi = new AuthApi();