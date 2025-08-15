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
  authType: 'jwt' | 'cas' | null;
  login: (username: string, password: string) => Promise<void>;
  ssoLogin: () => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  switchRole: (roleId: string) => Promise<void>;
  // 新增：统一的状态更新方法
  updateAuthState: (user: User | null, authType: 'jwt' | 'cas' | null) => void;
}

// 辅助函数：从localStorage恢复认证状态
const getInitialAuthState = () => {
  const authType = localStorage.getItem('auth_type');
  const token = localStorage.getItem('token');
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
  const userStr = localStorage.getItem('user');
  
  let user = null;
  if (userStr) {
    try {
      user = JSON.parse(userStr);
    } catch (e) {
      console.error('Failed to parse user from localStorage:', e);
    }
  }
  
  return {
    user,
    token,
    isAuthenticated: !!token || isAuthenticated,
    authType: (authType as 'jwt' | 'cas' | null) || (token ? 'jwt' : null),
    loading: false
  };
};

const initialState = getInitialAuthState();

export const useAuth = create<AuthState>((set, get) => ({
  ...initialState,
  loading: true, // 初始加载状态

  // 统一的状态更新方法
  updateAuthState: (user: User | null, authType: 'jwt' | 'cas' | null) => {
    // 统一清理旧数据
    const clearAuthData = () => {
      localStorage.removeItem('auth_type');
      localStorage.removeItem('isAuthenticated');
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
    };
    
    if (!user || !authType) {
      // 清空认证
      clearAuthData();
      set({
        user: null,
        authType: null,
        isAuthenticated: false,
        token: null,
        loading: false
      });
      return;
    }
    
    // 根据认证类型保存数据
    if (authType === 'cas') {
      // CAS认证：基于会话
      localStorage.setItem('auth_type', 'cas');
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('user', JSON.stringify(user));
      // CAS不使用token
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
    } else if (authType === 'jwt') {
      // JWT认证：基于令牌
      localStorage.setItem('auth_type', 'jwt');
      localStorage.setItem('user', JSON.stringify(user));
      // JWT不使用isAuthenticated标记
      localStorage.removeItem('isAuthenticated');
    }
    
    // 更新状态
    set({
      user,
      authType,
      isAuthenticated: true,
      loading: false
    });
  },

  login: async (username: string, password: string) => {
    try {
      set({ loading: true });
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
      
      // 更新认证状态
      get().updateAuthState(user, 'jwt');
      set({ token: access_token });
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
    const { authType } = get();
    
    if (authType === 'cas') {
      // CAS登出：清理本地存储
      get().updateAuthState(null, null);
      
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
    
    // JWT Token登出或CAS登出失败的fallback
    tokenManager.clearTokens();
    get().updateAuthState(null, null);
    set({ token: null });
    
    // 跳转到登录页
    window.location.href = '/login';
  },

  checkAuth: async () => {
    const authType = localStorage.getItem('auth_type');
    const token = localStorage.getItem('token');
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
    const userStr = localStorage.getItem('user');
    
    // 无认证信息
    if (!authType && !token && !isAuthenticated) {
      set({ loading: false, isAuthenticated: false });
      return;
    }
    
    try {
      // CAS认证检查
      if (authType === 'cas' && isAuthenticated && userStr) {
        // 尝试验证CAS会话是否仍然有效
        try {
          const currentUser = await authApi.getCurrentUser();
          // 如果能获取到用户信息，说明CAS会话有效
          get().updateAuthState(currentUser, 'cas');
        } catch (error) {
          // CAS会话可能已过期，保持本地状态但标记需要重新认证
          const user = JSON.parse(userStr);
          set({
            user,
            authType: 'cas',
            isAuthenticated: true,
            loading: false
          });
        }
        return;
      }
      
      // JWT Token认证检查
      if (token) {
        const user = await authApi.getCurrentUser();
        get().updateAuthState(user, 'jwt');
        set({ token });
        return;
      }
      
      // 其他情况，清空认证
      get().updateAuthState(null, null);
    } catch (error) {
      console.error('Auth check failed:', error);
      // 根据认证类型处理错误
      if (authType === 'jwt') {
        tokenManager.clearTokens();
      }
      get().updateAuthState(null, null);
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