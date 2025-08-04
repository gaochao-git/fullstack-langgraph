import { create } from 'zustand';
import { authApi } from '../services/authApi';

interface User {
  id: string;
  username: string;
  display_name: string;
  email: string;
  roles?: string[];
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
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  loading: true,

  login: async (username: string, password: string) => {
    try {
      const response = await authApi.login({ username, password });
      const { token, user } = response;
      
      localStorage.setItem('token', token);
      set({ 
        user, 
        token, 
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
  }
}));