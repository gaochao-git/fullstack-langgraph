# RBAC与认证系统集成文档

## 概述

本文档说明如何将RBAC（基于角色的访问控制）系统与认证模块集成，实现细粒度的权限控制。

## 集成架构

```
用户 -> 认证(JWT/SSO) -> 获取角色 -> 获取权限 -> 访问资源
```

## 核心组件

### 1. RBACService - 权限服务
位置：`src/apps/auth/rbac_service.py`

主要功能：
- 获取用户角色
- 获取用户权限
- 检查特定权限
- 构建菜单树
- 权限缓存管理

### 2. 认证中间件
位置：`src/apps/auth/middleware.py`

包含三个中间件：
- **AuthMiddleware** - JWT令牌验证
- **RBACMiddleware** - 自动权限检查
- **AuditMiddleware** - 访问日志记录

### 3. 权限依赖项
位置：`src/apps/auth/dependencies.py`

提供多种权限检查方式：
- `require_roles()` - 角色检查
- `require_permissions()` - 权限检查
- `PermissionChecker` - 权限检查类
- `RoleChecker` - 角色检查类

## 使用方式

### 1. 基本权限保护

```python
from fastapi import APIRouter, Depends
from src.apps.auth import CurrentUser, get_current_user

router = APIRouter()

# 只需要登录
@router.get("/profile")
async def get_profile(current_user: CurrentUser):
    return {"user": current_user}
```

### 2. 角色保护

```python
from src.apps.auth import require_roles

# 需要admin或super_admin角色
@router.post("/users", dependencies=[Depends(require_roles("admin", "super_admin"))])
async def create_user(user_data: dict):
    return {"message": "User created"}

# 使用预定义的角色检查器
from src.apps.auth import is_admin

@router.delete("/users/{user_id}", dependencies=[Depends(is_admin)])
async def delete_user(user_id: int):
    return {"message": "User deleted"}
```

### 3. 权限保护

```python
from src.apps.auth import require_permissions

# 需要特定权限
@router.get("/reports", dependencies=[Depends(require_permissions("report:read"))])
async def get_reports():
    return {"reports": []}

# 使用权限检查类
from src.apps.auth.dependencies import PermissionChecker

check_user_write = PermissionChecker("/api/v1/users", check_method=True)

@router.post("/users", dependencies=[Depends(check_user_write)])
async def create_user_with_permission(user_data: dict):
    return {"message": "User created"}
```

### 4. 获取用户权限信息

```python
# 在路由中获取用户的完整权限信息
@router.get("/my-permissions")
async def get_my_permissions(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    from src.apps.auth.rbac_service import RBACService
    
    service = RBACService(db)
    permissions = service.get_permission_tree(current_user["sub"])
    
    return permissions
```

### 5. 全局中间件配置

在FastAPI应用中启用认证和权限中间件：

```python
from fastapi import FastAPI
from src.apps.auth.middleware import setup_auth_middleware

app = FastAPI()

# 自动配置所有中间件
setup_auth_middleware(app)

# 或手动配置
from src.apps.auth.middleware import AuthMiddleware, RBACMiddleware

app.add_middleware(RBACMiddleware, check_permissions=True)
app.add_middleware(AuthMiddleware, exclude_paths=["/health", "/docs"])
```

## 权限数据结构

### 权限格式
权限使用路径匹配模式：
- `/api/v1/users` - 精确匹配
- `/api/v1/users/*` - 匹配单级
- `/api/v1/users/**` - 匹配多级

### HTTP方法
- `GET` - 读取权限
- `POST` - 创建权限
- `PUT` - 更新权限
- `DELETE` - 删除权限
- `*` - 所有方法

## API端点

### 认证相关
- `GET /api/v1/auth/me` - 获取当前用户信息
- `GET /api/v1/auth/me/permissions` - 获取权限树
- `GET /api/v1/auth/me/menus` - 获取菜单树

### 权限检查
- `POST /api/v1/auth/permissions/check` - 检查特定权限

## 前端集成

前端可以通过以下方式使用权限信息：

```javascript
// 获取用户权限
const response = await fetch('/api/v1/auth/me/permissions', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const permissions = await response.json();

// 权限数据结构
{
  "roles": [
    {
      "id": 1,
      "name": "admin",
      "description": "管理员"
    }
  ],
  "permissions": {
    "/api/v1/users": {
      "id": 1,
      "name": "/api/v1/users",
      "description": "用户管理",
      "method": "*",
      "enabled": true
    }
  },
  "menus": [
    {
      "id": 1,
      "name": "系统管理",
      "icon": "setting",
      "path": "/system",
      "children": [...]
    }
  ]
}
```

## 初始化数据

### 1. 创建默认角色

```python
from src.apps.auth.rbac_service import RBACService

service = RBACService(db)
service.create_default_roles()  # 创建super_admin, admin, user角色
```

### 2. 分配角色给用户

```python
# 给管理员分配super_admin角色
service.assign_role_to_user(
    user_id="admin",
    role_id=1,  # super_admin
    created_by="system"
)
```

### 3. 创建权限并分配给角色

```sql
-- 创建权限
INSERT INTO rbac_permissions (
    permission_id, 
    permission_name, 
    permission_description,
    http_method,
    create_by,
    update_by
) VALUES 
(1, '/api/v1/users', '用户管理', '*', 'system', 'system'),
(2, '/api/v1/roles', '角色管理', '*', 'system', 'system');

-- 分配权限给角色
INSERT INTO rbac_roles_permissions (
    role_id,
    back_permission_id,
    permission_type,
    create_by,
    update_by
) VALUES
(1, 1, 1, 'system', 'system'),  -- super_admin拥有用户管理权限
(1, 2, 1, 'system', 'system');  -- super_admin拥有角色管理权限
```

## 最佳实践

1. **权限粒度**：根据实际需求设置合适的权限粒度，避免过细或过粗
2. **缓存策略**：使用Redis缓存用户权限，提高性能
3. **权限继承**：通过角色实现权限继承，避免直接给用户分配权限
4. **审计日志**：记录所有权限相关的操作
5. **定期审查**：定期审查用户权限，移除不必要的权限

## 注意事项

1. JWT令牌中不要包含过多权限信息，避免令牌过大
2. 敏感操作应该实时检查权限，不要只依赖令牌中的权限
3. 使用HTTPS保护认证信息
4. 实现权限变更后的即时生效机制