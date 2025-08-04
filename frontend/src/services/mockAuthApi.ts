/**
 * 模拟认证API（用于开发测试）
 */

// 模拟用户数据
const mockUser = {
  id: "1",
  user_id: "admin",
  username: "admin",
  display_name: "系统管理员",
  email: "admin@example.com",
  roles: ["admin"]
};

// 模拟延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const mockAuthApi = {
  // 模拟登录
  async login(data: { username: string; password: string }) {
    await delay(500);
    
    if (data.username === 'admin' && data.password === 'admin123') {
      const token = 'mock-jwt-token-' + Date.now();
      return {
        access_token: token,
        token: token,
        user: mockUser
      };
    }
    
    throw new Error('用户名或密码错误');
  },

  // 模拟获取当前用户
  async getCurrentUser() {
    await delay(300);
    
    const token = localStorage.getItem('token');
    if (token && token.startsWith('mock-jwt-token-')) {
      return mockUser;
    }
    
    throw new Error('未登录');
  },

  // 模拟SSO
  async getSSOUrl() {
    return {
      url: '#'
    };
  },

  // 模拟注册
  async register(data: { username: string; password: string; email: string; display_name: string }) {
    await delay(500);
    
    // 模拟用户名已存在
    if (data.username === 'admin') {
      throw new Error('用户名已存在');
    }
    
    // 模拟邮箱已注册
    if (data.email === 'admin@example.com') {
      throw new Error('邮箱已被注册');
    }

    // 模拟密码强度验证
    if (data.password.length < 6) {
      throw new Error('密码至少6个字符');
    }
    if (!/[A-Z]/.test(data.password)) {
      throw new Error('密码必须包含大写字母');
    }
    if (!/[a-z]/.test(data.password)) {
      throw new Error('密码必须包含小写字母');
    }
    if (!/\d/.test(data.password)) {
      throw new Error('密码必须包含数字');
    }
    
    return {
      success: true,
      message: '注册成功',
      user: {
        id: 'new-user-' + Date.now(),
        username: data.username,
        email: data.email
      }
    };
  }
};