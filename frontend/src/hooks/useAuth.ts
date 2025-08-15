import { create } from 'zustand';
import { authApi } from '@/services/authApi';
import { tokenManager } from '@/utils/tokenManager';

interface Role {
  role_id: string;
  role_name: string;
  role_code?: string;
  is_active?: boolean;
}

interface User {
  id: string;
  username: string;
  display_name: string;
  email: string;
  roles?: Role[] | string[];
  current_role?: Role | string;
  department?: string;
  team?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  ssoLogin: () => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  switchRole: (roleId: string) => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token') || localStorage.getItem('isAuthenticated') === 'true',
  loading: true,

  login: async (username: string, password: string) => {
    try {
      const response = await authApi.login({ username, password });
      
      // 处理业务逻辑错误
      if (response.status === 'error') {
        set({ loading: false });
        throw new Error(response.msg || '登录失败');
      }
      
      // 处理成功响应
      const { access_token, refresh_token, user } = response.data || response;
      
      // 使用tokenManager保存tokens并启动自动刷新
      tokenManager.saveTokens(access_token, refresh_token);
      
      set({ 
        user, 
        token: access_token, 
        isAuthenticated: true,
        loading: false 
      });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },

  ssoLogin: async () => {
    try {
      // 使用CAS登录
      const response = await authApi.getCASLoginUrl();
      // 从响应中提取login_url
      const loginUrl = response?.data?.login_url;
      if (!loginUrl) {
        throw new Error('无法获取CAS登录URL');
      }
      // 重定向到CAS登录页面
      window.location.href = loginUrl;
    } catch (error) {
      throw error;
    }
  },

  logout: async () => {
    const authType = localStorage.getItem('auth_type');
    
    if (authType === 'cas') {
      // CAS登出：清理本地存储并调用CAS登出接口
      localStorage.removeItem('auth_type');
      localStorage.removeItem('user');
      localStorage.removeItem('isAuthenticated');
      
      try {
        // 调用CAS登出接口获取登出URL
        const response = await authApi.casLogout();
        if (response?.data?.logout_url) {
          // 重定向到CAS登出页面
          window.location.href = response.data.logout_url;
          return;
        }
      } catch (error) {
        console.error('CAS logout failed:', error);
      }
    }
    
    // JWT Token登出
    tokenManager.clearTokens();
    set({ 
      user: null, 
      token: null, 
      isAuthenticated: false,
      loading: false 
    });
    // 跳转到登录页
    window.location.href = '/login';
  },

  checkAuth: async () => {
    const authType = localStorage.getItem('auth_type');
    
    // CAS认证检查
    if (authType === 'cas') {
      const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
      const userStr = localStorage.getItem('user');
      
      if (isAuthenticated && userStr) {
        try {
          const user = JSON.parse(userStr);
          set({ 
            user, 
            isAuthenticated: true,
            loading: false 
          });
          return;
        } catch (error) {
          // 清理无效的CAS会话
          localStorage.removeItem('auth_type');
          localStorage.removeItem('user');
          localStorage.removeItem('isAuthenticated');
        }
      }
    }
    
    // JWT Token认证检查
    const token = localStorage.getItem('token');
    if (!token) {
      set({ loading: false, isAuthenticated: false });
      return;
    }

    try {
      const user = await authApi.getCurrentUser();
      set({ 
        user, 
        isAuthenticated: true,
        loading: false 
      });
    } catch (error) {
      tokenManager.clearTokens();
      set({ 
        user: null, 
        token: null, 
        isAuthenticated: false,
        loading: false 
      });
    }
  },

  switchRole: async (roleId: string) => {
    // 将来实现角色切换功能
    // 预期流程：
    // 1. 调用后端API切换角色
    // 2. 获取新的token和权限
    // 3. 更新用户状态和当前角色
    // 4. 刷新菜单和权限
    // TODO: 实现角色切换功能
  }
}));