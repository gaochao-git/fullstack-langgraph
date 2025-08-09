import { authApi } from '@/services/authApi';
import { message } from 'antd';

interface TokenPayload {
  exp: number;
  iat: number;
  sub: string;
  username: string;
  type?: string;
}

class TokenManager {
  private refreshPromise: Promise<void> | null = null;
  private readonly TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5分钟

  /**
   * 解析JWT token
   */
  private parseJWT(token: string): TokenPayload | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Failed to parse JWT:', error);
      return null;
    }
  }

  /**
   * 获取token剩余有效时间（毫秒）
   */
  getTokenExpiry(): number {
    const token = localStorage.getItem('token');
    if (!token) return 0;

    const payload = this.parseJWT(token);
    if (!payload || !payload.exp) return 0;

    const expiryTime = payload.exp * 1000; // 转换为毫秒
    const now = Date.now();
    return Math.max(0, expiryTime - now);
  }

  /**
   * 检查token是否需要刷新
   */
  shouldRefreshToken(): boolean {
    const expiry = this.getTokenExpiry();
    return expiry > 0 && expiry < this.TOKEN_REFRESH_THRESHOLD;
  }

  /**
   * 刷新access token
   */
  async refreshAccessToken(): Promise<void> {
    // 如果已经在刷新中，返回现有的promise避免重复请求
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        console.log('Refreshing access token...');
        const response = await authApi.refreshToken(refreshToken);

        if (response.status === 'ok' && response.data) {
          const { access_token } = response.data;
          localStorage.setItem('token', access_token);
          console.log('Access token refreshed successfully');
        } else {
          throw new Error(response.msg || 'Failed to refresh token');
        }
      } catch (error) {
        console.error('Failed to refresh token:', error);
        // 刷新失败，清除token并跳转登录
        this.clearTokens();
        message.error('登录已过期，请重新登录');
        window.location.href = '/login';
        throw error;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  /**
   * 检查并在需要时刷新token
   * 在每次请求前调用
   */
  async checkAndRefreshIfNeeded(): Promise<void> {
    if (this.shouldRefreshToken()) {
      try {
        await this.refreshAccessToken();
      } catch (error) {
        // 错误已在refreshAccessToken中处理
      }
    }
  }

  /**
   * 清除所有tokens
   */
  clearTokens(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
  }

  /**
   * 保存tokens
   */
  saveTokens(accessToken: string, refreshToken?: string): void {
    localStorage.setItem('token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
  }
}

// 导出单例
export const tokenManager = new TokenManager();