"""
SSO（单点登录）服务
处理各种SSO提供商的集成
"""

import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, quote
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, update
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode

from src.apps.auth.models import (
    AuthUser, AuthSession, AuthLoginHistory, AuthSSOProvider
)
from src.apps.user.models import RbacUser
from src.apps.auth.utils import JWTUtils, generate_state_token, generate_nonce
from src.apps.auth.schema import SSOLoginUrlResponse, LoginResponse
from src.shared.db.models import now_shanghai


class SSOService:
    """SSO服务基类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redirect_uri = os.getenv("SSO_REDIRECT_URI", "http://localhost:3000/sso/callback")
    
    async def get_login_url(self, provider_id: str) -> SSOLoginUrlResponse:
        """获取SSO登录URL"""
        # 获取提供商配置
        result = await self.db.execute(
            select(AuthSSOProvider).where(
                and_(
                    AuthSSOProvider.provider_id == provider_id,
                    AuthSSOProvider.is_active == True
                )
            )
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            raise BusinessException(
                f"SSO提供商 {provider_id} 不存在或未启用",
                ResponseCode.NOT_FOUND
            )
        
        # 根据提供商类型生成登录URL
        if provider.provider_type == "oauth2":
            return await self._get_oauth2_login_url(provider)
        elif provider.provider_type == "saml":
            return await self._get_saml_login_url(provider)
        else:
            raise BusinessException(
                f"不支持的SSO类型: {provider.provider_type}",
                ResponseCode.BAD_REQUEST
            )
    
    async def handle_callback(
        self, 
        provider_id: str, 
        code: str, 
        state: Optional[str] = None
    ) -> LoginResponse:
        """处理SSO回调"""
        # 获取提供商配置
        result = await self.db.execute(
            select(AuthSSOProvider).where(
                and_(
                    AuthSSOProvider.provider_id == provider_id,
                    AuthSSOProvider.is_active == True
                )
            )
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            raise BusinessException(
                f"SSO提供商 {provider_id} 不存在或未启用",
                ResponseCode.NOT_FOUND
            )
        
        # 根据提供商类型处理回调
        if provider.provider_type == "oauth2":
            return await self._handle_oauth2_callback(provider, code, state)
        else:
            raise BusinessException(
                f"不支持的SSO类型: {provider.provider_type}",
                ResponseCode.BAD_REQUEST
            )
    
    async def _get_oauth2_login_url(self, provider: AuthSSOProvider) -> SSOLoginUrlResponse:
        """生成OAuth2登录URL"""
        state = generate_state_token()
        nonce = generate_nonce()
        
        # 保存state到缓存（应该使用Redis）
        # 这里简化处理，实际应该保存到Redis并设置过期时间
        
        params = {
            "client_id": provider.client_id,
            "redirect_uri": provider.redirect_uri or self.redirect_uri,
            "response_type": "code",
            "scope": provider.scopes or "openid profile email",
            "state": state,
        }
        
        # 某些提供商需要nonce参数
        if "openid" in params["scope"]:
            params["nonce"] = nonce
        
        login_url = f"{provider.authorization_url}?{urlencode(params)}"
        
        return SSOLoginUrlResponse(
            url=login_url,
            state=state,
            provider=provider.provider_id
        )
    
    async def _get_saml_login_url(self, provider: AuthSSOProvider) -> SSOLoginUrlResponse:
        """生成SAML登录URL"""
        # SAML实现较复杂，这里只是示例
        raise BusinessException(
            "SAML SSO暂未实现",
            ResponseCode.NOT_IMPLEMENTED
        )
    
    async def _handle_oauth2_callback(
        self, 
        provider: AuthSSOProvider, 
        code: str, 
        state: Optional[str]
    ) -> LoginResponse:
        """处理OAuth2回调"""
        # 验证state（应该从Redis获取并验证）
        # 这里简化处理
        
        try:
            # 交换授权码获取令牌
            token_data = await self._exchange_code_for_token(provider, code)
            
            # 获取用户信息
            user_info = await self._get_oauth2_user_info(provider, token_data["access_token"])
            
            # 查找或创建用户
            user = await self._find_or_create_sso_user(provider, user_info)
            
            # 创建会话
            session = await self._create_sso_session(
                user.user_id,
                provider,
                token_data
            )
            
            # 创建JWT令牌
            token_data = {
                "sub": user.user_id,
                "username": user.user_name,
                "sso_provider": provider.provider_id,
                "session_id": session.session_id
            }
            
            access_token = JWTUtils.create_access_token(token_data)
            refresh_token = JWTUtils.create_refresh_token(token_data)
            
            # 记录登录历史
            async with self.db.begin():
                login_history = AuthLoginHistory(
                    user_id=user.user_id,
                    username=user.user_name,
                    login_type="sso",
                    success=True,
                    sso_provider=provider.provider_id,
                    login_time=now_shanghai()
                )
                self.db.add(login_history)
                await self.db.flush()
            
            # 构建用户信息
            user_info = {
                "id": str(user.id),
                "user_id": user.user_id,
                "username": user.user_name,
                "display_name": user.display_name,
                "email": user.email,
                "sso_provider": provider.provider_id
            }
            
            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=1800,
                user=user_info
            )
            
        except Exception as e:
            # 记录失败
            async with self.db.begin():
                login_history = AuthLoginHistory(
                    login_type="sso",
                    success=False,
                    failure_reason=str(e),
                    sso_provider=provider.provider_id,
                    login_time=now_shanghai()
                )
                self.db.add(login_history)
                await self.db.flush()
            
            raise BusinessException(
                "SSO登录失败",
                ResponseCode.INTERNAL_ERROR
            )
    
    async def _exchange_code_for_token(
        self, 
        provider: AuthSSOProvider, 
        code: str
    ) -> Dict[str, Any]:
        """交换授权码获取访问令牌"""
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": provider.redirect_uri or self.redirect_uri,
                "client_id": provider.client_id,
                "client_secret": provider.client_secret,
            }
            
            response = await client.post(
                provider.token_url,
                data=data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def _get_oauth2_user_info(
        self, 
        provider: AuthSSOProvider, 
        access_token: str
    ) -> Dict[str, Any]:
        """获取OAuth2用户信息"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                provider.userinfo_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get user info: {response.text}")
            
            return response.json()
    
    async def _find_or_create_sso_user(
        self, 
        provider: AuthSSOProvider, 
        user_info: Dict[str, Any]
    ) -> RbacUser:
        """查找或创建SSO用户"""
        # 提取用户属性
        sso_user_id = self._get_user_attribute(user_info, provider.user_id_attribute, "sub")
        username = self._get_user_attribute(user_info, provider.username_attribute, "preferred_username")
        email = self._get_user_attribute(user_info, provider.email_attribute, "email")
        display_name = self._get_user_attribute(user_info, provider.display_name_attribute, "name")
        
        # 查找现有用户（通过SSO ID或邮箱）
        result = await self.db.execute(
            select(AuthUser).where(
                and_(
                    AuthUser.sso_provider == provider.provider_id,
                    AuthUser.sso_user_id == sso_user_id
                )
            )
        )
        auth_user = result.scalar_one_or_none()
        
        if auth_user:
            # 返回现有用户
            result = await self.db.execute(
                select(RbacUser).where(
                    RbacUser.user_id == auth_user.user_id
                )
            )
            rbac_user = result.scalar_one_or_none()
            
            # 更新SSO属性
            async with self.db.begin():
                await self.db.execute(
                    update(AuthUser).where(
                        AuthUser.user_id == auth_user.user_id
                    ).values(
                        sso_attributes=json.dumps(user_info),
                        last_login=now_shanghai()
                    )
                )
            
            return rbac_user
        
        # 通过邮箱查找
        result = await self.db.execute(
            select(RbacUser).where(
                RbacUser.email == email
            )
        )
        rbac_user = result.scalar_one_or_none()
        
        if not rbac_user:
            # 创建新用户
            async with self.db.begin():
                user_id = f"sso_{provider.provider_id}_{secrets.token_urlsafe(8)}"
                
                rbac_user = RbacUser(
                    user_id=user_id,
                    user_name=username or email.split('@')[0],
                    display_name=display_name or username or email.split('@')[0],
                    email=email,
                    mobile="",  # SSO用户可能没有手机号
                    department_name="SSO用户",
                    group_name="SSO",
                    user_source=2,  # 2表示CAS
                    is_active=1,
                    create_by="SSO",
                    update_by="SSO",
                    create_time=now_shanghai(),
                    update_time=now_shanghai()
                )
                self.db.add(rbac_user)
                await self.db.flush()
        
        # 创建或更新认证记录
        async with self.db.begin():
            result = await self.db.execute(
                select(AuthUser).where(
                    AuthUser.user_id == rbac_user.user_id
                )
            )
            auth_user = result.scalar_one_or_none()
            
            if not auth_user:
                auth_user = AuthUser(
                    user_id=rbac_user.user_id,
                    sso_provider=provider.provider_id,
                    sso_user_id=sso_user_id,
                    sso_attributes=json.dumps(user_info),
                    last_login=now_shanghai(),
                    created_at=now_shanghai()
                )
                self.db.add(auth_user)
            else:
                await self.db.execute(
                    update(AuthUser).where(
                        AuthUser.user_id == rbac_user.user_id
                    ).values(
                        sso_provider=provider.provider_id,
                        sso_user_id=sso_user_id,
                        sso_attributes=json.dumps(user_info),
                        last_login=now_shanghai()
                    )
                )
            
            await self.db.flush()
        
        return rbac_user
    
    async def _create_sso_session(
        self, 
        user_id: str, 
        provider: AuthSSOProvider,
        token_data: Dict[str, Any]
    ) -> AuthSession:
        """创建SSO会话"""
        async with self.db.begin():
            session = AuthSession(
                session_id=secrets.token_urlsafe(32),
                user_id=user_id,
                sso_provider=provider.provider_id,
                sso_access_token=token_data.get("access_token"),  # 应加密存储
                sso_refresh_token=token_data.get("refresh_token"),  # 应加密存储
                sso_id_token=token_data.get("id_token"),
                expires_at=now_shanghai() + timedelta(hours=8),  # 8小时
                created_at=now_shanghai(),
                ip_address=None,  # 应从请求获取
                user_agent=None   # 应从请求获取
            )
            
            self.db.add(session)
            await self.db.flush()
            await self.db.refresh(session)
        
        return session
    
    def _get_user_attribute(
        self, 
        user_info: Dict[str, Any], 
        attribute_path: Optional[str], 
        default_path: str
    ) -> Any:
        """从用户信息中提取属性"""
        path = attribute_path or default_path
        
        # 支持嵌套属性，如 "profile.email"
        value = user_info
        for key in path.split('.'):
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value