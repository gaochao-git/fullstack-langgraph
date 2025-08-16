"""
RBAC Schema定义 - 根据实际数据库表结构
用于API请求和响应的数据验证
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


# ============ 基础Schema ============

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=1000, description="每页大小")
    search: Optional[str] = Field(None, description="搜索关键词", max_length=200)


class ApiResponse(BaseModel):
    """通用API响应模式"""
    success: bool = True
    message: Optional[str] = "操作成功"
    data: Optional[object] = None
    error: Optional[str] = None


class PaginationResponse(BaseModel):
    """分页响应"""
    data: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ 用户相关Schema ============

class UserCreateRequest(BaseModel):
    """创建用户请求 - 对应rbac_users表"""
    user_id: str = Field(..., max_length=64, description="用户ID")
    user_name: str = Field(..., min_length=1, max_length=50, description="用户名")
    display_name: str = Field(..., min_length=1, max_length=50, description="显示名称")
    department_name: str = Field(..., min_length=1, max_length=50, description="部门名称")
    group_name: str = Field(..., min_length=1, max_length=50, description="组名")
    email: EmailStr = Field(..., description="邮箱")
    mobile: Optional[str] = Field("", max_length=20, description="手机号")
    user_source: int = Field(2, description="用户来源：1=SSO,2=Local")
    is_active: int = Field(1, description="是否激活: 1激活 0禁用")
    role_ids: Optional[List[int]] = Field([], description="角色ID列表")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    user_name: Optional[str] = Field(None, min_length=1, max_length=50, description="用户名")
    display_name: Optional[str] = Field(None, min_length=1, max_length=50, description="显示名称")
    department_name: Optional[str] = Field(None, min_length=1, max_length=50, description="部门名称")
    group_name: Optional[str] = Field(None, min_length=1, max_length=50, description="组名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    mobile: Optional[str] = Field(None, max_length=20, description="手机号")
    user_source: Optional[int] = Field(None, description="用户来源：1=sso,2=local")
    is_active: Optional[int] = Field(None, description="是否激活: 1激活 0禁用")
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    user_id: str
    user_name: str
    display_name: str
    department_name: str
    group_name: str
    email: str
    mobile: str
    user_source: int
    is_active: int
    create_time: str
    update_time: str
    create_by: str
    update_by: str
    roles: List[dict] = []

    class Config:
        from_attributes = True


class UserQueryParams(PaginationParams):
    """用户查询参数"""
    is_active: Optional[int] = Field(None, description="激活状态筛选: 1激活 0禁用")
    department_name: Optional[str] = Field(None, description="部门筛选")
    group_name: Optional[str] = Field(None, description="组筛选")
    user_source: Optional[int] = Field(None, description="用户来源筛选：1=sso,2=local")


class UserListResponse(BaseModel):
    """用户列表响应"""
    data: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ 角色相关Schema ============

class RoleCreateRequest(BaseModel):
    """创建角色请求 - 对应rbac_roles表"""
    role_id: Optional[int] = Field(None, description="角色ID，不填则自动生成")
    role_name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    description: str = Field(..., min_length=1, max_length=200, description="角色描述")
    permission_ids: Optional[List[int]] = Field([], description="后端API权限ID列表")
    menu_ids: Optional[List[int]] = Field([], description="前端菜单权限ID列表")


class RoleUpdateRequest(BaseModel):
    """更新角色请求"""
    role_name: Optional[str] = Field(None, min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, min_length=1, max_length=200, description="角色描述")
    permission_ids: Optional[List[int]] = Field(None, description="后端API权限ID列表")
    menu_ids: Optional[List[int]] = Field(None, description="前端菜单权限ID列表")


class RoleResponse(BaseModel):
    """角色响应"""
    id: int
    role_id: int
    role_name: str
    description: str
    create_time: str
    update_time: str
    create_by: str
    update_by: str
    permission_count: int = 0
    user_count: int = 0

    class Config:
        from_attributes = True


class RoleQueryParams(PaginationParams):
    """角色查询参数"""
    role_id: Optional[int] = Field(None, description="角色ID筛选")


class RoleListResponse(BaseModel):
    """角色列表响应"""
    data: List[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ 权限相关Schema ============

class PermissionCreateRequest(BaseModel):
    """创建权限请求 - 对应rbac_permissions表"""
    permission_id: int = Field(..., description="权限ID")
    permission_description: str = Field(..., min_length=1, max_length=200, description="权限描述")
    permission_name: str = Field(..., min_length=1, max_length=100, description="权限名称(API路径)")
    http_method: str = Field("*", max_length=10, description="HTTP方法: GET,POST,PUT,DELETE,*")
    release_disable: str = Field("off", max_length=10, description="发布禁用")
    permission_allow_client: Optional[str] = Field(None, description="允许的客户端")


class PermissionUpdateRequest(BaseModel):
    """更新权限请求"""
    permission_description: Optional[str] = Field(None, min_length=1, max_length=200, description="权限描述")
    permission_name: Optional[str] = Field(None, min_length=1, max_length=100, description="权限名称(API路径)")
    http_method: Optional[str] = Field(None, max_length=10, description="HTTP方法: GET,POST,PUT,DELETE,*")
    release_disable: Optional[str] = Field(None, max_length=10, description="发布禁用")
    permission_allow_client: Optional[str] = Field(None, description="允许的客户端")


class PermissionResponse(BaseModel):
    """权限响应"""
    id: int
    permission_id: int
    permission_description: str
    permission_name: str
    http_method: str
    release_disable: str
    permission_allow_client: Optional[str]
    create_time: str
    update_time: str
    create_by: str
    update_by: str

    class Config:
        from_attributes = True


class PermissionQueryParams(PaginationParams):
    """权限查询参数"""
    permission_id: Optional[int] = Field(None, description="权限ID筛选")
    release_disable: Optional[str] = Field(None, description="发布状态筛选")
    http_method: Optional[str] = Field(None, description="HTTP方法筛选")


class PermissionListResponse(BaseModel):
    """权限列表响应"""
    data: List[PermissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ 菜单相关Schema ============

class MenuCreateRequest(BaseModel):
    """创建菜单请求 - 对应rbac_menus表"""
    menu_id: int = Field(..., description="菜单ID")
    menu_name: str = Field(..., min_length=1, max_length=50, description="菜单名称")
    menu_icon: str = Field(..., max_length=50, description="菜单图标")
    parent_id: int = Field(-1, description="父菜单ID")
    route_path: str = Field(..., max_length=200, description="路由路径")
    redirect_path: str = Field(..., max_length=200, description="重定向路径")
    menu_component: str = Field(..., max_length=100, description="组件名称")
    show_menu: int = Field(0, description="是否显示菜单: 1显示 0隐藏")


class MenuUpdateRequest(BaseModel):
    """更新菜单请求"""
    menu_name: Optional[str] = Field(None, min_length=1, max_length=50, description="菜单名称")
    menu_icon: Optional[str] = Field(None, max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    route_path: Optional[str] = Field(None, max_length=200, description="路由路径")
    redirect_path: Optional[str] = Field(None, max_length=200, description="重定向路径")
    menu_component: Optional[str] = Field(None, max_length=100, description="组件名称")
    show_menu: Optional[int] = Field(None, description="是否显示菜单: 1显示 0隐藏")


class MenuResponse(BaseModel):
    """菜单响应"""
    id: int
    menu_id: int
    menu_name: str
    menu_icon: str
    parent_id: int
    route_path: str
    redirect_path: str
    menu_component: str
    show_menu: int
    create_time: str
    update_time: str
    create_by: str
    update_by: str

    class Config:
        from_attributes = True


class MenuQueryParams(PaginationParams):
    """菜单查询参数"""
    parent_id: Optional[int] = Field(None, description="父菜单筛选")
    show_menu: Optional[int] = Field(None, description="显示状态筛选: 1显示 0隐藏")
    menu_id: Optional[int] = Field(None, description="菜单ID筛选")


class MenuListResponse(BaseModel):
    """菜单列表响应"""
    data: List[MenuResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ 用户角色关联Schema ============

class UserRoleCreateRequest(BaseModel):
    """用户角色关联请求"""
    user_id: str = Field(..., max_length=64, description="用户ID")
    role_id: int = Field(..., description="角色ID")


class UserRoleResponse(BaseModel):
    """用户角色关联响应"""
    id: int
    user_id: str
    role_id: int
    create_time: str
    update_time: str
    create_by: str
    update_by: str

    class Config:
        from_attributes = True


# ============ 角色权限关联Schema ============

class RolePermissionCreateRequest(BaseModel):
    """角色权限关联请求"""
    role_id: int = Field(..., description="角色ID")
    back_permission_id: int = Field(-1, description="后端权限ID")
    front_permission_id: int = Field(-1, description="前端权限ID")
    permission_type: int = Field(-1, description="权限类型")


class RolePermissionResponse(BaseModel):
    """角色权限关联响应"""
    id: int
    role_id: int
    back_permission_id: int
    front_permission_id: int
    permission_type: int
    create_time: str
    update_time: str
    create_by: str
    update_by: str

    class Config:
        from_attributes = True