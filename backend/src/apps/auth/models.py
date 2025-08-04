"""
认证相关的数据模型
支持JWT和SSO两种认证方式
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, BigInteger, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai, BaseModel
import secrets


class AuthUser(BaseModel):
    """扩展的用户认证模型 - 对应auth_users表
    用于存储认证相关的敏感信息，与rbac_users表关联
    """
    __tablename__ = "auth_users"
    __table_args__ = (
        Index('idx_auth_users_user_id', 'user_id'),
        Index('idx_auth_users_last_login', 'last_login'),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("rbac_users.user_id"), unique=True, nullable=False, comment="关联RBAC用户ID")
    password_hash = Column(String(255), nullable=True, comment="密码哈希（JWT认证使用）")
    mfa_secret = Column(String(255), nullable=True, comment="MFA密钥")
    mfa_enabled = Column(Boolean, default=False, nullable=False, comment="是否启用MFA")
    
    # 登录相关信息
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP")
    login_attempts = Column(Integer, default=0, nullable=False, comment="登录尝试次数")
    locked_until = Column(DateTime, nullable=True, comment="账户锁定到期时间")
    
    # SSO相关字段
    sso_provider = Column(String(50), nullable=True, comment="SSO提供商标识")
    sso_user_id = Column(String(255), nullable=True, comment="SSO用户ID")
    sso_attributes = Column(Text, nullable=True, comment="SSO属性（JSON格式）")
    
    # 其他安全相关
    password_changed_at = Column(DateTime, nullable=True, comment="密码最后修改时间")
    require_password_change = Column(Boolean, default=False, nullable=False, comment="是否需要修改密码")
    
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)


class AuthToken(BaseModel):
    """JWT令牌管理表 - 对应auth_tokens表
    用于管理JWT令牌的生命周期和黑名单
    """
    __tablename__ = "auth_tokens"
    __table_args__ = (
        Index('idx_auth_tokens_user_id', 'user_id'),
        Index('idx_auth_tokens_token_jti', 'token_jti'),
        Index('idx_auth_tokens_expires_at', 'expires_at'),
        Index('idx_auth_tokens_revoked', 'revoked'),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, comment="用户ID")
    token_jti = Column(String(255), unique=True, nullable=False, comment="JWT的jti标识")
    token_type = Column(String(20), nullable=False, comment="令牌类型：access/refresh")
    
    # 令牌元数据
    issued_at = Column(DateTime, default=now_shanghai, nullable=False, comment="签发时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    
    # 令牌状态
    revoked = Column(Boolean, default=False, nullable=False, comment="是否已撤销")
    revoked_at = Column(DateTime, nullable=True, comment="撤销时间")
    revoke_reason = Column(String(255), nullable=True, comment="撤销原因")
    
    # 设备和IP信息
    device_id = Column(String(255), nullable=True, comment="设备标识")
    device_name = Column(String(255), nullable=True, comment="设备名称")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="User-Agent")
    
    create_time = Column(DateTime, default=now_shanghai, nullable=False)


class AuthSession(BaseModel):
    """SSO会话管理表 - 对应auth_sessions表
    用于管理SSO登录会话
    """
    __tablename__ = "auth_sessions"
    __table_args__ = (
        Index('idx_auth_sessions_session_id', 'session_id'),
        Index('idx_auth_sessions_user_id', 'user_id'),
        Index('idx_auth_sessions_sso_provider', 'sso_provider'),
        Index('idx_auth_sessions_expires_at', 'expires_at'),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, comment="会话ID")
    user_id = Column(String(64), nullable=False, comment="用户ID")
    
    # SSO相关信息
    sso_provider = Column(String(50), nullable=False, comment="SSO提供商")
    sso_session_id = Column(String(255), nullable=True, comment="SSO提供商的会话ID")
    sso_access_token = Column(Text, nullable=True, comment="SSO访问令牌（加密存储）")
    sso_refresh_token = Column(Text, nullable=True, comment="SSO刷新令牌（加密存储）")
    sso_id_token = Column(Text, nullable=True, comment="SSO ID令牌")
    
    # 会话信息
    created_at = Column(DateTime, default=now_shanghai, nullable=False, comment="创建时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    last_accessed_at = Column(DateTime, default=now_shanghai, nullable=False, comment="最后访问时间")
    
    # 会话状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否活跃")
    terminated_at = Column(DateTime, nullable=True, comment="终止时间")
    termination_reason = Column(String(255), nullable=True, comment="终止原因")
    
    # 设备信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="User-Agent")
    
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    def generate_session_id(self):
        """生成安全的会话ID"""
        return secrets.token_urlsafe(32)


class AuthLoginHistory(BaseModel):
    """登录历史记录表 - 对应auth_login_history表
    记录所有登录尝试，用于安全审计
    """
    __tablename__ = "auth_login_history"
    __table_args__ = (
        Index('idx_auth_login_history_user_id', 'user_id'),
        Index('idx_auth_login_history_login_time', 'login_time'),
        Index('idx_auth_login_history_success', 'success'),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), nullable=True, comment="用户ID（失败时可能为空）")
    username = Column(String(100), nullable=True, comment="尝试登录的用户名")
    
    # 登录信息
    login_type = Column(String(20), nullable=False, comment="登录类型：jwt/sso")
    login_time = Column(DateTime, default=now_shanghai, nullable=False, comment="登录时间")
    success = Column(Boolean, nullable=False, comment="是否成功")
    
    # 失败原因
    failure_reason = Column(String(255), nullable=True, comment="失败原因")
    
    # 客户端信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="User-Agent")
    device_fingerprint = Column(String(255), nullable=True, comment="设备指纹")
    
    # SSO相关（如果是SSO登录）
    sso_provider = Column(String(50), nullable=True, comment="SSO提供商")
    
    create_time = Column(DateTime, default=now_shanghai, nullable=False)


class AuthApiKey(BaseModel):
    """API密钥表 - 对应auth_api_keys表
    用于服务间调用或第三方集成
    """
    __tablename__ = "auth_api_keys"
    __table_args__ = (
        Index('idx_auth_api_keys_key_hash', 'key_hash'),
        Index('idx_auth_api_keys_user_id', 'user_id'),
        Index('idx_auth_api_keys_expires_at', 'expires_at'),
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, comment="所属用户ID")
    
    # API密钥信息
    key_name = Column(String(100), nullable=False, comment="密钥名称")
    key_prefix = Column(String(20), nullable=False, comment="密钥前缀（用于识别）")
    key_hash = Column(String(255), unique=True, nullable=False, comment="密钥哈希")
    
    # 权限控制
    scopes = Column(Text, nullable=True, comment="权限范围（JSON数组）")
    allowed_ips = Column(Text, nullable=True, comment="允许的IP列表（JSON数组）")
    
    # 生命周期
    issued_at = Column(DateTime, default=now_shanghai, nullable=False, comment="签发时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间（null表示永不过期）")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    revoked_at = Column(DateTime, nullable=True, comment="撤销时间")
    revoke_reason = Column(String(255), nullable=True, comment="撤销原因")
    
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")


class AuthSSOProvider(BaseModel):
    """SSO提供商配置表 - 对应auth_sso_providers表
    管理多个SSO提供商的配置
    """
    __tablename__ = "auth_sso_providers"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    provider_id = Column(String(50), unique=True, nullable=False, comment="提供商标识")
    provider_name = Column(String(100), nullable=False, comment="提供商名称")
    provider_type = Column(String(50), nullable=False, comment="提供商类型：oauth2/saml/cas")
    
    # OAuth2配置
    client_id = Column(String(255), nullable=True, comment="OAuth2 Client ID")
    client_secret = Column(Text, nullable=True, comment="OAuth2 Client Secret（加密存储）")
    authorization_url = Column(String(500), nullable=True, comment="授权URL")
    token_url = Column(String(500), nullable=True, comment="Token URL")
    userinfo_url = Column(String(500), nullable=True, comment="用户信息URL")
    
    # SAML配置
    saml_metadata_url = Column(String(500), nullable=True, comment="SAML元数据URL")
    saml_entity_id = Column(String(255), nullable=True, comment="SAML实体ID")
    
    # 通用配置
    redirect_uri = Column(String(500), nullable=True, comment="回调URI")
    scopes = Column(String(500), nullable=True, comment="请求的权限范围")
    
    # 用户映射配置
    user_id_attribute = Column(String(100), nullable=True, comment="用户ID属性名")
    username_attribute = Column(String(100), nullable=True, comment="用户名属性名")
    email_attribute = Column(String(100), nullable=True, comment="邮箱属性名")
    display_name_attribute = Column(String(100), nullable=True, comment="显示名称属性名")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    priority = Column(Integer, default=0, nullable=False, comment="优先级")
    
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")