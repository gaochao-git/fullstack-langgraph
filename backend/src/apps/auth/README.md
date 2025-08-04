# 认证模块设计文档

## 概述

本认证模块支持JWT和SSO两种认证方式，基于FastAPI和SQLAlchemy实现。

## 数据库表结构

### 1. auth_users - 用户认证信息表
扩展RBAC用户表，存储认证相关的敏感信息：
- 密码哈希（JWT认证）
- MFA设置
- SSO关联信息
- 登录历史和安全设置

### 2. auth_tokens - JWT令牌管理表
管理JWT令牌的生命周期：
- Access Token和Refresh Token记录
- 令牌撤销管理
- 设备和会话追踪

### 3. auth_sessions - SSO会话管理表
管理SSO登录会话：
- SSO提供商会话信息
- OAuth2令牌存储
- 会话状态管理

### 4. auth_login_history - 登录历史表
记录所有登录尝试，用于安全审计：
- 成功/失败记录
- 客户端信息
- 异常检测

### 5. auth_api_keys - API密钥表
管理服务间调用的API密钥：
- 密钥生命周期管理
- 权限范围控制
- IP白名单

### 6. auth_sso_providers - SSO提供商配置表
支持多个SSO提供商：
- OAuth2/SAML配置
- 用户属性映射
- 动态配置管理

## 认证流程

### JWT认证流程
1. 用户提交用户名和密码
2. 验证用户身份和MFA（如启用）
3. 生成Access Token和Refresh Token
4. 返回令牌给客户端
5. 客户端使用Bearer Token访问API
6. 服务端验证令牌有效性

### SSO认证流程
1. 用户选择SSO登录
2. 重定向到SSO提供商
3. 用户在SSO提供商处认证
4. SSO回调到应用
5. 验证回调并获取用户信息
6. 创建或关联本地用户
7. 生成JWT令牌

## API接口

### 认证接口
- `POST /api/v1/auth/login` - JWT登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `POST /api/v1/auth/logout` - 登出
- `GET /api/v1/auth/me` - 获取当前用户信息

### SSO接口
- `GET /api/v1/auth/sso/providers` - 获取SSO提供商列表
- `GET /api/v1/auth/sso/url` - 获取SSO登录URL
- `POST /api/v1/auth/sso/callback` - SSO回调处理

### 密码管理
- `POST /api/v1/auth/change-password` - 修改密码
- `POST /api/v1/auth/forgot-password` - 忘记密码
- `POST /api/v1/auth/reset-password` - 重置密码

### MFA管理
- `POST /api/v1/auth/mfa/enable` - 启用MFA
- `POST /api/v1/auth/mfa/verify` - 验证MFA
- `POST /api/v1/auth/mfa/disable` - 禁用MFA

### API密钥管理
- `POST /api/v1/auth/api-keys` - 创建API密钥
- `GET /api/v1/auth/api-keys` - 获取密钥列表
- `DELETE /api/v1/auth/api-keys/{id}` - 撤销密钥

## 使用示例

### 1. 保护API端点

```python
from fastapi import APIRouter, Depends
from src.apps.auth import get_current_user, CurrentUser

router = APIRouter()

# 基本认证保护
@router.get("/protected")
async def protected_route(current_user: CurrentUser):
    return {"user": current_user}

# 角色保护
from src.apps.auth import require_roles

@router.get("/admin", dependencies=[Depends(require_roles("admin"))])
async def admin_only():
    return {"message": "Admin only content"}
```

### 2. 初始化管理员账户

```bash
# 首次部署时创建管理员账户
curl -X POST http://localhost:8000/api/v1/auth/init/admin \
  -H "Content-Type: application/json" \
  -d '{"password": "your-secure-password"}'
```

### 3. 配置SSO提供商

```python
# 在数据库中添加SSO提供商配置
provider = AuthSSOProvider(
    provider_id="google",
    provider_name="Google",
    provider_type="oauth2",
    client_id="your-client-id",
    client_secret="your-client-secret",
    authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
    scopes="openid profile email",
    is_active=True
)
```

## 环境变量配置

```env
# JWT配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 安全配置
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# SSO配置
SSO_REDIRECT_URI=http://localhost:3000/sso/callback
```

## 安全建议

1. **密码策略**：强制使用强密码（已实现检查）
2. **MFA**：建议为管理员账户启用MFA
3. **令牌管理**：定期清理过期令牌
4. **审计日志**：定期检查登录历史
5. **API密钥**：限制作用域和IP范围
6. **HTTPS**：生产环境必须使用HTTPS

## 待实现功能

1. 邮件发送（密码重置）
2. MFA完整实现
3. SAML SSO支持
4. 权限细粒度控制
5. Redis令牌黑名单
6. 设备指纹识别
7. 异常登录检测