"""
认证相关的数据模式定义
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


# ============= SSO相关 =============

class SSOProviderInfo(BaseModel):
    """SSO提供商信息"""
    provider_id: str
    provider_name: str
    provider_type: str
    login_url: Optional[str] = None


class SSOLoginUrlResponse(BaseModel):
    """SSO登录URL响应"""
    url: str = Field(..., description="SSO登录URL")
    state: str = Field(..., description="State参数")
    provider: str = Field(..., description="提供商标识")


class SSOCallbackRequest(BaseModel):
    """SSO回调请求"""
    code: str = Field(..., description="授权码")
    state: Optional[str] = Field(None, description="State参数")
    provider: Optional[str] = Field(None, description="提供商标识")


# ============= 注册相关 =============

class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    password: str = Field(..., min_length=1, description="密码")  # 最小长度由validator检查
    email: EmailStr = Field(..., description="邮箱地址")
    display_name: str = Field(..., min_length=1, max_length=50, description="显示名称")
    
    @validator('username')
    def validate_username(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        # 使用 PasswordUtils 进行密码强度检查
        from .utils import PasswordUtils
        is_strong, error_msg = PasswordUtils.is_strong_password(v)
        if not is_strong:
            raise ValueError(error_msg)
        return v


class RegisterResponse(BaseModel):
    """注册响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应信息")
    user: Optional[Dict[str, Any]] = Field(None, description="用户信息")


# ============= 用户相关 =============

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
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        # 这里可以调用PasswordUtils.is_strong_password
        return v


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, description="新密码")


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr = Field(..., description="邮箱地址")


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


# ============= API密钥相关 =============

class CreateAPIKeyRequest(BaseModel):
    """创建API密钥请求"""
    key_name: str = Field(..., min_length=1, max_length=100, description="密钥名称")
    scopes: List[str] = Field(default=[], description="权限范围")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="过期天数")
    allowed_ips: Optional[List[str]] = Field(None, description="允许的IP列表")


class CreateAPIKeyResponse(BaseModel):
    """创建API密钥响应"""
    api_key: str = Field(..., description="API密钥（仅此次显示）")
    key_prefix: str = Field(..., description="密钥前缀")
    key_name: str = Field(..., description="密钥名称")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class APIKeyInfo(BaseModel):
    """API密钥信息"""
    id: int
    key_name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime


# ============= 会话管理相关 =============

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    device_name: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    last_accessed_at: datetime
    created_at: datetime
    is_current: bool = False


class TerminateSessionRequest(BaseModel):
    """终止会话请求"""
    session_id: str = Field(..., description="会话ID")


# ============= 安全相关 =============

class LoginAttempt(BaseModel):
    """登录尝试记录"""
    username: Optional[str]
    login_type: str
    success: bool
    failure_reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    login_time: datetime


class SecurityEventLog(BaseModel):
    """安全事件日志"""
    event_type: str
    event_description: str
    user_id: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]


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