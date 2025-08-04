"""
RBAC (Role-Based Access Control) Models
基于角色的访问控制模型 - 根据实际数据库表结构
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, TIMESTAMP
from sqlalchemy.orm import relationship
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai, BaseModel


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
    user_source = Column(Integer, default=3, nullable=False, comment="用户来源")
    is_active = Column(Integer, default=1, nullable=False, comment="是否激活")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")

    def to_dict(self, exclude_fields=None, include_relations=True):
        """重写to_dict方法，添加关联关系"""
        result = super().to_dict(exclude_fields=exclude_fields)
        
        if include_relations:
            # 获取用户角色
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
        
        # 添加统计信息
        result['permission_count'] = 0
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
    create_time = Column(DateTime, default=now_shanghai, nullable=False, index=True)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(50), nullable=False, comment="创建人")
    update_by = Column(String(50), nullable=False, comment="更新人")

    def to_dict(self, exclude_fields=None, include_relations=False):
        """重写to_dict方法"""
        result = super().to_dict(exclude_fields=exclude_fields)
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