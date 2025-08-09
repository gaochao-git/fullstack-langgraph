"""
RBAC权限服务
处理用户角色权限相关的业务逻辑
"""

from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, update, delete
from fastapi import HTTPException, status
from functools import lru_cache
import json
import re

from src.apps.user.models import (
    RbacUser, RbacRole, RbacPermission, RbacMenu,
    RbacUsersRoles, RbacRolesPermissions
)
from src.shared.db.models import now_shanghai


class RBACService:
    """RBAC权限服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_roles(self, user_id: str) -> List[RbacRole]:
        """获取用户的所有角色"""
        result = await self.db.execute(
            select(RbacRole).join(
                RbacUsersRoles,
                RbacUsersRoles.role_id == RbacRole.role_id
            ).where(
                RbacUsersRoles.user_id == user_id
            )
        )
        roles = result.scalars().all()
        
        return list(roles)
    
    async def get_user_permissions(self, user_id: str) -> List[RbacPermission]:
        """获取用户的所有权限（通过角色）"""
        # 获取用户的所有角色ID
        role_ids_result = await self.db.execute(
            select(RbacUsersRoles.role_id).where(
                RbacUsersRoles.user_id == user_id
            )
        )
        role_ids = [row[0] for row in role_ids_result.fetchall()]
        
        if not role_ids:
            return []
        
        # 获取这些角色的所有权限
        result = await self.db.execute(
            select(RbacPermission).join(
                RbacRolesPermissions,
                RbacRolesPermissions.back_permission_id == RbacPermission.permission_id
            ).where(
                RbacRolesPermissions.role_id.in_(role_ids)
            ).distinct()
        )
        permissions = result.scalars().all()
        
        return list(permissions)
    
    async def get_user_menus(self, user_id: str) -> List[RbacMenu]:
        """获取用户可访问的菜单"""
        # 获取用户的所有角色ID
        role_ids_result = await self.db.execute(
            select(RbacUsersRoles.role_id).where(
                RbacUsersRoles.user_id == user_id
            )
        )
        role_ids = [row[0] for row in role_ids_result.fetchall()]
        
        if not role_ids:
            return []
        
        # 获取这些角色可访问的菜单（通过前端权限ID）
        result = await self.db.execute(
            select(RbacMenu).join(
                RbacRolesPermissions,
                RbacRolesPermissions.front_permission_id == RbacMenu.menu_id
            ).where(
                and_(
                    RbacRolesPermissions.role_id.in_(role_ids),
                    RbacMenu.show_menu == 1  # 只返回需要显示的菜单
                )
            ).distinct()
        )
        menus = result.scalars().all()
        
        return list(menus)
    
    async def check_permission(
        self, 
        user_id: str, 
        resource: str, 
        action: str = "*"
    ) -> bool:
        """
        检查用户是否有特定权限
        
        Args:
            user_id: 用户ID
            resource: 资源路径，如 /api/v1/users
            action: HTTP方法，如 GET, POST, PUT, DELETE, *
        
        Returns:
            bool: 是否有权限
        """
        permissions = await self.get_user_permissions(user_id)
        
        for perm in permissions:
            # 检查是否被禁用
            if perm.release_disable == "on":
                continue
            
            # 检查HTTP方法
            if perm.http_method != "*" and perm.http_method != action:
                continue
            
            # 检查资源路径（支持通配符）
            if self._match_resource(perm.permission_name, resource):
                return True
        
        return False
    
    async def check_role(self, user_id: str, role_names: List[str]) -> bool:
        """检查用户是否有指定角色"""
        user_roles = await self.get_user_roles(user_id)
        user_role_names = [role.role_name for role in user_roles]
        
        # 检查是否有任一所需角色
        return any(role in user_role_names for role in role_names)
    
    async def assign_role_to_user(
        self, 
        user_id: str, 
        role_id: int, 
        created_by: str
    ):
        """给用户分配角色"""
        async with self.db.begin():
            # 检查是否已存在
            result = await self.db.execute(
                select(RbacUsersRoles).where(
                    and_(
                        RbacUsersRoles.user_id == user_id,
                        RbacUsersRoles.role_id == role_id
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                return
            
            # 创建关联
            user_role = RbacUsersRoles(
                user_id=user_id,
                role_id=role_id,
                create_by=created_by,
                update_by=created_by,
                create_time=now_shanghai(),
                update_time=now_shanghai()
            )
            
            self.db.add(user_role)
            await self.db.flush()
    
    async def remove_role_from_user(self, user_id: str, role_id: int):
        """移除用户的角色"""
        async with self.db.begin():
            await self.db.execute(
                delete(RbacUsersRoles).where(
                    and_(
                        RbacUsersRoles.user_id == user_id,
                        RbacUsersRoles.role_id == role_id
                    )
                )
            )
    
    async def get_role_by_name(self, role_name: str) -> Optional[RbacRole]:
        """根据角色名获取角色"""
        result = await self.db.execute(
            select(RbacRole).where(
                RbacRole.role_name == role_name
            )
        )
        return result.scalar_one_or_none()
    
    async def create_default_roles(self):
        """创建默认角色"""
        async with self.db.begin():
            default_roles = [
                {
                    "role_id": 1,
                    "role_name": "super_admin",
                    "description": "超级管理员",
                },
                {
                    "role_id": 2,
                    "role_name": "admin",
                    "description": "管理员",
                },
                {
                    "role_id": 3,
                    "role_name": "user",
                    "description": "普通用户",
                }
            ]
            
            for role_data in default_roles:
                # 检查是否已存在
                result = await self.db.execute(
                    select(RbacRole).where(
                        RbacRole.role_name == role_data["role_name"]
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    role = RbacRole(
                        role_id=role_data["role_id"],
                        role_name=role_data["role_name"],
                        description=role_data["description"],
                        create_by="system",
                        update_by="system",
                        create_time=now_shanghai(),
                        update_time=now_shanghai()
                    )
                    self.db.add(role)
            
            await self.db.flush()
    
    async def get_permission_tree(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的权限树
        返回格式化的权限数据，便于前端使用
        """
        roles = await self.get_user_roles(user_id)
        permissions = await self.get_user_permissions(user_id)
        menus = await self.get_user_menus(user_id)
        
        # 构建菜单树
        menu_tree = self._build_menu_tree(menus)
        
        # 构建权限映射
        permission_map = {
            perm.permission_name: {
                "id": perm.permission_id,
                "name": perm.permission_name,
                "description": perm.permission_description,
                "method": perm.http_method,
                "enabled": perm.release_disable != "on"
            }
            for perm in permissions
        }
        
        return {
            "roles": [
                {
                    "id": role.role_id,
                    "name": role.role_name,
                    "description": role.description
                }
                for role in roles
            ],
            "permissions": permission_map,
            "menus": menu_tree
        }
    
    def _match_resource(self, pattern: str, resource: str) -> bool:
        """
        匹配资源路径
        支持通配符：
        - * 匹配任意字符（不包括/）
        - ** 匹配任意字符（包括/）
        """
        # 将通配符转换为正则表达式
        regex_pattern = pattern.replace("**", ".*").replace("*", "[^/]*")
        regex_pattern = f"^{regex_pattern}$"
        
        return bool(re.match(regex_pattern, resource))
    
    def _build_menu_tree(self, menus: List[RbacMenu]) -> List[Dict[str, Any]]:
        """构建菜单树结构"""
        menu_dict = {}
        root_menus = []
        
        # 先将所有菜单放入字典
        for menu in menus:
            menu_data = {
                "id": menu.menu_id,
                "name": menu.menu_name,
                "icon": menu.menu_icon,
                "path": menu.route_path,
                "component": menu.menu_component,
                "redirect": menu.redirect_path,
                "parent_id": menu.parent_id,
                "children": []
            }
            menu_dict[menu.menu_id] = menu_data
        
        # 构建树结构
        for menu_data in menu_dict.values():
            if menu_data["parent_id"] == -1:
                root_menus.append(menu_data)
            else:
                parent = menu_dict.get(menu_data["parent_id"])
                if parent:
                    parent["children"].append(menu_data)
        
        return root_menus


class PermissionCache:
    """权限缓存（用于提高性能）"""
    
    def __init__(self, cache_ttl: int = 300):  # 5分钟缓存
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
    
    @lru_cache(maxsize=1000)
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """获取用户权限集合（缓存）"""
        # 实际应该使用Redis等缓存
        # 这里简化处理
        return set()
    
    def invalidate_user(self, user_id: str):
        """清除用户的权限缓存"""
        self.get_user_permissions.cache_clear()


# 全局权限缓存实例
permission_cache = PermissionCache()


async def check_api_permission(
    user_id: str,
    path: str,
    method: str,
    db: AsyncSession
) -> bool:
    """
    检查API权限的便捷函数
    
    Args:
        user_id: 用户ID
        path: API路径
        method: HTTP方法
        db: 数据库会话
    
    Returns:
        bool: 是否有权限
    """
    service = RBACService(db)
    return await service.check_permission(user_id, path, method)


async def get_user_menu_tree(user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """获取用户菜单树的便捷函数"""
    service = RBACService(db)
    permission_data = await service.get_permission_tree(user_id)
    return permission_data["menus"]