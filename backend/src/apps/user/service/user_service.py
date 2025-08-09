"""RBAC服务层 - 用户权限管理"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, distinct

from src.apps.user.models import (
    RbacUser, RbacRole, RbacPermission, RbacMenu, 
    RbacUsersRoles, RbacRolesPermissions
)
from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.apps.user.schema import (
    UserCreateRequest, UserUpdateRequest, UserQueryParams,
    RoleCreateRequest, RoleUpdateRequest, RoleQueryParams,
    PermissionCreateRequest, PermissionUpdateRequest, PermissionQueryParams,
    MenuCreateRequest, MenuUpdateRequest, MenuQueryParams,
    UserRoleCreateRequest, RolePermissionCreateRequest
)
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode

logger = get_logger(__name__)


class RbacUserService:
    """用户管理服务"""
    
    async def create_user(
        self, 
        db: AsyncSession, 
        user_data: UserCreateRequest,
        create_by: str = 'system'
    ) -> RbacUser:
        """创建用户"""
        async with db.begin():
            # 检查用户是否存在
            result = await db.execute(
                select(RbacUser).where(
                    or_(
                        RbacUser.user_id == user_data.user_id,
                        RbacUser.user_name == user_data.user_name,
                        RbacUser.email == user_data.email
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise BusinessException("用户ID、用户名或邮箱已存在", ResponseCode.CONFLICT)
            
            # 创建用户
            data = user_data.dict(exclude={'role_ids'})
            data['create_by'] = create_by
            data['update_by'] = create_by
            data['create_time'] = now_shanghai()
            data['update_time'] = now_shanghai()
            
            logger.info(f"Creating user: {user_data.user_id}")
            user = RbacUser(**data)
            db.add(user)
            await db.flush()
            
            # 分配角色
            if user_data.role_ids:
                await self._assign_roles_to_user(db, user.user_id, user_data.role_ids, create_by)
            
            await db.refresh(user)
            return user
    
    async def get_user_by_id(
        self, 
        db: AsyncSession, 
        user_id: str
    ) -> Optional[RbacUser]:
        """根据用户ID获取用户"""
        result = await db.execute(
            select(RbacUser).where(RbacUser.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def list_users(
        self, 
        db: AsyncSession, 
        params: UserQueryParams
    ) -> Tuple[List[RbacUser], int]:
        """用户列表查询"""
        # 构建查询条件
        query = select(RbacUser)
        conditions = []
        
        if params.search:
            conditions.append(
                RbacUser.user_name.contains(params.search) |
                RbacUser.display_name.contains(params.search) |
                RbacUser.email.contains(params.search)
            )
        if params.is_active is not None:
            conditions.append(RbacUser.is_active == params.is_active)
        if params.department_name:
            conditions.append(RbacUser.department_name == params.department_name)
        if params.group_name:
            conditions.append(RbacUser.group_name == params.group_name)
        if params.user_source is not None:
            conditions.append(RbacUser.user_source == params.user_source)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 分页查询
        query = query.order_by(RbacUser.create_time.desc())
        query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
        result = await db.execute(query)
        users = list(result.scalars().all())
        
        # 为每个用户加载角色信息
        for user in users:
            # 查询用户的角色关联
            user_roles_result = await db.execute(
                select(RbacUsersRoles).where(RbacUsersRoles.user_id == user.user_id)
            )
            user_roles = list(user_roles_result.scalars().all())
            
            # 获取角色详细信息
            roles = []
            for user_role in user_roles:
                role_result = await db.execute(
                    select(RbacRole).where(RbacRole.role_id == user_role.role_id)
                )
                role = role_result.scalar_one_or_none()
                if role:
                    roles.append(role)
            
            # 动态添加角色信息到用户对象
            user.roles = roles
        
        # 计算总数
        count_query = select(func.count(RbacUser.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return users, total
    
    async def update_user(
        self, 
        db: AsyncSession, 
        user_id: str, 
        user_data: UserUpdateRequest,
        update_by: str = 'system'
    ) -> Optional[RbacUser]:
        """更新用户"""
        async with db.begin():
            # 检查用户是否存在
            result = await db.execute(
                select(RbacUser).where(RbacUser.user_id == user_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                raise BusinessException("用户不存在", ResponseCode.NOT_FOUND)
            
            # 更新数据
            data = user_data.dict(exclude_unset=True, exclude={'role_ids'})
            data['update_by'] = update_by
            data['update_time'] = now_shanghai()
            
            logger.info(f"Updating user: {user_id}")
            await db.execute(
                update(RbacUser).where(RbacUser.user_id == user_id).values(**data)
            )
            
            # 更新角色关联
            if user_data.role_ids is not None:
                await self._update_user_roles(db, user_id, user_data.role_ids, update_by)
            
            # 返回更新后的数据
            result = await db.execute(
                select(RbacUser).where(RbacUser.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def delete_user(
        self, 
        db: AsyncSession, 
        user_id: str
    ) -> bool:
        """删除用户"""
        async with db.begin():
            # 先删除用户角色关联
            await db.execute(
                delete(RbacUsersRoles).where(RbacUsersRoles.user_id == user_id)
            )
            
            # 删除用户
            result = await db.execute(
                delete(RbacUser).where(RbacUser.user_id == user_id)
            )
            return result.rowcount > 0
    
    async def _assign_roles_to_user(
        self, 
        db: AsyncSession, 
        user_id: str, 
        role_ids: List[int],
        create_by: str = 'system'
    ):
        """为用户分配角色"""
        for role_id in role_ids:
            user_role = RbacUsersRoles(
                user_id=user_id,
                role_id=role_id,
                create_by=create_by,
                update_by=create_by,
                create_time=now_shanghai(),
                update_time=now_shanghai()
            )
            db.add(user_role)
    
    async def _update_user_roles(
        self, 
        db: AsyncSession, 
        user_id: str, 
        role_ids: List[int],
        update_by: str = 'system'
    ):
        """更新用户角色关联"""
        # 删除现有关联
        await db.execute(
            delete(RbacUsersRoles).where(RbacUsersRoles.user_id == user_id)
        )
        
        # 添加新关联
        for role_id in role_ids:
            user_role = RbacUsersRoles(
                user_id=user_id,
                role_id=role_id,
                create_by=update_by,
                update_by=update_by,
                create_time=now_shanghai(),
                update_time=now_shanghai()
            )
            db.add(user_role)


class RbacRoleService:
    """角色管理服务"""
    
    async def create_role(
        self, 
        db: AsyncSession, 
        role_data: RoleCreateRequest,
        create_by: str = 'system'
    ) -> RbacRole:
        """创建角色"""
        async with db.begin():
            # 如果没有提供 role_id，自动生成
            if role_data.role_id is None:
                # 获取当前最大的 role_id
                result = await db.execute(
                    select(func.max(RbacRole.role_id))
                )
                max_role_id = result.scalar() or 0
                role_data.role_id = max_role_id + 1
            else:
                # 检查角色是否存在
                result = await db.execute(
                    select(RbacRole).where(RbacRole.role_id == role_data.role_id)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    raise BusinessException("角色ID已存在", ResponseCode.CONFLICT)
            
            # 创建角色
            data = role_data.dict(exclude={'permission_ids', 'menu_ids'})
            data['create_by'] = create_by
            data['update_by'] = create_by
            data['create_time'] = now_shanghai()
            data['update_time'] = now_shanghai()
            
            logger.info(f"Creating role: {role_data.role_id}")
            role = RbacRole(**data)
            db.add(role)
            await db.flush()
            
            # 分配权限（API权限和菜单权限）
            if role_data.permission_ids or role_data.menu_ids:
                await self._update_role_permissions(
                    db, 
                    role_data.role_id, 
                    role_data.permission_ids or [], 
                    role_data.menu_ids or [],
                    create_by
                )
            
            await db.refresh(role)
            return role
    
    async def get_role_by_id(
        self, 
        db: AsyncSession, 
        role_id: int
    ) -> Optional[RbacRole]:
        """根据角色ID获取角色"""
        result = await db.execute(
            select(RbacRole).where(RbacRole.role_id == role_id)
        )
        return result.scalar_one_or_none()
    
    async def list_roles(
        self, 
        db: AsyncSession, 
        params: RoleQueryParams
    ) -> Tuple[List[RbacRole], int]:
        """角色列表查询"""
        # 构建查询条件
        query = select(RbacRole)
        conditions = []
        
        if params.search:
            conditions.append(
                RbacRole.role_name.contains(params.search) |
                RbacRole.description.contains(params.search)
            )
        if params.role_id is not None:
            conditions.append(RbacRole.role_id == params.role_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 分页查询
        query = query.order_by(RbacRole.create_time.desc())
        query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
        result = await db.execute(query)
        roles = list(result.scalars().all())
        
        # 为每个角色计算统计信息
        for role in roles:
            # 计算权限数量 - 使用与get_role_permissions_and_menus相同的逻辑
            role_perms_result = await db.execute(
                select(RbacRolesPermissions).where(RbacRolesPermissions.role_id == role.role_id)
            )
            role_permissions = list(role_perms_result.scalars().all())
            
            # 计算API权限数量
            permission_count = sum(1 for rp in role_permissions 
                                 if rp.permission_type == 2 and rp.back_permission_id != -1)
            
            # 计算用户数量
            user_count_result = await db.execute(
                select(func.count(RbacUsersRoles.id))
                .where(RbacUsersRoles.role_id == role.role_id)
            )
            user_count = user_count_result.scalar() or 0
            
            # 动态添加统计属性
            role.permission_count = permission_count
            role.user_count = user_count
        
        # 计算总数
        count_query = select(func.count(RbacRole.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return roles, total
    
    async def update_role(
        self, 
        db: AsyncSession, 
        role_id: int, 
        role_data: RoleUpdateRequest,
        update_by: str = 'system'
    ) -> Optional[RbacRole]:
        """更新角色"""
        async with db.begin():
            # 检查角色是否存在
            result = await db.execute(
                select(RbacRole).where(RbacRole.role_id == role_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                raise BusinessException("角色不存在", ResponseCode.NOT_FOUND)
            
            # 更新数据
            data = role_data.dict(exclude_unset=True, exclude={'permission_ids', 'menu_ids'})
            data['update_by'] = update_by
            data['update_time'] = now_shanghai()
            
            logger.info(f"Updating role: {role_id}")
            await db.execute(
                update(RbacRole).where(RbacRole.role_id == role_id).values(**data)
            )
            
            # 更新权限关联（API权限和菜单权限）
            if role_data.permission_ids is not None or role_data.menu_ids is not None:
                await self._update_role_permissions(
                    db, 
                    role_id, 
                    role_data.permission_ids or [], 
                    role_data.menu_ids or [],
                    update_by
                )
            
            # 返回更新后的数据
            result = await db.execute(
                select(RbacRole).where(RbacRole.role_id == role_id)
            )
            return result.scalar_one_or_none()
    
    async def delete_role(
        self, 
        db: AsyncSession, 
        role_id: int
    ) -> bool:
        """删除角色"""
        async with db.begin():
            # 先删除关联关系
            await db.execute(
                delete(RbacUsersRoles).where(RbacUsersRoles.role_id == role_id)
            )
            await db.execute(
                delete(RbacRolesPermissions).where(RbacRolesPermissions.role_id == role_id)
            )
            
            # 删除角色
            result = await db.execute(
                delete(RbacRole).where(RbacRole.role_id == role_id)
            )
            return result.rowcount > 0
    
    async def _assign_permissions_to_role(
        self, 
        db: AsyncSession, 
        role_id: int, 
        permission_ids: List[int],
        create_by: str = 'system'
    ):
        """为角色分配权限"""
        for permission_id in permission_ids:
            role_permission = RbacRolesPermissions(
                role_id=role_id,
                back_permission_id=permission_id,
                front_permission_id=permission_id,
                permission_type=1,
                create_by=create_by,
                update_by=create_by,
                create_time=now_shanghai(),
                update_time=now_shanghai()
            )
            db.add(role_permission)
    
    async def _update_role_permissions(
        self, 
        db: AsyncSession, 
        role_id: int, 
        permission_ids: List[int],
        menu_ids: List[int] = None,
        update_by: str = 'system'
    ):
        """更新角色权限关联 - 同时处理API权限和菜单权限"""
        # 删除现有关联
        await db.execute(
            delete(RbacRolesPermissions).where(RbacRolesPermissions.role_id == role_id)
        )
        
        # 添加后端API权限关联
        for permission_id in permission_ids:
            role_permission = RbacRolesPermissions(
                role_id=role_id,
                back_permission_id=permission_id,
                front_permission_id=-1,  # API权限不关联前端
                permission_type=2,  # 2表示API权限
                create_by=update_by,
                update_by=update_by,
                create_time=now_shanghai(),
                update_time=now_shanghai()
            )
            db.add(role_permission)
        
        # 添加前端菜单权限关联
        if menu_ids:
            for menu_id in menu_ids:
                role_permission = RbacRolesPermissions(
                    role_id=role_id,
                    back_permission_id=-1,  # 菜单权限不关联后端
                    front_permission_id=menu_id,
                    permission_type=1,  # 1表示菜单权限
                    create_by=update_by,
                    update_by=update_by,
                    create_time=now_shanghai(),
                    update_time=now_shanghai()
                )
                db.add(role_permission)
    
    async def get_role_permissions_and_menus(
        self, 
        db: AsyncSession, 
        role_id: int
    ) -> dict:
        """获取角色关联的权限和菜单"""
        # 获取角色的权限关联
        result = await db.execute(
            select(RbacRolesPermissions).where(RbacRolesPermissions.role_id == role_id)
        )
        role_permissions = list(result.scalars().all())
        
        # 分离API权限和菜单权限
        api_permission_ids = []
        menu_ids = []
        
        for rp in role_permissions:
            if rp.permission_type == 2 and rp.back_permission_id != -1:  # API权限
                api_permission_ids.append(rp.back_permission_id)
            elif rp.permission_type == 1 and rp.front_permission_id != -1:  # 菜单权限
                menu_ids.append(rp.front_permission_id)
        
        return {
            'api_permission_ids': api_permission_ids,
            'menu_ids': menu_ids
        }


class RbacPermissionService:
    """权限管理服务"""
    
    async def create_permission(
        self, 
        db: AsyncSession, 
        permission_data: PermissionCreateRequest,
        create_by: str = 'system'
    ) -> RbacPermission:
        """创建权限"""
        async with db.begin():
            # 检查权限是否存在
            result = await db.execute(
                select(RbacPermission).where(
                    or_(
                        RbacPermission.permission_id == permission_data.permission_id,
                        RbacPermission.permission_name == permission_data.permission_name
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise BusinessException("权限ID或权限名称已存在", ResponseCode.CONFLICT)
            
            # 创建权限
            data = permission_data.dict()
            data['create_by'] = create_by
            data['update_by'] = create_by
            data['create_time'] = now_shanghai()
            data['update_time'] = now_shanghai()
            
            logger.info(f"Creating permission: {permission_data.permission_id}")
            permission = RbacPermission(**data)
            db.add(permission)
            await db.flush()
            await db.refresh(permission)
            return permission
    
    async def get_permission_by_id(
        self, 
        db: AsyncSession, 
        permission_id: int
    ) -> Optional[RbacPermission]:
        """根据权限ID获取权限"""
        result = await db.execute(
            select(RbacPermission).where(RbacPermission.permission_id == permission_id)
        )
        return result.scalar_one_or_none()
    
    async def list_permissions(
        self, 
        db: AsyncSession, 
        params: PermissionQueryParams
    ) -> Tuple[List[RbacPermission], int]:
        """权限列表查询 - 显示所有权限（包括已删除的）"""
        # 构建查询条件
        query = select(RbacPermission)
        conditions = []
        
        if params.search:
            conditions.append(
                RbacPermission.permission_name.contains(params.search) |
                RbacPermission.permission_description.contains(params.search)
            )
        if params.permission_id is not None:
            conditions.append(RbacPermission.permission_id == params.permission_id)
        if params.release_disable:
            conditions.append(RbacPermission.release_disable == params.release_disable)
        if params.http_method:
            conditions.append(RbacPermission.http_method == params.http_method)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 分页查询
        query = query.order_by(RbacPermission.create_time.desc())
        query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
        result = await db.execute(query)
        permissions = list(result.scalars().all())
        
        # 计算总数
        count_query = select(func.count(RbacPermission.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return permissions, total
    
    async def update_permission(
        self, 
        db: AsyncSession, 
        permission_id: int, 
        permission_data: PermissionUpdateRequest,
        update_by: str = 'system'
    ) -> Optional[RbacPermission]:
        """更新权限"""
        async with db.begin():
            # 检查权限是否存在
            result = await db.execute(
                select(RbacPermission).where(RbacPermission.permission_id == permission_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                raise BusinessException("权限不存在", ResponseCode.NOT_FOUND)
            
            # 更新数据
            data = permission_data.dict(exclude_unset=True)
            data['update_by'] = update_by
            data['update_time'] = now_shanghai()
            
            logger.info(f"Updating permission: {permission_id}")
            await db.execute(
                update(RbacPermission).where(RbacPermission.permission_id == permission_id).values(**data)
            )
            
            # 返回更新后的数据
            result = await db.execute(
                select(RbacPermission).where(RbacPermission.permission_id == permission_id)
            )
            return result.scalar_one_or_none()
    
    async def delete_permission(
        self, 
        db: AsyncSession, 
        permission_id: int,
        delete_by: str = 'system'
    ) -> bool:
        """逻辑删除权限"""
        async with db.begin():
            # 检查权限是否存在且未删除
            result = await db.execute(
                select(RbacPermission).where(
                    and_(
                        RbacPermission.permission_id == permission_id,
                        RbacPermission.is_deleted == 0
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                return False
            
            # 逻辑删除权限（设置is_deleted=1）
            await db.execute(
                update(RbacPermission)
                .where(RbacPermission.permission_id == permission_id)
                .values(
                    is_deleted=1,
                    update_by=delete_by,
                    update_time=now_shanghai()
                )
            )
            return True


class RbacMenuService:
    """菜单管理服务"""
    
    async def create_menu(
        self, 
        db: AsyncSession, 
        menu_data: MenuCreateRequest,
        create_by: str = 'system'
    ) -> RbacMenu:
        """创建菜单"""
        async with db.begin():
            # 检查菜单是否存在
            result = await db.execute(
                select(RbacMenu).where(RbacMenu.menu_id == menu_data.menu_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise BusinessException("菜单ID已存在", ResponseCode.CONFLICT)
            
            # 创建菜单
            data = menu_data.dict()
            data['create_by'] = create_by
            data['update_by'] = create_by
            data['create_time'] = now_shanghai()
            data['update_time'] = now_shanghai()
            
            logger.info(f"Creating menu: {menu_data.menu_id}")
            menu = RbacMenu(**data)
            db.add(menu)
            await db.flush()
            await db.refresh(menu)
            return menu
    
    async def get_menu_by_id(
        self, 
        db: AsyncSession, 
        menu_id: int
    ) -> Optional[RbacMenu]:
        """根据菜单ID获取菜单"""
        result = await db.execute(
            select(RbacMenu).where(RbacMenu.menu_id == menu_id)
        )
        return result.scalar_one_or_none()
    
    async def list_menus(
        self, 
        db: AsyncSession, 
        params: MenuQueryParams
    ) -> Tuple[List[RbacMenu], int]:
        """菜单列表查询"""
        # 构建查询条件
        query = select(RbacMenu)
        conditions = []
        
        if params.search:
            conditions.append(RbacMenu.menu_name.contains(params.search))
        if params.parent_id is not None:
            conditions.append(RbacMenu.parent_id == params.parent_id)
        if params.show_menu is not None:
            conditions.append(RbacMenu.show_menu == params.show_menu)
        if params.menu_id is not None:
            conditions.append(RbacMenu.menu_id == params.menu_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 分页查询
        query = query.order_by(RbacMenu.create_time.desc())
        query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
        result = await db.execute(query)
        menus = list(result.scalars().all())
        
        # 计算总数
        count_query = select(func.count(RbacMenu.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return menus, total
    
    async def update_menu(
        self, 
        db: AsyncSession, 
        menu_id: int, 
        menu_data: MenuUpdateRequest,
        update_by: str = 'system'
    ) -> Optional[RbacMenu]:
        """更新菜单"""
        async with db.begin():
            # 检查菜单是否存在
            result = await db.execute(
                select(RbacMenu).where(RbacMenu.menu_id == menu_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                raise BusinessException("菜单不存在", ResponseCode.NOT_FOUND)
            
            # 更新数据
            data = menu_data.dict(exclude_unset=True)
            data['update_by'] = update_by
            data['update_time'] = now_shanghai()
            
            logger.info(f"Updating menu: {menu_id}")
            await db.execute(
                update(RbacMenu).where(RbacMenu.menu_id == menu_id).values(**data)
            )
            
            # 返回更新后的数据
            result = await db.execute(
                select(RbacMenu).where(RbacMenu.menu_id == menu_id)
            )
            return result.scalar_one_or_none()
    
    async def delete_menu(
        self, 
        db: AsyncSession, 
        menu_id: int
    ) -> bool:
        """删除菜单"""
        async with db.begin():
            result = await db.execute(
                delete(RbacMenu).where(RbacMenu.menu_id == menu_id)
            )
            return result.rowcount > 0


# 全局服务实例
rbac_user_service = RbacUserService()
rbac_role_service = RbacRoleService()
rbac_permission_service = RbacPermissionService()
rbac_menu_service = RbacMenuService()