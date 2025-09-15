"""
认证相关的工具函数
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
import jwt
# JWT错误处理
import pyotp
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
from src.shared.core.config import settings

SECRET_KEY = settings.JWT_SECRET_KEY or settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


class PasswordUtils:
    """密码相关工具"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def is_strong_password(password: str) -> tuple[bool, str]:
        """检查密码强度
        返回: (是否强密码, 错误信息)
        """
        # 使用配置中的密码策略
        if len(password) < settings.MIN_PASSWORD_LENGTH:
            return False, f"密码长度至少{settings.MIN_PASSWORD_LENGTH}位"
        
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if settings.REQUIRE_LOWERCASE and not has_lower:
            return False, "密码必须包含小写字母"
        if settings.REQUIRE_UPPERCASE and not has_upper:
            return False, "密码必须包含大写字母"
        if settings.REQUIRE_DIGITS and not has_digit:
            return False, "密码必须包含数字"
        if settings.REQUIRE_SPECIAL_CHARS and not has_special:
            return False, "密码必须包含特殊字符"
        
        return True, ""


class JWTUtils:
    """JWT相关工具"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        # 设置过期时间
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # 添加标准声明
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16),  # JWT ID，用于撤销
            "type": "access"
        })
        
        # 编码JWT
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        
        # 设置更长的过期时间
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # 添加标准声明
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> dict:
        """解码JWT令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.exceptions.PyJWTError as e:
            raise BusinessException(
                "无效的认证凭据",
                ResponseCode.UNAUTHORIZED
            )
    
    @staticmethod
    def get_jti(token: str) -> Optional[str]:
        """获取JWT的jti"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("jti")
        except:
            return None


class MFAUtils:
    """多因素认证工具"""
    
    @staticmethod
    def generate_secret() -> str:
        """生成MFA密钥"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_uri(secret: str, user_email: str, issuer: str = "智能运维平台") -> str:
        """生成MFA QR码URI"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=issuer)
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """验证TOTP令牌"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)


class APIKeyUtils:
    """API密钥工具"""
    
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """生成API密钥（Bearer Token格式）
        返回: (完整密钥, 明文密钥)
        
        注意：临时返回明文，后续稳定后再改为hash
        """
        # 生成Bearer Token格式的API Key
        # 格式：omind_ak_<random>
        key_id = f"omind_ak_{secrets.token_urlsafe(32)}"
        
        # 临时方案：直接返回明文作为"hash"
        return key_id, key_id
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """计算API密钥的哈希值
        
        临时方案：直接返回明文
        """
        return api_key
    
    @staticmethod
    def verify_api_key(api_key: str, stored_value: str) -> bool:
        """验证API密钥
        
        临时方案：直接比较明文
        """
        return api_key == stored_value


class TokenBlacklist:
    """令牌黑名单管理（应该使用Redis等缓存实现）"""
    
    # 简单的内存存储，生产环境应使用Redis
    _blacklist = set()
    
    @classmethod
    def add(cls, jti: str):
        """添加到黑名单"""
        cls._blacklist.add(jti)
    
    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        """检查是否在黑名单中"""
        return jti in cls._blacklist
    
    @classmethod
    def remove_expired(cls, expired_jtis: list[str]):
        """移除过期的JTI"""
        for jti in expired_jtis:
            cls._blacklist.discard(jti)


def generate_state_token() -> str:
    """生成OAuth2 state参数"""
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    """生成OpenID Connect nonce参数"""
    return secrets.token_urlsafe(32)


def mask_email(email: str) -> str:
    """隐藏邮箱地址"""
    if '@' not in email:
        return email
    
    local, domain = email.split('@')
    if len(local) <= 3:
        masked_local = local[0] + '*' * (len(local) - 1)
    else:
        masked_local = local[:2] + '*' * (len(local) - 4) + local[-2:]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """隐藏手机号"""
    if len(phone) < 7:
        return phone
    
    return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]


