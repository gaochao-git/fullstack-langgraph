import { create } from 'zustand';
import { authApi } from '../services/authApi';

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
  isAuthenticated: !!localStorage.getItem('token'),
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
      const { access_token, user } = response.data || response;
      
      localStorage.setItem('token', access_token);
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
      // 获取SSO登录URL
      const { url } = await authApi.getSSOUrl();
      // 重定向到SSO登录页面
      window.location.href = url;
    } catch (error) {
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
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
      localStorage.removeItem('token');
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
    console.log('角色切换功能待实现', roleId);
  }
}));