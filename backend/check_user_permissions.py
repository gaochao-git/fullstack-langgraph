#!/usr/bin/env python3
"""
检查用户的角色和权限分配情况
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db_context
from src.apps.user.models import RbacUser, RbacUsersRoles, RbacRole, RbacRolesPermissions, RbacMenu
from src.apps.auth.service.menu_service import menu_service


async def check_user_permissions(username: str):
    """检查指定用户的权限情况"""
    async with get_async_db_context() as db:
        # 1. 查找用户
        user_stmt = select(RbacUser).where(RbacUser.user_name == username)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"❌ 用户 {username} 不存在")
            return
        
        print(f"\n👤 用户信息:")
        print(f"  - ID: {user.user_id}")
        print(f"  - 用户名: {user.user_name}")
        print(f"  - 显示名: {user.display_name}")
        print(f"  - 状态: {'激活' if user.is_active else '禁用'}")
        
        # 2. 查找用户角色
        roles_stmt = select(RbacRole).join(
            RbacUsersRoles, RbacUsersRoles.role_id == RbacRole.role_id
        ).where(RbacUsersRoles.user_id == user.user_id)
        
        roles_result = await db.execute(roles_stmt)
        roles = list(roles_result.scalars().all())
        
        print(f"\n👥 用户角色 ({len(roles)} 个):")
        if roles:
            for role in roles:
                print(f"  - {role.role_name} (ID: {role.role_id}, Code: {role.role_code})")
                
                # 检查角色的菜单权限
                menu_perms_stmt = select(RbacRolesPermissions).where(
                    RbacRolesPermissions.role_id == role.role_id,
                    RbacRolesPermissions.permission_type == 1  # 菜单权限
                )
                menu_perms_result = await db.execute(menu_perms_stmt)
                menu_perms = list(menu_perms_result.scalars().all())
                
                print(f"    菜单权限 ({len(menu_perms)} 个):")
                for perm in menu_perms:
                    if perm.front_permission_id != -1:
                        # 查找对应的菜单
                        menu_stmt = select(RbacMenu).where(RbacMenu.menu_id == perm.front_permission_id)
                        menu_result = await db.execute(menu_stmt)
                        menu = menu_result.scalar_one_or_none()
                        if menu:
                            print(f"      - {menu.menu_name} (ID: {menu.menu_id})")
        else:
            print("  ⚠️  用户没有分配任何角色")
        
        # 3. 测试菜单服务
        print(f"\n📋 通过菜单服务获取用户菜单:")
        user_menus = await menu_service.get_user_menus(db, user.user_id)
        print(f"  菜单数量: {len(user_menus)}")
        
        def print_menu_tree(menus, level=0):
            for menu in menus:
                indent = "  " * (level + 1)
                print(f"{indent}- {menu['menu_name']} ({menu['route_path']})")
                if menu.get('children'):
                    print_menu_tree(menu['children'], level + 1)
        
        if user_menus:
            print_menu_tree(user_menus)
        else:
            print("  ⚠️  没有可访问的菜单")
        
        # 4. 检查系统中的菜单总数
        all_menus_stmt = select(RbacMenu)
        all_menus_result = await db.execute(all_menus_stmt)
        all_menus = list(all_menus_result.scalars().all())
        
        print(f"\n📊 系统菜单统计:")
        print(f"  总菜单数: {len(all_menus)}")
        print(f"  根菜单:")
        for menu in all_menus:
            if menu.parent_id == -1:
                print(f"    - {menu.menu_name} (ID: {menu.menu_id})")


async def create_test_permissions():
    """创建测试权限数据"""
    async with get_async_db_context() as db:
        async with db.begin():
            # 检查是否有admin角色
            admin_role_stmt = select(RbacRole).where(RbacRole.role_code == 'admin')
            admin_role_result = await db.execute(admin_role_stmt)
            admin_role = admin_role_result.scalar_one_or_none()
            
            if not admin_role:
                print("❌ admin角色不存在，请先创建角色")
                return
            
            # 获取所有菜单
            menus_stmt = select(RbacMenu)
            menus_result = await db.execute(menus_stmt)
            menus = list(menus_result.scalars().all())
            
            if not menus:
                print("❌ 系统中没有菜单，请先创建菜单")
                return
            
            print(f"\n✅ 为admin角色分配所有菜单权限...")
            
            # 为admin角色分配所有菜单权限
            for menu in menus:
                # 检查是否已存在
                existing_stmt = select(RbacRolesPermissions).where(
                    RbacRolesPermissions.role_id == admin_role.role_id,
                    RbacRolesPermissions.front_permission_id == menu.menu_id,
                    RbacRolesPermissions.permission_type == 1
                )
                existing_result = await db.execute(existing_stmt)
                existing = existing_result.scalar_one_or_none()
                
                if not existing:
                    role_perm = RbacRolesPermissions(
                        role_id=admin_role.role_id,
                        back_permission_id=-1,
                        front_permission_id=menu.menu_id,
                        permission_type=1,  # 菜单权限
                        create_by='system',
                        update_by='system'
                    )
                    db.add(role_perm)
                    print(f"  - 分配菜单: {menu.menu_name}")
            
            await db.flush()
            print("✅ 权限分配完成")


async def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("请输入要检查的用户名 (默认: gaochao): ").strip() or "gaochao"
    
    await check_user_permissions(username)
    
    # 询问是否创建测试权限
    print("\n" + "="*50)
    create = input("是否为admin角色分配所有菜单权限? (y/N): ").strip().lower()
    if create == 'y':
        await create_test_permissions()
        print("\n重新检查用户权限...")
        await check_user_permissions(username)


if __name__ == "__main__":
    asyncio.run(main())