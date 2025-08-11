"""
菜单管理服务
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_

from src.apps.user.models import RbacMenu
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
        # TODO: 根据用户角色权限过滤菜单
        # 目前先返回所有显示的菜单
        return await self.get_menu_tree(db, show_menu_only=True)
    
    async def _generate_menu_id(self, db: AsyncSession) -> int:
        """生成新的菜单ID"""
        stmt = select(RbacMenu.menu_id).order_by(RbacMenu.menu_id.desc()).limit(1)
        result = await db.execute(stmt)
        max_id = result.scalar_one_or_none()
        return (max_id + 1) if max_id else 1


# 全局实例
menu_service = MenuService()