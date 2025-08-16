"""
User and RBAC (Role-Based Access Control) Models
用户和基于角色的访问控制模型 - 根据实际数据库表结构
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, TIMESTAMP, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai, BaseModel, JSONType
import json


class RbacUser(BaseModel):
    """RBAC用户模型 - 对应rbac_users表"""
    __tablename__ = "rbac_users"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), unique=True, nullable=False, comment="用户ID")
    user_name = Column(String(50), unique=True, nullable=False, comment="用户名")
    display_name = Column(String(50), nullable=False, comment="显示名称")
    department_name = Column(String(50), nullable=False, comment="部门名称")
    group_name = Column(String(50), nullable=False, comment="组名")
    email = Column(String(100), nullable=False, comment="邮箱")
    mobile = Column(String(20), nullable=False, comment="手机号")
    user_source = Column(Integer, default=2, nullable=False, comment="用户来源：1=cas,2=local")
    
    # 认证相关字段（本地用户使用）
    locked_until = Column(DateTime, nullable=True, comment="账户锁定到期时间")
    login_attempts = Column(Integer, default=0, nullable=False, comment="登录失败次数")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    mfa_enabled = Column(Boolean, default=False, nullable=False, comment="是否启用MFA")
    mfa_secret = Column(String(255), nullable=True, comment="MFA密钥")
    password_hash = Column(String(255), nullable=True, comment="密码哈希（本地认证用）")
    
    is_active = Column(Integer, default=1, nullable=False, comment="用户是否活跃,1活跃,0冻结")
    is_deleted = Column(Integer, default=0, nullable=False, comment="是否删除:0未删除,1已删除")
    
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")

    def to_dict(self, exclude_fields=None, include_relations=True):
        """重写to_dict方法，添加关联关系"""
        result = super().to_dict(exclude_fields=exclude_fields)
        
        if include_relations:
            # 添加动态角色信息（如果存在）
            if hasattr(self, 'roles'):
                result['roles'] = [role.to_dict(include_relations=False) for role in self.roles]
            else:
                result['roles'] = []
            
        return result


class RbacRole(BaseModel):
    """RBAC角色模型 - 对应rbac_roles表"""
    __tablename__ = "rbac_roles"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    role_id = Column(Integer, unique=True, default=-1, nullable=False, comment="角色ID")
    role_name = Column(String(50), nullable=False, comment="角色名称")
    description = Column(String(200), nullable=False, comment="角色描述")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")

    def to_dict(self, exclude_fields=None, include_relations=False):
        """重写to_dict方法，添加统计信息"""
        result = super().to_dict(exclude_fields=exclude_fields)
        
        # 添加动态统计属性（如果存在）
        if hasattr(self, 'permission_count'):
            result['permission_count'] = self.permission_count
        else:
            result['permission_count'] = 0
            
        if hasattr(self, 'user_count'):
            result['user_count'] = self.user_count
        else:
            result['user_count'] = 0
        
        return result


class RbacPermission(BaseModel):
    """RBAC权限模型 - 对应rbac_permissions表"""
    __tablename__ = "rbac_permissions"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    permission_id = Column(Integer, unique=True, default=-1, nullable=False, comment="权限ID")
    permission_description = Column(String(200), nullable=False, comment="权限描述")
    permission_name = Column(String(100), nullable=False, comment="权限名称(API路径)")
    http_method = Column(String(10), default='*', nullable=False, comment="HTTP方法: GET,POST,PUT,DELETE,*")
    release_disable = Column(String(10), default='off', nullable=False, comment="发布禁用")
    permission_allow_client = Column(Text, nullable=True, comment="允许的客户端")
    is_deleted = Column(Integer, default=0, nullable=False, comment="是否删除:0未删除,1已删除")
    create_time = Column(DateTime, default=now_shanghai, nullable=False, index=True)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")

    def to_dict(self, exclude_fields=None, include_relations=False):
        """重写to_dict方法，添加统计信息"""
        result = super().to_dict(exclude_fields=exclude_fields)
        
        # 添加动态统计属性（如果存在）
        if hasattr(self, 'permission_count'):
            result['permission_count'] = self.permission_count
        if hasattr(self, 'user_count'):
            result['user_count'] = self.user_count
            
        return result


class RbacMenu(BaseModel):
    """RBAC菜单模型 - 对应rbac_menus表"""
    __tablename__ = "rbac_menus"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    menu_id = Column(Integer, unique=True, default=-1, nullable=False, comment="菜单ID")
    menu_name = Column(String(50), nullable=False, comment="菜单名称")
    menu_icon = Column(String(50), nullable=False, comment="菜单图标")
    parent_id = Column(Integer, default=-1, nullable=False, comment="父菜单ID")
    route_path = Column(String(200), nullable=False, comment="路由路径")
    redirect_path = Column(String(200), nullable=False, comment="重定向路径")
    menu_component = Column(String(100), nullable=False, comment="组件名称")
    show_menu = Column(Integer, default=0, nullable=False, comment="是否显示菜单")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序顺序")
    create_time = Column(TIMESTAMP, default=now_shanghai, nullable=False)
    update_time = Column(TIMESTAMP, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")


class RbacUsersRoles(BaseModel):
    """用户角色关联表 - 对应rbac_users_roles表"""
    __tablename__ = "rbac_users_roles"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True, comment="用户ID")
    role_id = Column(Integer, default=-1, nullable=False, comment="角色ID")
    is_deleted = Column(Integer, default=0, nullable=False, comment="是否删除:0未删除,1已删除")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")


class RbacRolesPermissions(BaseModel):
    """角色权限关联表 - 对应rbac_roles_permissions表"""
    __tablename__ = "rbac_roles_permissions"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    role_id = Column(Integer, default=-1, nullable=False, index=True, comment="角色ID")
    back_permission_id = Column(Integer, default=-1, nullable=False, comment="后端权限ID")
    front_permission_id = Column(Integer, default=-1, nullable=False, comment="前端权限ID")
    permission_type = Column(Integer, default=-1, nullable=False, comment="权限类型")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")


class User(Base):
    """User model matching users table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200), nullable=True)
    email = Column(String(255), nullable=True)
    user_type = Column(String(20), default='regular', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    preferences = Column(JSONType, nullable=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    def to_dict(self):
        """Convert model to dictionary."""
        preferences = self.preferences or {}
        if isinstance(preferences, str):
            try:
                preferences = json.loads(preferences)
            except:
                preferences = {}

        return {
            'id': self.id,
            'user_name': self.user_name,
            'display_name': self.display_name,
            'email': self.email,
            'user_type': self.user_type,
            'is_active': self.is_active,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'avatar_url': self.avatar_url,
            'preferences': preferences,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }


class UserThread(Base):
    """User Thread model matching user_threads table."""
    __tablename__ = "user_threads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(100), nullable=False, index=True)
    thread_id = Column(String(255), nullable=False, index=True)
    thread_title = Column(String(500), nullable=True)
    agent_id = Column(String(100), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    last_message_time = Column(DateTime, nullable=True)
    create_at = Column(DateTime, default=now_shanghai, nullable=False)
    update_at = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_name', 'thread_id', name='uk_user_thread'),
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'user_name': self.user_name,
            'thread_id': self.thread_id,
            'thread_title': self.thread_title,
            'agent_id': self.agent_id,
            'is_archived': self.is_archived,
            'message_count': self.message_count,
            'last_message_time': self.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_message_time else None,
            'create_at': self.create_at.strftime('%Y-%m-%d %H:%M:%S') if self.create_at else None,
            'update_at': self.update_at.strftime('%Y-%m-%d %H:%M:%S') if self.update_at else None,
        }