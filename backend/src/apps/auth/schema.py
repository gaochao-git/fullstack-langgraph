"""
认证模块数据模式定义
包含登录、SSO、用户、会话、API Key和菜单相关的所有Schema
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


# ============= 登录相关 =============

class LoginRequest(BaseModel):
    """JWT登录请求"""
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    mfa_code: Optional[str] = Field(None, description="MFA验证码")
    device_id: Optional[str] = Field(None, description="设备ID")
    device_name: Optional[str] = Field(None, description="设备名称")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: Dict[str, Any] = Field(..., description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class LogoutRequest(BaseModel):
    """登出请求"""
    everywhere: bool = Field(default=False, description="是否登出所有设备")


# ============= 用户相关 =============

class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    phone: Optional[str] = None
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v


class RegisterResponse(BaseModel):
    """注册响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应信息")
    user: Optional[Dict[str, Any]] = Field(None, description="用户信息")


class UserProfile(BaseModel):
    """用户资料"""
    id: str
    user_id: str
    username: str
    display_name: str
    email: str
    mobile: Optional[str] = None
    department_name: Optional[str] = None
    group_name: Optional[str] = None
    roles: List[Dict[str, Any]] = []
    permissions: List[str] = []
    last_login: Optional[datetime] = None
    mfa_enabled: bool = False


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr = Field(..., description="注册邮箱")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, description="新密码")
    confirm_password: str = Field(..., min_length=6, description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('密码不匹配')
        return v


class UserProfileUpdate(BaseModel):
    """用户资料更新"""
    nickname: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    """用户信息响应"""
    user_id: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None


# ============= MFA相关 =============

class EnableMFARequest(BaseModel):
    """启用MFA请求"""
    password: str = Field(..., description="当前密码")


class EnableMFAResponse(BaseModel):
    """启用MFA响应"""
    secret: str = Field(..., description="MFA密钥")
    qr_uri: str = Field(..., description="QR码URI")
    backup_codes: List[str] = Field(..., description="备份码")


class VerifyMFARequest(BaseModel):
    """验证MFA请求"""
    code: str = Field(..., pattern=r'^\d{6}$', description="6位数字验证码")


class DisableMFARequest(BaseModel):
    """禁用MFA请求"""
    password: str = Field(..., description="当前密码")
    code: str = Field(..., pattern=r'^\d{6}$', description="MFA验证码")


# ============= 会话相关 =============

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    last_accessed_at: Optional[datetime] = None
    is_current: bool = False


class TerminateSessionRequest(BaseModel):
    """终止会话请求"""
    session_id: str = Field(..., description="会话ID")


# ============= API Key相关 =============

class CreateAPIKeyRequest(BaseModel):
    """创建API Key请求"""
    user_id: str = Field(..., description="用户ID")
    key_name: str = Field(..., min_length=1, max_length=100, description="API Key名称")
    mark_comment: str = Field(..., min_length=1, max_length=64, description="工单号")
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650, description="过期天数")
    scopes: Optional[List[int]] = Field(default_factory=list, description="权限ID列表")
    allowed_ips: Optional[List[str]] = Field(default_factory=list, description="允许的IP列表")


class APIKeyInfo(BaseModel):
    """API Key信息"""
    key_id: str
    user_id: str
    user_name: Optional[str] = None
    key_name: str
    key_prefix: str
    mark_comment: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    is_active: bool
    scopes: Optional[List[int]] = []
    allowed_ips: Optional[List[str]] = []
    create_by: Optional[str] = None
    update_by: Optional[str] = None


class CreateAPIKeyResponse(BaseModel):
    """创建API Key响应"""
    api_key: str  # 完整的key，只在创建时返回一次
    key_info: APIKeyInfo


# ============= 菜单相关 =============

class MenuCreateRequest(BaseModel):
    """创建菜单请求"""
    menu_name: str = Field(..., min_length=1, max_length=50, description="菜单名称")
    menu_icon: Optional[str] = Field("default", max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(-1, description="父菜单ID，-1表示根菜单")
    route_path: str = Field(..., min_length=1, max_length=200, description="路由路径")
    redirect_path: Optional[str] = Field("", max_length=200, description="重定向路径")
    menu_component: str = Field(..., min_length=1, max_length=100, description="组件名称")
    show_menu: Optional[int] = Field(1, description="是否显示菜单：1-显示，0-隐藏")
    sort_order: Optional[int] = Field(0, description="排序顺序：数字越小越靠前")


class MenuUpdateRequest(BaseModel):
    """更新菜单请求"""
    menu_name: Optional[str] = Field(None, min_length=1, max_length=50, description="菜单名称")
    menu_icon: Optional[str] = Field(None, max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    route_path: Optional[str] = Field(None, min_length=1, max_length=200, description="路由路径")
    redirect_path: Optional[str] = Field(None, max_length=200, description="重定向路径")
    menu_component: Optional[str] = Field(None, min_length=1, max_length=100, description="组件名称")
    show_menu: Optional[int] = Field(None, description="是否显示菜单：1-显示，0-隐藏")
    sort_order: Optional[int] = Field(None, description="排序顺序：数字越小越靠前")


class MenuResponse(BaseModel):
    """菜单响应"""
    id: int = Field(..., description="数据库主键ID")
    menu_id: int = Field(..., description="菜单ID")
    menu_name: str = Field(..., description="菜单名称")
    menu_icon: str = Field(..., description="菜单图标")
    parent_id: int = Field(..., description="父菜单ID")
    route_path: str = Field(..., description="路由路径")
    redirect_path: str = Field(..., description="重定向路径")
    menu_component: str = Field(..., description="组件名称")
    show_menu: int = Field(..., description="是否显示菜单")
    sort_order: int = Field(..., description="排序顺序")
    create_time: Optional[str] = Field(None, description="创建时间")
    update_time: Optional[str] = Field(None, description="更新时间")


class MenuTreeResponse(MenuResponse):
    """菜单树响应"""
    children: List['MenuTreeResponse'] = Field(default_factory=list, description="子菜单")


class MenuListResponse(BaseModel):
    """菜单列表响应"""
    menus: List[MenuTreeResponse] = Field(..., description="菜单树")
    total: int = Field(..., description="菜单总数")


class UserMenuResponse(BaseModel):
    """用户菜单响应"""
    menus: List[MenuTreeResponse] = Field(..., description="用户可访问的菜单树")


class MenuParentOption(BaseModel):
    """父菜单选项"""
    label: str = Field(..., description="显示标签")
    value: int = Field(..., description="菜单ID")
    children: Optional[List['MenuParentOption']] = Field(default_factory=list, description="子选项")


class MenuParentOptionsResponse(BaseModel):
    """父菜单选项响应"""
    options: List[MenuParentOption] = Field(..., description="父菜单选项列表")


# ============= 权限验证相关 =============

class TokenValidationResponse(BaseModel):
    """令牌验证响应"""
    valid: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    scopes: List[str] = []
    expires_at: Optional[datetime] = None


class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    resource: str = Field(..., description="资源标识")
    action: str = Field(..., description="操作类型")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


# 解决前向引用问题
MenuTreeResponse.model_rebuild()
MenuParentOption.model_rebuild()