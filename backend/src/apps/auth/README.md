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

### 3. auth_sessions - 会话管理表
管理用户登录会话：
- CAS会话信息
- 会话状态管理
- 单点登出支持

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

## 认证流程

### JWT认证流程
1. 用户提交用户名和密码
2. 验证用户身份和MFA（如启用）
3. 生成Access Token和Refresh Token
4. 返回令牌给客户端
5. 客户端使用Bearer Token访问API
6. 服务端验证令牌有效性

### CAS认证流程
1. 用户选择CAS登录
2. 重定向到CAS服务器
3. 用户在CAS服务器认证
4. CAS回调到应用
5. 验证票据并获取用户信息
6. 创建或关联本地用户
7. 创建会话（Session模式）

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

### 3. 配置CAS认证

CAS认证通过环境变量配置，参见下方的环境变量配置部分。

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

# SSO配置（通用）
SSO_REDIRECT_URI=http://localhost:3000/sso/callback

# CAS配置（接入公司CAS必需）
CAS_SERVER_URL=https://your-cas-server.com/cas     # CAS服务器地址
CAS_SERVICE_URL=http://your-app.com/sso/callback   # 应用回调地址（需在CAS服务器注册）
CAS_VERSION=3                                       # CAS协议版本（默认3）
CAS_VERIFY_SSL=true                                 # 是否验证SSL证书（生产环境必须true）
CAS_SESSION_TIMEOUT=36000                           # 会话超时时间（秒，默认10小时）
CAS_SINGLE_LOGOUT_ENABLED=true                      # 是否启用单点登出
```

## CAS集成配置说明

### 必需配置参数

1. **CAS_SERVER_URL**
   - 说明：公司CAS服务器的基础URL
   - 示例：`https://sso.company.com/cas`
   - 注意：不要包含具体路径如/login或/logout

2. **CAS_SERVICE_URL**
   - 说明：应用的回调URL，用户登录后CAS将重定向到此地址
   - 示例：`https://app.company.com/sso/callback`
   - 注意：
     - 必须与CAS服务器中注册的Service URL完全一致
     - 生产环境必须使用HTTPS
     - 路径固定为 `/sso/callback`

3. **CAS_VERIFY_SSL**
   - 说明：是否验证CAS服务器的SSL证书
   - 生产环境：必须设置为 `true`
   - 开发环境：如果使用自签名证书可设置为 `false`

### 可选配置参数

4. **CAS_VERSION**
   - 说明：CAS协议版本
   - 默认值：`3`
   - 可选值：`2` 或 `3`

5. **CAS_SESSION_TIMEOUT**
   - 说明：CAS会话超时时间（秒）
   - 默认值：`36000`（10小时）
   - 建议：与公司CAS服务器的会话超时保持一致

6. **CAS_SINGLE_LOGOUT_ENABLED**
   - 说明：是否启用单点登出
   - 默认值：`true`
   - 功能：用户在CAS服务器登出时，所有应用同时登出

### CAS属性映射配置

CAS返回的用户属性需要映射到本地用户表，配置文件位于：
`src/shared/core/cas_mapping_config.yaml`

```yaml
# 示例：将CAS属性映射到本地字段
cas_attribute_mapping:
  direct_mapping:
    username: user_name        # CAS的username -> 表的user_name
    display_name: display_name  # CAS的display_name -> 表的display_name  
    email: email               # CAS的email -> 表的email
    
  # 如果CAS返回的是DN格式的组织信息
  group_name_parsing:
    enabled: true
    parser_type: CAS_dn
```

### 集成前准备

1. **在CAS服务器注册应用**
   - 提供Service URL（即CAS_SERVICE_URL的值）
   - 获取必要的访问权限

2. **确认CAS返回的属性**
   - 与CAS管理员确认返回的用户属性
   - 根据实际属性调整映射配置

3. **网络连通性**
   - 确保应用服务器能访问CAS服务器
   - 检查防火墙规则

4. **HTTPS配置**
   - 生产环境必须配置HTTPS
   - 确保SSL证书有效

### 集成步骤

1. **修改.env配置**
   系统已内置CAS配置，只需修改以下两个参数：
   ```env
   # 修改为公司的CAS服务器地址
   CAS_SERVER_URL=https://cas.company.com/cas
   
   # 修改为应用的实际访问地址
   CAS_SERVICE_URL=https://app.company.com/sso/callback
   ```
   
   其他配置保持默认即可：
   - `CAS_VERIFY_SSL=false`：开发环境默认不验证SSL
   - `CAS_VERSION=3`：使用CAS v3协议
   - `CAS_SESSION_TIMEOUT=36000`：10小时会话超时
   - 其他配置无需修改

2. **验证配置**
   ```bash
   # 获取CAS登录URL
   curl http://localhost:8000/api/v1/auth/cas/login
   ```

3. **测试登录流程**
   - 访问应用登录页面
   - 选择SSO登录
   - 跳转到CAS登录页面
   - 登录成功后自动回调到应用

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
3. 增强CAS功能支持
4. 权限细粒度控制
5. Redis令牌黑名单
6. 设备指纹识别
7. 异常登录检测