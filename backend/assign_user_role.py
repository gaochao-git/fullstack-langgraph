#!/usr/bin/env python3
"""
为用户分配角色
"""

import asyncio
from sqlalchemy import select, func
from datetime import datetime

from src.shared.db.config import get_async_db_context
from src.apps.user.models import RbacUser, RbacUsersRoles, RbacRole, RbacRolesPermissions, RbacMenu
from src.shared.db.models import now_shanghai


async def assign_admin_role_to_user(username: str):
    """为用户分配超级管理员角色"""
    async with get_async_db_context() as db:
        async with db.begin():
            # 1. 查找用户
            user_stmt = select(RbacUser).where(RbacUser.user_name == username)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                print(f"❌ 用户 {username} 不存在")
                return False
            
            print(f"✅ 找到用户: {user.user_name} (ID: {user.user_id})")
            
            # 2. 查找超级管理员角色
            admin_role_stmt = select(RbacRole).where(RbacRole.role_name == '超级管理员')
            admin_role_result = await db.execute(admin_role_stmt)
            admin_role = admin_role_result.scalar_one_or_none()
            
            if not admin_role:
                print("⚠️  超级管理员角色不存在，创建中...")
                # 获取最大的role_id
                max_id_stmt = select(func.max(RbacRole.role_id))
                max_id_result = await db.execute(max_id_stmt)
                max_id = max_id_result.scalar() or 0
                
                admin_role = RbacRole(
                    role_id=max_id + 1,
                    role_name='超级管理员',
                    description='超级管理员',
                    create_by='system',
                    update_by='system',
                    create_time=now_shanghai(),
                    update_time=now_shanghai()
                )
                db.add(admin_role)
                await db.flush()
                print("✅ 超级管理员角色创建成功")
            else:
                print(f"✅ 找到超级管理员角色 (ID: {admin_role.role_id})")
            
            # 3. 检查是否已有角色关联
            existing_stmt = select(RbacUsersRoles).where(
                RbacUsersRoles.user_id == user.user_id,
                RbacUsersRoles.role_id == admin_role.role_id
            )
            existing_result = await db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                print("ℹ️  用户已经是超级管理员")
            else:
                # 4. 创建用户角色关联
                user_role = RbacUsersRoles(
                    user_id=user.user_id,
                    role_id=admin_role.role_id,
                    create_by='system',
                    update_by='system',
                    create_time=now_shanghai(),
                    update_time=now_shanghai()
                )
                db.add(user_role)
                await db.flush()
                print("✅ 成功为用户分配超级管理员角色")
            
            # 5. 为超级管理员角色分配所有菜单权限
            print("\n📋 检查超级管理员角色的菜单权限...")
            
            # 获取所有菜单
            menus_stmt = select(RbacMenu)
            menus_result = await db.execute(menus_stmt)
            menus = list(menus_result.scalars().all())
            
            print(f"系统中共有 {len(menus)} 个菜单")
            
            # 为超级管理员角色分配所有菜单权限
            added_count = 0
            for menu in menus:
                # 检查是否已存在
                perm_existing_stmt = select(RbacRolesPermissions).where(
                    RbacRolesPermissions.role_id == admin_role.role_id,
                    RbacRolesPermissions.front_permission_id == menu.menu_id,
                    RbacRolesPermissions.permission_type == 1
                )
                perm_existing_result = await db.execute(perm_existing_stmt)
                perm_existing = perm_existing_result.scalar_one_or_none()
                
                if not perm_existing:
                    role_perm = RbacRolesPermissions(
                        role_id=admin_role.role_id,
                        back_permission_id=-1,
                        front_permission_id=menu.menu_id,
                        permission_type=1,  # 菜单权限
                        create_by='system',
                        update_by='system',
                        create_time=now_shanghai(),
                        update_time=now_shanghai()
                    )
                    db.add(role_perm)
                    added_count += 1
            
            if added_count > 0:
                await db.flush()
                print(f"✅ 为超级管理员角色新增了 {added_count} 个菜单权限")
            else:
                print("ℹ️  超级管理员角色已拥有所有菜单权限")
            
            return True


async def check_user_menus(username: str):
    """检查用户的菜单权限"""
    async with get_async_db_context() as db:
        # 查找用户
        user_stmt = select(RbacUser).where(RbacUser.user_name == username)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"❌ 用户 {username} 不存在")
            return
        
        # 使用菜单服务获取用户菜单
        from src.apps.auth.service.menu_service import menu_service
        user_menus = await menu_service.get_user_menus(db, user.user_id)
        
        print(f"\n📋 用户 {username} 的菜单权限:")
        print(f"可访问菜单数: {len(user_menus)}")
        
        def print_menu_tree(menus, level=0):
            for menu in menus:
                indent = "  " * level
                print(f"{indent}- {menu['menu_name']} ({menu['route_path']})")
                if menu.get('children'):
                    print_menu_tree(menu['children'], level + 1)
        
        if user_menus:
            print_menu_tree(user_menus)
        else:
            print("⚠️  没有可访问的菜单")


async def main():
    """主函数"""
    print("用户角色分配工具")
    print("=" * 50)
    
    username = input("请输入用户名 (默认: gaochao): ").strip() or "gaochao"
    
    success = await assign_admin_role_to_user(username)
    
    if success:
        await check_user_menus(username)
        print("\n✅ 操作完成！")
        print("现在用户应该可以看到所有菜单了。")
        print("请刷新前端页面重试。")


if __name__ == "__main__":
    asyncio.run(main())