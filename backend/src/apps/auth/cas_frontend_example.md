# CAS前端集成示例

## 1. CAS登录流程

### 1.1 检查认证状态
```javascript
// 检查是否已经通过CAS认证
async function checkCASAuth() {
  try {
    const response = await fetch('/api/v1/cas/check', {
      credentials: 'include' // 重要：携带Cookie
    });
    const data = await response.json();
    
    if (data.data.authenticated) {
      console.log('已认证用户:', data.data.user);
      return data.data.user;
    }
    return null;
  } catch (error) {
    console.error('检查认证状态失败:', error);
    return null;
  }
}
```

### 1.2 跳转到CAS登录
```javascript
// 获取CAS登录URL并跳转
async function loginWithCAS() {
  try {
    const response = await fetch('/api/v1/cas/login');
    const data = await response.json();
    
    if (data.status === 'ok' && data.data.login_url) {
      // 跳转到CAS登录页面
      window.location.href = data.data.login_url;
    }
  } catch (error) {
    console.error('获取CAS登录URL失败:', error);
  }
}
```

### 1.3 处理CAS回调
```javascript
// 在回调页面处理CAS返回
// 路由: /sso/callback?ticket=ST-xxx
async function handleCASCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const ticket = urlParams.get('ticket');
  
  if (!ticket) {
    console.error('缺少CAS票据');
    return;
  }
  
  try {
    const response = await fetch(`/api/v1/cas/callback?ticket=${ticket}`, {
      credentials: 'include'
    });
    const data = await response.json();
    
    if (data.status === 'ok') {
      console.log('CAS登录成功:', data.data.user);
      // 跳转到主页或之前的页面
      window.location.href = '/dashboard';
    } else {
      console.error('CAS认证失败:', data.message);
    }
  } catch (error) {
    console.error('处理CAS回调失败:', error);
  }
}
```

## 2. CAS登出流程

### 2.1 单点登出
```javascript
async function logoutFromCAS() {
  try {
    const response = await fetch('/api/v1/cas/logout', {
      method: 'POST',
      credentials: 'include'
    });
    const data = await response.json();
    
    if (data.status === 'ok' && data.data.redirect_required) {
      // 跳转到CAS登出URL，实现单点登出
      window.location.href = data.data.logout_url;
    }
  } catch (error) {
    console.error('CAS登出失败:', error);
  }
}
```

## 3. 访问受保护的资源

### 3.1 带认证的API调用
```javascript
// 所有CAS保护的API调用都需要携带Cookie
async function fetchProtectedResource() {
  try {
    const response = await fetch('/api/v1/cas/protected-resource', {
      credentials: 'include' // 必须：携带session cookie
    });
    
    if (response.status === 401) {
      // 未认证，跳转到CAS登录
      await loginWithCAS();
      return;
    }
    
    const data = await response.json();
    console.log('受保护的资源:', data);
  } catch (error) {
    console.error('访问受保护资源失败:', error);
  }
}
```

## 4. 会话管理

### 4.1 查看活跃会话
```javascript
async function getActiveSessions() {
  try {
    const response = await fetch('/api/v1/cas/sessions/active', {
      credentials: 'include'
    });
    const data = await response.json();
    
    if (data.status === 'ok') {
      console.log('活跃会话:', data.data.sessions);
      return data.data.sessions;
    }
  } catch (error) {
    console.error('获取会话列表失败:', error);
  }
}
```

### 4.2 终止其他会话
```javascript
async function terminateSession(sessionId) {
  try {
    const response = await fetch('/api/v1/cas/sessions/terminate', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ session_id: sessionId })
    });
    
    const data = await response.json();
    if (data.status === 'ok') {
      console.log('会话已终止');
    }
  } catch (error) {
    console.error('终止会话失败:', error);
  }
}
```

## 5. React组件示例

```jsx
import React, { useState, useEffect } from 'react';

function CASAuthButton() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    checkAuth();
  }, []);
  
  async function checkAuth() {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/cas/check', {
        credentials: 'include'
      });
      const data = await response.json();
      
      if (data.data.authenticated) {
        setUser(data.data.user);
      }
    } finally {
      setLoading(false);
    }
  }
  
  async function handleLogin() {
    const response = await fetch('/api/v1/cas/login');
    const data = await response.json();
    window.location.href = data.data.login_url;
  }
  
  async function handleLogout() {
    const response = await fetch('/api/v1/cas/logout', {
      method: 'POST',
      credentials: 'include'
    });
    const data = await response.json();
    window.location.href = data.data.logout_url;
  }
  
  if (loading) return <div>加载中...</div>;
  
  if (user) {
    return (
      <div>
        <span>欢迎, {user.display_name}</span>
        <button onClick={handleLogout}>登出</button>
      </div>
    );
  }
  
  return <button onClick={handleLogin}>CAS登录</button>;
}
```

## 6. 配置说明

### 6.1 前端配置
```javascript
// config.js
export const CAS_CONFIG = {
  // CAS回调地址，需要与后端配置一致
  callbackUrl: '/sso/callback',
  
  // 登录成功后的默认跳转页面
  defaultRedirect: '/dashboard',
  
  // API基础路径
  apiBase: '/api/v1/cas'
};
```

### 6.2 路由配置
```javascript
// React Router 示例
import { BrowserRouter, Route, Routes } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/sso/callback" element={<CASCallback />} />
        <Route path="/dashboard" element={<ProtectedDashboard />} />
        {/* 其他路由 */}
      </Routes>
    </BrowserRouter>
  );
}
```

## 7. 注意事项

1. **Cookie设置**：所有CAS相关的API调用必须设置 `credentials: 'include'`
2. **CORS配置**：确保后端正确配置了CORS，允许携带Cookie
3. **HTTPS**：生产环境必须使用HTTPS，否则Cookie可能无法正常工作
4. **会话超时**：定期检查会话状态，超时后引导用户重新登录
5. **单点登出**：登出时必须跳转到CAS服务器，确保所有应用都登出

## 8. 错误处理

```javascript
// 统一的错误处理
async function casApiCall(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include' // 始终携带Cookie
    });
    
    if (response.status === 401) {
      // 未认证，跳转到CAS登录
      const loginResp = await fetch('/api/v1/cas/login');
      const loginData = await loginResp.json();
      window.location.href = loginData.data.login_url;
      return;
    }
    
    const data = await response.json();
    
    if (data.status !== 'ok') {
      throw new Error(data.message || '请求失败');
    }
    
    return data.data;
  } catch (error) {
    console.error('CAS API调用失败:', error);
    throw error;
  }
}
```