"""
CAS (Central Authentication Service) 集成服务
"""

import secrets
import httpx
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from urllib.parse import urlencode, quote
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.logging import get_logger
from src.shared.core.config import settings
from src.apps.auth.models import AuthUser
from src.apps.user.models import RbacUser
from src.apps.auth.utils import JWTUtils
from src.apps.auth.utils import CASAttributeParser
from src.apps.auth.schema import LoginResponse
from src.shared.db.models import now_shanghai

logger = get_logger(__name__)


class CASService:
    """CAS单点登录服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # CAS服务器配置
        self.cas_server_url = settings.CAS_SERVER_URL
        self.service_url = settings.CAS_SERVICE_URL
        self.cas_version = settings.CAS_VERSION
        self.verify_ssl = settings.CAS_VERIFY_SSL
        self.apply_attributes = settings.CAS_APPLY_ATTRIBUTES
        self.session_timeout = settings.CAS_SESSION_TIMEOUT
        self.check_next = settings.CAS_CHECK_NEXT
        self.single_logout_enabled = settings.CAS_SINGLE_LOGOUT_ENABLED
        
        # 初始化CAS属性解析器（使用YAML配置）
        self.attribute_parser = CASAttributeParser()
        
    def get_login_url(self) -> str:
        """获取CAS登录URL"""
        params = {
            'service': self.service_url
        }
        return f"{self.cas_server_url}/login?{urlencode(params)}"
    
    def get_logout_url(self, redirect_url: Optional[str] = None) -> str:
        """获取CAS登出URL"""
        if redirect_url:
            params = {
                'service': redirect_url
            }
            return f"{self.cas_server_url}/logout?{urlencode(params)}"
        return f"{self.cas_server_url}/logout"
    
    async def validate_ticket(self, ticket: str) -> Dict[str, Any]:
        """
        验证CAS票据
        
        Args:
            ticket: CAS票据
            
        Returns:
            包含用户信息的字典
        """
        # 构建验证URL
        if self.cas_version == '3':
            validate_url = f"{self.cas_server_url}/p3/serviceValidate"
        else:
            validate_url = f"{self.cas_server_url}/serviceValidate"
            
        params = {
            'service': self.service_url,
            'ticket': ticket
        }
        
        try:
            # 请求CAS服务器验证票据
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.get(
                    validate_url,
                    params=params,
                    timeout=10.0
                )
                
            if response.status_code != 200:
                logger.error(f"CAS ticket validation failed: {response.status_code}")
                raise BusinessException(
                    "CAS票据验证失败",
                    ResponseCode.UNAUTHORIZED
                )
                
            # 解析XML响应
            root = ET.fromstring(response.text)
            
            # CAS命名空间
            ns = {'cas': 'http://www.yale.edu/tp/cas'}
            
            # 检查认证是否成功
            auth_success = root.find('.//cas:authenticationSuccess', ns)
            if auth_success is None:
                auth_failure = root.find('.//cas:authenticationFailure', ns)
                if auth_failure is not None:
                    error_code = auth_failure.get('code', 'UNKNOWN')
                    error_msg = auth_failure.text.strip() if auth_failure.text else 'Unknown error'
                    logger.error(f"CAS authentication failed: {error_code} - {error_msg}")
                raise BusinessException(
                    "CAS认证失败",
                    ResponseCode.UNAUTHORIZED
                )
                
            # 提取用户名
            user_element = auth_success.find('cas:user', ns)
            if user_element is None:
                raise BusinessException(
                    "CAS响应中缺少用户信息",
                    ResponseCode.INTERNAL_ERROR
                )
                
            username = user_element.text.strip()
            
            # 提取属性
            attributes = {}
            attrs_element = auth_success.find('cas:attributes', ns)
            if attrs_element is not None:
                for attr in attrs_element:
                    attr_name = attr.tag.replace('{http://www.yale.edu/tp/cas}', '')
                    attributes[attr_name] = attr.text
                    
            logger.info(f"CAS validation successful for user: {username}")
            
            return {
                'username': username,
                'attributes': attributes
            }
            
        except httpx.RequestError as e:
            logger.error(f"CAS request error: {e}")
            raise BusinessException(
                "无法连接到CAS服务器",
                ResponseCode.INTERNAL_ERROR
            )
        except ET.ParseError as e:
            logger.error(f"CAS response parse error: {e}")
            raise BusinessException(
                "CAS响应格式错误",
                ResponseCode.INTERNAL_ERROR
            )
            
    async def process_cas_login(self, ticket: str) -> LoginResponse:
        """
        处理CAS登录
        
        Args:
            ticket: CAS票据
            
        Returns:
            登录响应
        """
        # 验证票据
        cas_data = await self.validate_ticket(ticket)
        username = cas_data['username']
        attributes = cas_data.get('attributes', {})
        
        # 解析CAS属性（使用YAML配置）
        parsed_attrs = self.attribute_parser.parse_attributes(attributes)
        
        # 查找或创建用户
        result = await self.db.execute(
            select(RbacUser).where(
                or_(
                    RbacUser.user_name == username,
                    RbacUser.email == parsed_attrs.get('email')
                )
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # 创建新用户（使用YAML配置中的字段映射）
            user = RbacUser(
                user_id=parsed_attrs.get('user_id', f"cas_{username}"),
                user_name=parsed_attrs.get('user_name', username),
                display_name=parsed_attrs.get('display_name', username),
                email=parsed_attrs.get('email', f"{username}@cas.local"),
                mobile=parsed_attrs.get('mobile', ''),
                department_name=parsed_attrs.get('department_name', '未分配部门'),
                group_name=parsed_attrs.get('group_name', '未分配团队'),
                user_source=parsed_attrs.get('user_source', 1),  # 1=CAS来源
                is_active=parsed_attrs.get('is_active', 1),
                is_deleted=parsed_attrs.get('is_deleted', 0),
                create_by=parsed_attrs.get('create_by', 'CAS'),
                update_by=parsed_attrs.get('update_by', 'CAS'),
                created_at=now_shanghai(),
                updated_at=now_shanghai()
            )
            self.db.add(user)
            await self.db.flush()
            
            # 创建认证记录
            auth_user = AuthUser(
                user_id=user.user_id,
                auth_type='cas',
                password_hash='',  # CAS用户不需要密码
                created_at=now_shanghai(),
                updated_at=now_shanghai()
            )
            self.db.add(auth_user)
            await self.db.flush()
            
            logger.info(f"Created new user from CAS: {username}")
        else:
            # 更新用户信息（使用YAML配置中的字段）
            if parsed_attrs.get('display_name'):
                user.display_name = parsed_attrs['display_name']
            if parsed_attrs.get('email'):
                user.email = parsed_attrs['email']
            if parsed_attrs.get('department_name'):
                user.department_name = parsed_attrs['department_name']
            if parsed_attrs.get('group_name'):
                user.group_name = parsed_attrs['group_name']
            user.last_login = now_shanghai()
            user.updated_at = now_shanghai()
            user.update_by = 'CAS'
            await self.db.flush()
            
        # 生成JWT token
        token_data = {
            "sub": user.user_id,
            "username": user.user_name,
            "roles": [],  # TODO: 从用户角色关系中获取
            "permissions": []  # TODO: 从角色权限中获取
        }
        
        access_token = JWTUtils.create_access_token(token_data)
        refresh_token = JWTUtils.create_refresh_token({"sub": user.user_id})
        
        await self.db.commit()
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "user_id": user.user_id,
                "username": user.user_name,
                "display_name": user.display_name,
                "email": user.email,
                "roles": []  # TODO: 返回实际角色
            }
        )