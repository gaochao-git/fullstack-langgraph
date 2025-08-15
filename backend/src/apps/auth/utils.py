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
    def generate_api_key() -> tuple[str, str, str]:
        """生成API密钥（Bearer Token格式）
        返回: (完整密钥, 密钥前缀, 密钥哈希)
        """
        # 生成Bearer Token格式的API Key
        # 格式：omind_ak_<random>
        key_id = f"omind_ak_{secrets.token_urlsafe(32)}"
        
        # 计算哈希（用于存储）
        key_hash = hashlib.sha256(key_id.encode()).hexdigest()
        
        # 前缀用于显示（只显示前16个字符）
        prefix = key_id[:16]
        
        return key_id, prefix, key_hash
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """计算API密钥的哈希值"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, stored_hash: str) -> bool:
        """验证API密钥"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return key_hash == stored_hash


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


def parse_cas_attributes(attributes: Dict[str, Any]) -> Dict[str, Any]:
    """
    简单的CAS属性解析函数
    
    Args:
        attributes: CAS返回的原始属性字典
        
    Returns:
        解析后的属性字典
    """
    parsed = {}
    
    # 直接映射的属性
    direct_mappings = {
        'display_name': 'display_name',
        'email': 'email',
        'username': 'username',
        'mobile': 'mobile',
        'department': 'department'
    }
    
    for cas_attr, local_attr in direct_mappings.items():
        if cas_attr in attributes:
            parsed[local_attr] = attributes[cas_attr]
    
    # 解析group_name属性（可能包含LDAP格式的DN）
    if 'group_name' in attributes:
        group_name = attributes['group_name']
        parsed['group_name'] = group_name
        
        # 尝试从LDAP DN中提取部门信息
        if 'department' not in parsed and group_name:
            # 例如: CN=张三,OU=开发组,OU=技术部,OU=淘宝,DC=taobao,DC=COM
            parts = [p.strip() for p in group_name.split(',')]
            for part in parts:
                if part.startswith('OU='):
                    # 获取第一个OU作为部门
                    parsed['department'] = part[3:]
                    break
    
    # 处理其他可能的属性格式
    if 'cn' in attributes and 'display_name' not in parsed:
        parsed['display_name'] = attributes['cn']
        
    if 'mail' in attributes and 'email' not in parsed:
        parsed['email'] = attributes['mail']
        
    if 'uid' in attributes and 'username' not in parsed:
        parsed['username'] = attributes['uid']
    
    return parsed


class CASAttributeParser:
    """
    CAS属性解析器，使用YAML配置文件进行属性映射
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化CAS属性解析器
        
        Args:
            config_path: YAML配置文件路径，默认使用 cas_mapping_config.yaml
        """
        if config_path is None:
            # 使用默认配置文件路径
            import os
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'shared', 'core', 'cas_mapping_config.yaml'
            )
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            # 如果配置文件加载失败，使用默认配置
            return {
                'attribute_mapping': {
                    'display_name': 'display_name',
                    'email': 'email',
                    'group_name': 'group_name',
                    'username': 'user_name',
                    'mobile': 'mobile'
                }
            }
    
    def parse_attributes(self, cas_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据配置文件解析CAS属性
        
        Args:
            cas_attributes: CAS返回的原始属性
            
        Returns:
            解析后的属性字典
        """
        parsed = {}
        
        # 获取属性映射配置
        mapping = self.config.get('attribute_mapping', {})
        
        # 进行属性映射
        for cas_attr, db_field in mapping.items():
            if cas_attr in cas_attributes:
                value = cas_attributes[cas_attr]
                
                # 特殊处理group_name
                if cas_attr == 'group_name' and value:
                    # 解析LDAP DN格式
                    parsed['group_name'] = value
                    parsed['department_name'] = self._parse_department_from_dn(value)
                elif db_field:
                    parsed[db_field] = value
        
        # 设置默认值
        defaults = self.config.get('defaults', {})
        for field, default_value in defaults.items():
            if field not in parsed:
                parsed[field] = default_value
        
        # 确保必要字段存在
        if 'user_id' not in parsed and 'user_name' in parsed:
            parsed['user_id'] = f"cas_{parsed['user_name']}"
        
        return parsed
    
    def _parse_department_from_dn(self, dn: str) -> str:
        """
        从LDAP DN中解析部门信息
        
        Args:
            dn: LDAP DN字符串
            
        Returns:
            部门名称
        """
        if not dn:
            return '未分配部门'
        
        # 解析DN格式，例如: CN=张三,OU=开发组,OU=技术部,OU=淘宝,DC=taobao,DC=COM
        parts = [p.strip() for p in dn.split(',')]
        departments = []
        
        for part in parts:
            if part.startswith('OU='):
                departments.append(part[3:])
        
        if departments:
            # 返回最后一个OU作为主要部门
            return departments[-1] if departments else '未分配部门'
        
        return '未分配部门'