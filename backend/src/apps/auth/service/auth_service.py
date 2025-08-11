"""
认证服务层
处理认证相关的业务逻辑
"""

import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_
from sqlalchemy.future import select

from src.apps.auth.models import (
    AuthUser, AuthToken, AuthSession, AuthLoginHistory, 
    AuthApiKey, AuthSSOProvider
)
from src.apps.user.models import RbacUser, RbacUsersRoles, RbacRole
from src.apps.auth.utils import (
    PasswordUtils, JWTUtils, MFAUtils, APIKeyUtils,
    TokenBlacklist, generate_state_token, mask_email
)
from src.apps.auth.schema import (
    LoginRequest, LoginResponse, UserProfile,
    CreateAPIKeyRequest, CreateAPIKeyResponse, APIKeyInfo
)
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode


class AuthService:
    """认证服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))
    
    async def login_with_password(self, request: LoginRequest, ip_address: str = None, user_agent: str = None) -> LoginResponse:
        """使用密码登录"""
        async with self.db.begin():
            # 记录登录尝试
            login_history = AuthLoginHistory(
                username=request.username,
                login_type="jwt",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            try:
                # 查找用户 (使用异步查询)
                stmt = select(RbacUser).where(
                    or_(
                        RbacUser.user_name == request.username,
                        RbacUser.email == request.username
                    )
                )
                result = await self.db.execute(stmt)
                rbac_user = result.scalar_one_or_none()
                
                if not rbac_user:
                    raise BusinessException(
                        "用户名或密码错误",
                        ResponseCode.UNAUTHORIZED
                    )
                
                # 检查用户是否激活
                if rbac_user.is_active != 1:
                    raise BusinessException(
                        "账户已被禁用",
                        ResponseCode.FORBIDDEN
                    )
                
                # 获取认证信息 (使用异步查询)
                stmt = select(AuthUser).where(AuthUser.user_id == rbac_user.user_id)
                result = await self.db.execute(stmt)
                auth_user = result.scalar_one_or_none()
                
                if not auth_user:
                    # 首次登录，创建认证记录
                    auth_user = AuthUser(
                        user_id=rbac_user.user_id,
                        create_time=datetime.now(timezone.utc)
                    )
                    self.db.add(auth_user)
                    await self.db.flush()
                
                # 检查账户是否被锁定
                if auth_user.locked_until and auth_user.locked_until > datetime.now(timezone.utc):
                    remaining_minutes = (auth_user.locked_until - datetime.now(timezone.utc)).seconds // 60
                    raise BusinessException(
                        f"账户已被锁定，请{remaining_minutes}分钟后再试",
                        ResponseCode.FORBIDDEN
                    )
                
                # 验证密码
                if not auth_user.password_hash or not PasswordUtils.verify_password(
                    request.password, auth_user.password_hash
                ):
                    # 增加失败次数
                    auth_user.login_attempts += 1
                    
                    # 检查是否需要锁定账户
                    if auth_user.login_attempts >= self.max_login_attempts:
                        auth_user.locked_until = datetime.now(timezone.utc) + timedelta(
                            minutes=self.lockout_duration
                        )
                        await self.db.flush()
                        raise BusinessException(
                            f"登录失败次数过多，账户已被锁定{self.lockout_duration}分钟",
                            ResponseCode.FORBIDDEN
                        )
                    
                    await self.db.flush()
                    raise BusinessException(
                        "用户名或密码错误",
                        ResponseCode.UNAUTHORIZED
                    )
                
                # 检查MFA
                if auth_user.mfa_enabled:
                    if not request.mfa_code:
                        raise BusinessException(
                            "需要MFA验证码",
                            ResponseCode.FORBIDDEN
                        )
                    
                    if not MFAUtils.verify_totp(auth_user.mfa_secret, request.mfa_code):
                        raise BusinessException(
                            "MFA验证码错误",
                            ResponseCode.UNAUTHORIZED
                        )
                
                # 登录成功，重置失败次数
                auth_user.login_attempts = 0
                auth_user.last_login = datetime.now(timezone.utc)
                auth_user.last_login_ip = None  # 应从请求中获取
                
                # 获取用户角色和权限
                user_roles = await self._get_user_roles(rbac_user.user_id)
                user_permissions = []  # TODO: Fix async permissions
                
                # 创建令牌
                token_data = {
                    "sub": rbac_user.user_id,
                    "username": rbac_user.user_name,
                    "roles": [role["role_id"] for role in user_roles],
                    "permissions": user_permissions  # 可选：将权限加入token
                }
                
                access_token = JWTUtils.create_access_token(token_data)
                refresh_token = JWTUtils.create_refresh_token(token_data)
                
                # 保存令牌记录
                access_jti = JWTUtils.get_jti(access_token)
                refresh_jti = JWTUtils.get_jti(refresh_token)
                
                # Access Token
                access_token_record = AuthToken(
                    user_id=rbac_user.user_id,
                    token_jti=access_jti,
                    token_type="access",
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
                    device_id=request.device_id,
                    device_name=request.device_name,
                    ip_address=None,  # 应从请求中获取
                    user_agent=None,  # 应从请求中获取
                )
                self.db.add(access_token_record)
                
                # Refresh Token
                refresh_token_record = AuthToken(
                    user_id=rbac_user.user_id,
                    token_jti=refresh_jti,
                    token_type="refresh",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                    device_id=request.device_id,
                    device_name=request.device_name,
                    ip_address=None,  # 应从请求中获取
                    user_agent=None,  # 应从请求中获取
                )
                self.db.add(refresh_token_record)
                
                # 记录登录成功
                login_history.user_id = rbac_user.user_id
                login_history.success = True
                
                self.db.add(login_history)
                await self.db.flush()
                
                # 构建用户信息
                user_info = {
                    "id": str(rbac_user.id),
                    "user_id": rbac_user.user_id,
                    "username": rbac_user.user_name,
                    "display_name": rbac_user.display_name,
                    "email": rbac_user.email,
                    "roles": user_roles
                }
                
                return LoginResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type="Bearer",
                    expires_in=1800,  # 30分钟
                    user=user_info
                )
                
            except BusinessException:
                raise
            except Exception as e:
                # 记录登录失败
                login_history.success = False
                login_history.failure_reason = str(e)
                self.db.add(login_history)
                await self.db.flush()
                raise BusinessException(
                    "登录处理失败",
                    ResponseCode.INTERNAL_ERROR
                )
    
    async def register_user(self, request, ip_address: str = None, user_agent: str = None):
        """用户注册"""
        from src.apps.auth.schema import RegisterRequest, RegisterResponse
        
        async with self.db.begin():
            # 检查用户名是否已存在
            stmt = select(RbacUser).where(
                or_(
                    RbacUser.user_name == request.username,
                    RbacUser.email == request.email
                )
            )
            result = await self.db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                if existing_user.user_name == request.username:
                    raise BusinessException(
                        "用户名已存在",
                        ResponseCode.BAD_REQUEST
                    )
                else:
                    raise BusinessException(
                        "邮箱已被注册",
                        ResponseCode.BAD_REQUEST
                    )
            
            # 生成用户ID
            user_id = f"user_{int(datetime.now().timestamp())}"
            
            # 创建RBAC用户
            rbac_user = RbacUser(
                user_id=user_id,
                user_name=request.username,
                display_name=request.display_name,
                email=request.email,
                mobile="",
                department_name="默认部门",
                group_name="普通用户",
                user_source=3,  # 手动注册
                is_active=1,    # 默认激活，可根据需求改为需要审核
                create_by="system",
                update_by="system"
            )
            self.db.add(rbac_user)
            
            # 创建认证用户
            password_hash = PasswordUtils.hash_password(request.password)
            auth_user = AuthUser(
                user_id=user_id,
                password_hash=password_hash,
                require_password_change=False
            )
            self.db.add(auth_user)
            
            # 记录注册历史
            login_history = AuthLoginHistory(
                user_id=user_id,
                username=request.username,
                login_type="register",
                success=True,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(login_history)
            
            await self.db.flush()
            
            return RegisterResponse(
                success=True,
                message="注册成功",
                user={
                    "id": user_id,
                    "username": request.username,
                    "email": request.email
                }
            )
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """刷新访问令牌"""
        async with self.db.begin():
            # 解码刷新令牌
            payload = JWTUtils.decode_token(refresh_token)
            
            # 验证令牌类型
            if payload.get("type") != "refresh":
                raise BusinessException(
                    "无效的刷新令牌",
                    ResponseCode.UNAUTHORIZED
                )
            
            # 检查令牌是否被撤销
            jti = payload.get("jti")
            if TokenBlacklist.is_blacklisted(jti):
                raise BusinessException(
                    "令牌已被撤销",
                    ResponseCode.UNAUTHORIZED
                )
            
            # 检查数据库中的令牌状态
            stmt = select(AuthToken).where(
                AuthToken.token_jti == jti,
                AuthToken.revoked == False
            )
            result = await self.db.execute(stmt)
            token_record = result.scalar_one_or_none()
            
            if not token_record:
                raise BusinessException(
                    "令牌不存在或已失效",
                    ResponseCode.UNAUTHORIZED
                )
            
            # 生成新的访问令牌
            user_id = payload.get("sub")
            username = payload.get("username")
            roles = payload.get("roles", [])
            
            new_token_data = {
                "sub": user_id,
                "username": username,
                "roles": roles
            }
            
            new_access_token = JWTUtils.create_access_token(new_token_data)
            new_jti = JWTUtils.get_jti(new_access_token)
            
            # 保存新令牌记录
            new_token_record = AuthToken(
                user_id=user_id,
                token_jti=new_jti,
                token_type="access",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
                device_id=token_record.device_id,
                device_name=token_record.device_name,
                ip_address=None,  # 应从请求中获取
                user_agent=None,  # 应从请求中获取
            )
            self.db.add(new_token_record)
            
            # 更新刷新令牌的最后使用时间
            token_record.last_used_at = datetime.now(timezone.utc)
            
            await self.db.flush()
            
            return {
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": 1800
            }
    
    async def logout(self, user_id: str, current_jti: str, everywhere: bool = False):
        """登出"""
        async with self.db.begin():
            if everywhere:
                # 撤销用户的所有令牌
                stmt = select(AuthToken).where(
                    AuthToken.user_id == user_id,
                    AuthToken.revoked == False
                )
                result = await self.db.execute(stmt)
                tokens = result.scalars().all()
                
                for token in tokens:
                    token.revoked = True
                    token.revoked_at = datetime.now(timezone.utc)
                    token.revoke_reason = "用户主动登出所有设备"
                    TokenBlacklist.add(token.token_jti)
            else:
                # 只撤销当前令牌
                stmt = select(AuthToken).where(
                    AuthToken.token_jti == current_jti
                )
                result = await self.db.execute(stmt)
                token = result.scalar_one_or_none()
                
                if token:
                    token.revoked = True
                    token.revoked_at = datetime.now(timezone.utc)
                    token.revoke_reason = "用户主动登出"
                    TokenBlacklist.add(current_jti)
            
            await self.db.flush()
    
    async def get_user_profile(self, user_id: str) -> UserProfile:
        """获取用户资料"""
        try:
            # 获取RBAC用户信息
            stmt = select(RbacUser).where(
                RbacUser.user_id == user_id
            )
            result = await self.db.execute(stmt)
            rbac_user = result.scalar_one_or_none()
            
            if not rbac_user:
                raise BusinessException(
                    "用户不存在",
                    ResponseCode.NOT_FOUND
                )
            
            # 获取认证信息
            stmt = select(AuthUser).where(
                AuthUser.user_id == user_id
            )
            result = await self.db.execute(stmt)
            auth_user = result.scalar_one_or_none()
            
            # 获取角色
            roles = await self._get_user_roles(user_id)
            
            # 获取权限（这里简化处理，实际应该通过角色获取权限）
            permissions = []
            
            return UserProfile(
                id=str(rbac_user.id),
                user_id=rbac_user.user_id,
                username=rbac_user.user_name,
                display_name=rbac_user.display_name,
                email=rbac_user.email,
                mobile=rbac_user.mobile,
                department_name=rbac_user.department_name,
                group_name=rbac_user.group_name,
                roles=roles,
                permissions=permissions,
                last_login=auth_user.last_login if auth_user else None,
                mfa_enabled=auth_user.mfa_enabled if auth_user else False
            )
            
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                "获取用户资料失败",
                ResponseCode.INTERNAL_ERROR
            )
    
    async def change_password(self, user_id: str, old_password: str, new_password: str):
        """修改密码"""
        async with self.db.begin():
            # 获取认证信息
            stmt = select(AuthUser).where(
                AuthUser.user_id == user_id
            )
            result = await self.db.execute(stmt)
            auth_user = result.scalar_one_or_none()
            
            if not auth_user:
                raise BusinessException(
                    "用户不存在",
                    ResponseCode.NOT_FOUND
                )
            
            # 验证旧密码
            if not PasswordUtils.verify_password(old_password, auth_user.password_hash):
                raise BusinessException(
                    "原密码错误",
                    ResponseCode.UNAUTHORIZED
                )
            
            # 检查新密码强度
            is_strong, error_msg = PasswordUtils.is_strong_password(new_password)
            if not is_strong:
                raise BusinessException(
                    error_msg,
                    ResponseCode.BAD_REQUEST
                )
            
            # 更新密码
            auth_user.password_hash = PasswordUtils.hash_password(new_password)
            auth_user.password_changed_at = datetime.now(timezone.utc)
            auth_user.require_password_change = False
            
            await self.db.flush()
    
    async def create_api_key(
        self, 
        user_id: str, 
        request: CreateAPIKeyRequest,
        creator: str = None
    ) -> CreateAPIKeyResponse:
        """创建API密钥"""
        async with self.db.begin():
            # 生成API密钥
            api_key, prefix, key_hash = APIKeyUtils.generate_api_key()
            
            # 计算过期时间
            expires_at = None
            if request.expires_in_days:
                expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)
            
            # 创建记录
            api_key_record = AuthApiKey(
                user_id=user_id,
                key_name=request.key_name,
                key_prefix=prefix,
                key_hash=key_hash,
                mark_comment=request.mark_comment,
                scopes=json.dumps(request.scopes) if request.scopes else None,
                allowed_ips=json.dumps(request.allowed_ips) if request.allowed_ips else None,
                expires_at=expires_at,
                create_by=creator or user_id  # 使用创建者或默认为用户自己
            )
            
            self.db.add(api_key_record)
            await self.db.flush()
            await self.db.refresh(api_key_record)
            
            # 构建返回信息
            key_info = APIKeyInfo(
                key_id=str(api_key_record.id),
                user_id=user_id,
                key_name=request.key_name,
                key_prefix=prefix,
                mark_comment=request.mark_comment,
                created_at=api_key_record.create_time,
                expires_at=expires_at,
                last_used_at=None,
                is_active=True,
                scopes=request.scopes or [],
                allowed_ips=request.allowed_ips or [],
                create_by=api_key_record.create_by,
                update_by=api_key_record.update_by
            )
            
            return CreateAPIKeyResponse(
                api_key=api_key,
                key_info=key_info
            )
    
    async def _get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户角色"""
        stmt = select(
            RbacRole.role_id,
            RbacRole.role_name,
            RbacRole.description
        ).join(
            RbacUsersRoles,
            RbacUsersRoles.role_id == RbacRole.role_id
        ).where(
            RbacUsersRoles.user_id == user_id
        )
        
        result = await self.db.execute(stmt)
        user_roles = result.fetchall()
        
        return [
            {
                "role_id": role.role_id,
                "role_name": role.role_name,
                "description": role.description
            }
            for role in user_roles
        ]
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限列表（用于JWT）"""
        from .rbac_service import RBACService
        
        service = RBACService(self.db)
        permissions = await service.get_user_permissions(user_id)
        
        # 只返回权限名称列表（减少JWT大小）
        return [perm.permission_name for perm in permissions if perm.release_disable != "on"]


# 创建全局实例
auth_service = AuthService(None)  # 使用None，因为会通过依赖注入传入session