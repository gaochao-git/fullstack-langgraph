"""
CAS (Central Authentication Service) 集成服务
使用python-cas库简化集成
"""

import asyncio
import secrets
import time
import json
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from cas import CASClient

from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.logging import get_logger
from src.shared.core.config import settings
from src.apps.auth.models import AuthSession, AuthLoginHistory
from src.apps.user.models import RbacUser, RbacRole, RbacUsersRoles
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
        self.session_timeout = settings.CAS_SESSION_TIMEOUT
        self.check_next = settings.CAS_CHECK_NEXT
        self.single_logout_enabled = settings.CAS_SINGLE_LOGOUT_ENABLED
        
        
        # 初始化CAS客户端
        self.cas_client = CASClient(
            version=int(self.cas_version),
            service_url=self.service_url,
            server_url=self.cas_server_url,
            verify_ssl_certificate=self.verify_ssl,
            renew=False,  # 不强制重新认证
            extra_login_params={},  # 可以添加额外的登录参数
            username_attribute=None  # 使用默认的用户名属性
        )
        
    def get_login_url(self) -> str:
        """获取CAS登录URL"""
        # 使用 CAS 客户端生成登录URL，避免手动拼接导致的问题
        login_url = self.cas_client.get_login_url()
        return login_url
    
    def get_logout_url(self, redirect_url: Optional[str] = None) -> str:
        """获取CAS登出URL"""
        # 使用 CAS 客户端生成登出URL
        logout_url = self.cas_client.get_logout_url(redirect_url)
        return logout_url
    
    async def validate_ticket(self, ticket: str) -> Dict[str, Any]:
        """
        验证CAS票据
        
        Args:
            ticket: CAS票据
            
        Returns:
            包含用户信息的字典
        """
        # 使用python-cas库
        try:
            # python-cas是同步的，需要在异步环境中调用
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
            logger.error(f"CAS validation error: {e}", exc_info=True)
            raise BusinessException(
                "CAS验证失败",
                ResponseCode.UNAUTHORIZED
            )
    
    def parse_cas_attributes(self, username: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析CAS返回的用户属性
        
        这是CAS属性映射的核心方法，不同公司可以通过修改此方法来适配自己的CAS属性格式
        
        Args:
            username: CAS返回的用户名
            attributes: CAS返回的属性字典
            
        Returns:
            解析后的用户属性字典，包含数据库所需的所有字段
            
        示例CAS属性:
        {
            "display_name": "张三",
            "username": "zhangsan", 
            "email": "zhangsan@company.com",
            "group_name": "CN=zhangsan,OU=团队名称,OU=部门名称"
        }
        """
        parsed = {}
        
        # 1. 直接映射的字段
        parsed['user_name'] = attributes.get('username', username)
        parsed['display_name'] = attributes.get('display_name', username)
        parsed['email'] = attributes.get('email', '')  # 获取不到时为空字符串
        parsed['mobile'] = attributes.get('mobile', '')
        
        # 2. 解析group_name获取部门和团队信息
        group_name = attributes.get('group_name', '')
        if group_name:
            # 解析DN格式: CN=zhangsan,OU=团队名称,OU=部门名称
            parts = [p.strip() for p in group_name.split(',')]
            ou_values = []
            
            for part in parts:
                if part.startswith('OU='):
                    ou_values.append(part[3:])
            
            # 第一个OU作为团队，第二个OU作为部门
            if len(ou_values) >= 1:
                parsed['group_name'] = ou_values[0]
            else:
                parsed['group_name'] = '未分配团队'
                
            if len(ou_values) >= 2:
                parsed['department_name'] = ou_values[1]
            else:
                parsed['department_name'] = '未分配部门'
        else:
            parsed['group_name'] = '未分配团队'
            parsed['department_name'] = '未分配部门'
        
        # 3. 生成user_id (使用cas_前缀)
        parsed['user_id'] = f"cas_{parsed['user_name']}"
        
        # 4. 设置固定字段
        parsed['user_source'] = 1  # 1=CAS来源
        parsed['is_active'] = 1
        parsed['is_deleted'] = 0
        parsed['create_by'] = 'CAS'
        parsed['update_by'] = 'CAS'
        
        # 5. 其他可选字段
        parsed['position'] = attributes.get('position', '')
        parsed['org_code'] = attributes.get('org_code', '')
        
        return parsed
    
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
        
        # 记录CAS返回的原始数据
        logger.info(f"CAS验证成功，返回的用户信息:")
        logger.info(f"  - 用户名: {username}")
        logger.info(f"  - 原始属性: {json.dumps(attributes, ensure_ascii=False, indent=2)}")
        
        # 使用独立方法解析CAS属性
        parsed_attrs = self.parse_cas_attributes(username, attributes)
        logger.info(f"  - 解析后属性: {json.dumps(parsed_attrs, ensure_ascii=False, indent=2)}")
        
        # 查找用户（只根据用户名查找，避免邮箱冲突）
        user_name = parsed_attrs.get('user_name', username)
        result = await self.db.execute(
            select(RbacUser).where(
                RbacUser.user_name == user_name
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # 创建新用户（使用解析后的属性）
            # 如果配置中没有生成user_id，使用时间戳
            if 'user_id' not in parsed_attrs:
                timestamp = int(time.time() * 1000)
                parsed_attrs['user_id'] = f"user_{timestamp}"
            
            # 创建用户对象，使用解析后的所有属性
            user = RbacUser(**{
                key: value for key, value in parsed_attrs.items()
                if hasattr(RbacUser, key) and key not in ['create_time', 'update_time']
            })
            
            self.db.add(user)
            await self.db.flush()
            
            # 为新CAS用户分配默认角色
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
                    create_by=parsed_attrs.get('create_by', 'CAS'),
                    update_by=parsed_attrs.get('update_by', 'CAS')
                )
                self.db.add(user_role)
                await self.db.flush()
                logger.info(f"Assigned default role '{default_role.role_name}' to CAS user: {user_name}")
            else:
                logger.warning(f"No default role found for CAS user: {user_name}")
            
            logger.info(f"Created new CAS user: {user_name} (ID: {user.user_id})")
        else:
            # 每次登录都更新用户信息（基于配置文件的映射）
            # 更新所有从CAS获取到的属性，但不更新系统字段
            update_fields = [
                'display_name', 'email', 'department_name', 'group_name', 
                'mobile', 'position', 'org_code'
            ]
            
            for field in update_fields:
                if field in parsed_attrs and hasattr(user, field):
                    setattr(user, field, parsed_attrs[field])
            
            # 更新登录时间和更新信息
            user.last_login = now_shanghai()
            user.updated_at = now_shanghai()
            user.update_by = parsed_attrs.get('update_by', 'CAS')
            
            await self.db.flush()
            logger.info(f"Updated CAS user information: {user_name}")
            
        # 创建CAS Session（纯Session管理，不涉及JWT）
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