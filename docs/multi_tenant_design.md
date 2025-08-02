# 多租户管理设计方案

## 1. 租户模型设计

### 租户层级结构
```
租户(Tenant) -> 团队(Team) -> 用户(User) -> 资源(MCP服务器/配置)
```

### 数据隔离策略
- **数据库级隔离**: 通过tenant_id字段实现行级安全
- **应用级隔离**: 在API层面添加租户过滤
- **资源隔离**: MCP服务器、配置按租户分组

## 2. 数据库设计

### 新增租户管理表
```sql
-- 租户表
CREATE TABLE tenants (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id VARCHAR(100) UNIQUE NOT NULL,
    tenant_name VARCHAR(200) NOT NULL,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    max_servers INT DEFAULT 10,
    max_configs INT DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 租户用户关联表
CREATE TABLE tenant_users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    role ENUM('admin', 'member', 'viewer') DEFAULT 'member',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_tenant_user (tenant_id, user_id)
);
```

### 现有表添加租户字段
```sql
-- 为mcp_servers表添加租户字段
ALTER TABLE mcp_servers ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default';
ALTER TABLE mcp_servers ADD INDEX idx_tenant_id (tenant_id);

-- 确保mcp_configs表的tenant字段建立索引
ALTER TABLE mcp_configs ADD INDEX idx_tenant (tenant);
```

## 3. API设计

### 租户管理API
```
GET    /api/v1/tenants                 # 获取租户列表
POST   /api/v1/tenants                 # 创建租户
GET    /api/v1/tenants/{tenant_id}     # 获取租户详情
PUT    /api/v1/tenants/{tenant_id}     # 更新租户
DELETE /api/v1/tenants/{tenant_id}     # 删除租户

GET    /api/v1/tenants/{tenant_id}/users     # 获取租户用户
POST   /api/v1/tenants/{tenant_id}/users     # 添加租户用户
DELETE /api/v1/tenants/{tenant_id}/users/{user_id}  # 移除租户用户
```

### 资源API支持租户过滤
```
GET /api/v1/mcp/servers?tenant_id=xxx
GET /api/v1/mcp/configs?tenant=xxx
```

## 4. 中间件设计

### 租户识别中间件
- 从请求头获取租户信息
- 验证用户对租户的访问权限
- 自动注入租户过滤条件

### 权限控制中间件
- 租户级权限控制
- 资源配额限制
- 操作审计日志

## 5. 前端设计

### 租户选择器
- 顶部导航栏租户切换
- 支持多租户用户切换工作空间

### 管理界面
- 超级管理员: 租户管理界面
- 租户管理员: 租户内用户管理
- 普通用户: 资源管理界面

## 6. 实施步骤

### 第一阶段: 基础多租户
1. 创建租户管理表
2. 实现租户CRUD API
3. 添加租户中间件
4. 更新现有API支持租户过滤

### 第二阶段: 权限管理
1. 实现租户用户管理
2. 添加角色权限控制
3. 实现资源配额限制

## 7. 安全考虑

### 数据安全
- 租户数据完全隔离
- 防止租户间数据泄露
- 加密敏感配置信息

### 访问控制
- 基于JWT|CAS SSO的身份认证
- 细粒度权限控制
- API访问频率限制