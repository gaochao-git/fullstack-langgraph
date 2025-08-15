"""
菜单管理服务
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, distinct

from src.apps.user.models import RbacMenu, RbacUsersRoles, RbacRole, RbacRolesPermissions
from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode

logger = get_logger(__name__)


class MenuService:
    """菜单管理服务"""
    
    async def create_menu(
        self, 
        db: AsyncSession, 
        menu_data: dict,
        creator: str = "admin"
    ) -> RbacMenu:
        """创建菜单"""
        async with db.begin():
            # 检查菜单ID是否已存在
            if 'menu_id' in menu_data:
                stmt = select(RbacMenu).where(RbacMenu.menu_id == menu_data['menu_id'])
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    raise BusinessException(
                        f"菜单ID {menu_data['menu_id']} 已存在",
                        ResponseCode.CONFLICT
                    )
            
            # 生成菜单ID（如果没有提供）
            if 'menu_id' not in menu_data:
                menu_data['menu_id'] = await self._generate_menu_id(db)
            
            menu = RbacMenu(
                menu_id=menu_data['menu_id'],
                menu_name=menu_data['menu_name'],
                menu_icon=menu_data.get('menu_icon', 'default'),
                parent_id=menu_data.get('parent_id', -1),
                route_path=menu_data['route_path'],
                redirect_path=menu_data.get('redirect_path', ''),
                menu_component=menu_data['menu_component'],
                show_menu=menu_data.get('show_menu', 1),
                sort_order=menu_data.get('sort_order', 0),
                create_by=creator,
                update_by=creator
            )
            db.add(menu)
            await db.flush()
            await db.refresh(menu)
            
            logger.info(f"Created menu: {menu.menu_name} (ID: {menu.menu_id})")
            return menu
    
    async def update_menu(
        self,
        db: AsyncSession,
        menu_id: int,
        menu_data: dict,
        updater: str = "admin"
    ) -> Optional[RbacMenu]:
        """更新菜单"""
        async with db.begin():
            stmt = select(RbacMenu).where(RbacMenu.menu_id == menu_id)
            result = await db.execute(stmt)
            menu = result.scalar_one_or_none()
            
            if not menu:
                raise BusinessException(
                    f"菜单 {menu_id} 不存在",
                    ResponseCode.NOT_FOUND
                )
            
            # 更新字段
            update_data = {
                'update_by': updater,
                'update_time': now_shanghai()
            }
            
            for key, value in menu_data.items():
                if key not in ['menu_id', 'create_time', 'create_by']:
                    update_data[key] = value
            
            stmt = update(RbacMenu).where(RbacMenu.menu_id == menu_id).values(**update_data)
            await db.execute(stmt)
            
            # 返回更新后的菜单
            stmt = select(RbacMenu).where(RbacMenu.menu_id == menu_id)
            result = await db.execute(stmt)
            updated_menu = result.scalar_one_or_none()
            
            logger.info(f"Updated menu: {menu_id}")
            return updated_menu
    
    async def delete_menu(
        self,
        db: AsyncSession,
        menu_id: int
    ) -> bool:
        """删除菜单"""
        async with db.begin():
            # 检查是否有子菜单
            stmt = select(RbacMenu).where(RbacMenu.parent_id == menu_id)
            result = await db.execute(stmt)
            children = result.scalars().all()
            
            if children:
                raise BusinessException(
                    "该菜单有子菜单，请先删除子菜单",
                    ResponseCode.VALIDATION_ERROR
                )
            
            # 删除菜单
            stmt = delete(RbacMenu).where(RbacMenu.menu_id == menu_id)
            result = await db.execute(stmt)
            
            if result.rowcount == 0:
                raise BusinessException(
                    f"菜单 {menu_id} 不存在",
                    ResponseCode.NOT_FOUND
                )
            
            logger.info(f"Deleted menu: {menu_id}")
            return True
    
    async def get_menu_by_id(
        self,
        db: AsyncSession,
        menu_id: int
    ) -> Optional[RbacMenu]:
        """根据ID获取菜单"""
        stmt = select(RbacMenu).where(RbacMenu.menu_id == menu_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_menus(
        self,
        db: AsyncSession,
        show_menu_only: bool = False
    ) -> List[RbacMenu]:
        """获取所有菜单"""
        stmt = select(RbacMenu).order_by(RbacMenu.sort_order, RbacMenu.menu_id)
        
        if show_menu_only:
            stmt = stmt.where(RbacMenu.show_menu == 1)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_menu_tree(
        self, 
        db: AsyncSession,
        show_menu_only: bool = False
    ) -> List[Dict]:
        """获取菜单树"""
        menus = await self.get_all_menus(db, show_menu_only)
        
        # 构建菜单树
        menu_dict = {}
        root_menus = []
        
        # 先创建所有菜单节点
        for menu in menus:
            menu_data = {
                'id': menu.id,
                'menu_id': menu.menu_id,
                'menu_name': menu.menu_name,
                'menu_icon': menu.menu_icon,
                'parent_id': menu.parent_id,
                'route_path': menu.route_path,
                'redirect_path': menu.redirect_path,
                'menu_component': menu.menu_component,
                'show_menu': menu.show_menu,
                'sort_order': menu.sort_order,
                'create_time': menu.create_time.isoformat() if menu.create_time else None,
                'update_time': menu.update_time.isoformat() if menu.update_time else None,
                'children': []
            }
            menu_dict[menu.menu_id] = menu_data
        
        # 构建父子关系
        for menu in menus:
            if menu.parent_id == -1:
                root_menus.append(menu_dict[menu.menu_id])
            elif menu.parent_id in menu_dict:
                menu_dict[menu.parent_id]['children'].append(menu_dict[menu.menu_id])
        
        # 递归排序每一层级的菜单
        def sort_menu_level(menu_list):
            # 对当前层级按 sort_order 排序
            menu_list.sort(key=lambda x: (x.get('sort_order', 0), x.get('menu_id', 0)))
            # 递归排序子菜单
            for menu in menu_list:
                if menu.get('children'):
                    sort_menu_level(menu['children'])
        
        # 排序根菜单和所有子菜单
        sort_menu_level(root_menus)
        
        return root_menus
    
    async def get_user_menus(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[Dict]:
        """获取用户有权限的菜单树"""
        # 1. 获取用户的角色
        user_roles_stmt = select(RbacUsersRoles.role_id).where(
            RbacUsersRoles.user_id == user_id
        )
        user_roles_result = await db.execute(user_roles_stmt)
        role_ids = [row[0] for row in user_roles_result.fetchall()]
        
        if not role_ids:
            logger.warning(f"用户 {user_id} 没有分配任何角色")
            return []
        
        # 2. 检查是否是超级管理员
        admin_roles_stmt = select(RbacRole).where(
            and_(
                RbacRole.role_id.in_(role_ids),
                RbacRole.role_code.in_(['super_admin', 'admin']),
                RbacRole.is_active == 1
            )
        )
        admin_roles_result = await db.execute(admin_roles_stmt)
        is_admin = admin_roles_result.scalar_one_or_none() is not None
        
        if is_admin:
            # 超级管理员可以看到所有菜单
            logger.info(f"用户 {user_id} 是管理员，返回所有菜单")
            return await self.get_menu_tree(db, show_menu_only=True)
        
        # 3. 获取角色关联的菜单ID
        # 从 RbacRolesPermissions 表获取菜单权限
        # permission_type = 1 表示菜单权限，front_permission_id 对应菜单ID
        menu_ids_stmt = select(distinct(RbacRolesPermissions.front_permission_id)).where(
            and_(
                RbacRolesPermissions.role_id.in_(role_ids),
                RbacRolesPermissions.permission_type == 1,  # 菜单权限
                RbacRolesPermissions.front_permission_id != -1  # 有效的菜单ID
            )
        )
        menu_ids_result = await db.execute(menu_ids_stmt)
        menu_ids = [row[0] for row in menu_ids_result.fetchall()]
        
        if not menu_ids:
            logger.warning(f"用户 {user_id} 的角色没有分配任何菜单权限")
            return []
        
        logger.info(f"用户 {user_id} 有权限访问的菜单ID: {menu_ids}")
        
        # 4. 获取这些菜单及其父菜单（保证菜单树的完整性）
        # 需要获取所有祖先菜单以构建完整的树
        all_menu_ids = set(menu_ids)
        
        # 获取所有菜单信息
        all_menus_stmt = select(RbacMenu).where(
            RbacMenu.show_menu == 1  # 只获取显示的菜单
        )
        all_menus_result = await db.execute(all_menus_stmt)
        all_menus = list(all_menus_result.scalars().all())
        
        # 构建菜单字典以快速查找
        menu_dict = {menu.menu_id: menu for menu in all_menus}
        
        # 递归获取所有祖先菜单ID
        def get_ancestor_ids(menu_id: int) -> set:
            ancestors = set()
            if menu_id in menu_dict:
                menu = menu_dict[menu_id]
                if menu.parent_id != -1 and menu.parent_id in menu_dict:
                    ancestors.add(menu.parent_id)
                    ancestors.update(get_ancestor_ids(menu.parent_id))
            return ancestors
        
        # 添加所有祖先菜单ID
        for menu_id in menu_ids:
            all_menu_ids.update(get_ancestor_ids(menu_id))
        
        logger.info(f"包含祖先菜单后的完整菜单ID集合: {all_menu_ids}")
        
        # 5. 构建只包含有权限菜单的树
        return self._build_menu_tree_with_ids(all_menus, all_menu_ids)
    
    def _build_menu_tree_with_ids(self, menus: List[RbacMenu], allowed_menu_ids: set) -> List[Dict]:
        """根据允许的菜单ID构建菜单树"""
        # 筛选允许的菜单
        allowed_menus = [menu for menu in menus if menu.menu_id in allowed_menu_ids]
        
        # 构建菜单字典
        menu_dict = {}
        root_menus = []
        
        # 先创建所有菜单节点
        for menu in allowed_menus:
            menu_data = {
                'id': menu.id,
                'menu_id': menu.menu_id,
                'menu_name': menu.menu_name,
                'menu_icon': menu.menu_icon,
                'parent_id': menu.parent_id,
                'route_path': menu.route_path,
                'redirect_path': menu.redirect_path,
                'menu_component': menu.menu_component,
                'show_menu': menu.show_menu,
                'sort_order': menu.sort_order,
                'create_time': menu.create_time.isoformat() if menu.create_time else None,
                'update_time': menu.update_time.isoformat() if menu.update_time else None,
                'children': []
            }
            menu_dict[menu.menu_id] = menu_data
        
        # 构建父子关系
        for menu in allowed_menus:
            if menu.parent_id == -1:
                root_menus.append(menu_dict[menu.menu_id])
            elif menu.parent_id in menu_dict:
                menu_dict[menu.parent_id]['children'].append(menu_dict[menu.menu_id])
        
        # 递归排序每一层级的菜单
        def sort_menu_level(menu_list):
            # 对当前层级按 sort_order 排序
            menu_list.sort(key=lambda x: (x.get('sort_order', 0), x.get('menu_id', 0)))
            # 递归排序子菜单
            for menu in menu_list:
                if menu.get('children'):
                    sort_menu_level(menu['children'])
        
        # 排序根菜单和所有子菜单
        sort_menu_level(root_menus)
        
        return root_menus
    
    async def _generate_menu_id(self, db: AsyncSession) -> int:
        """生成新的菜单ID"""
        stmt = select(RbacMenu.menu_id).order_by(RbacMenu.menu_id.desc()).limit(1)
        result = await db.execute(stmt)
        max_id = result.scalar_one_or_none()
        return (max_id + 1) if max_id else 1


# 全局实例
menu_service = MenuService()