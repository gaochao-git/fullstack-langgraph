"""
CAS (Central Authentication Service) 集成服务
使用python-cas库简化集成
"""

import secrets
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import timedelta

try:
    from cas import CASClient
except ImportError:
    # 如果没有安装python-cas，使用自定义实现
    CASClient = None
    import httpx
    import xml.etree.ElementTree as ET

from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.logging import get_logger
from src.shared.core.config import settings
from src.apps.auth.models import AuthSession
from src.apps.user.models import RbacUser
from src.apps.auth.utils import CASAttributeParser
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
        
        # 初始化CAS客户端（如果安装了python-cas）
        if CASClient:
            self.cas_client = CASClient(
                version=int(self.cas_version) if self.cas_version else 3,
                service_url=self.service_url,
                server_url=self.cas_server_url
            )
        else:
            self.cas_client = None
        
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
        if self.cas_client:
            # 使用python-cas库
            try:
                # python-cas是同步的，需要在异步环境中调用
                import asyncio
                loop = asyncio.get_event_loop()
                
                # 在线程池中执行同步操作
                user, attributes, pgtiou = await loop.run_in_executor(
                    None,
                    self.cas_client.verify_ticket,
                    ticket
                )
                
                if not user:
                    raise BusinessException(
                        "CAS票据验证失败",
                        ResponseCode.UNAUTHORIZED
                    )
                
                logger.info(f"CAS validation successful for user: {user}")
                
                return {
                    'username': user,
                    'attributes': attributes or {}
                }
                
            except Exception as e:
                logger.error(f"CAS validation error: {e}")
                raise BusinessException(
                    "CAS验证失败",
                    ResponseCode.UNAUTHORIZED
                )
        else:
            # 使用自定义实现（原有代码）
            return await self._validate_ticket_custom(ticket)
    
    async def _validate_ticket_custom(self, ticket: str) -> Dict[str, Any]:
        """自定义的票据验证实现（备用）"""
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
            
    async def process_cas_login(self, ticket: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        处理CAS登录 - 纯Session模式
        
        Args:
            ticket: CAS票据
            ip_address: 客户端IP
            user_agent: 客户端UA
            
        Returns:
            CAS会话信息（不发放JWT）
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
            # 生成与本地用户一致的user_id格式
            import time
            timestamp = int(time.time() * 1000)
            user_id = parsed_attrs.get('user_id', f"user_{timestamp}")
            
            user = RbacUser(
                user_id=user_id,
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
                update_by=parsed_attrs.get('update_by', 'CAS')
            )
            self.db.add(user)
            await self.db.flush()
            
            # CAS用户不创建auth_user记录（可选）
            # 因为CAS用户不需要密码，认证完全依赖CAS Server
            
            # 为新CAS用户分配默认角色
            from src.apps.user.models import RbacRole, RbacUsersRoles
            # 查找默认角色（假设有一个名为"普通用户"的角色）
            result = await self.db.execute(
                select(RbacRole).where(
                    RbacRole.role_name == "普通用户"
                )
            )
            default_role = result.scalar_one_or_none()
            
            if default_role:
                user_role = RbacUsersRoles(
                    user_id=user.user_id,
                    role_id=default_role.role_id,
                    create_by='CAS',
                    update_by='CAS'
                )
                self.db.add(user_role)
                await self.db.flush()
                logger.info(f"Assigned default role '{default_role.role_name}' to CAS user: {username}")
            else:
                logger.warning(f"No default role found for CAS user: {username}")
            
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
            
        # 创建CAS Session（纯Session管理，不涉及JWT）
        from src.apps.auth.models import AuthSession
        cas_session = AuthSession(
            session_id=secrets.token_urlsafe(32),
            user_id=user.user_id,
            sso_provider='cas',
            sso_session_id=ticket,  # 保存CAS票据作为关联
            expires_at=now_shanghai() + timedelta(hours=self.session_timeout/3600),  # session_timeout是秒，转换为小时
            ip_address=ip_address,
            user_agent=user_agent,
            last_accessed_at=now_shanghai()
        )
        self.db.add(cas_session)
        await self.db.flush()
        
        # 记录登录历史
        from src.apps.auth.models import AuthLoginHistory
        login_history = AuthLoginHistory(
            user_id=user.user_id,
            username=user.user_name,
            login_type="sso",
            success=True,
            sso_provider="cas",
            ip_address=ip_address,
            user_agent=user_agent,
            login_time=now_shanghai()
        )
        self.db.add(login_history)
        
        await self.db.commit()
        
        # 返回Session信息（不返回JWT）
        return {
            "session_id": cas_session.session_id,
            "expires_in": self.session_timeout * 3600,  # 转换为秒
            "user": {
                "user_id": user.user_id,
                "username": user.user_name,
                "display_name": user.display_name,
                "email": user.email,
                "department": user.department_name,
                "auth_type": "cas"
            }
        }