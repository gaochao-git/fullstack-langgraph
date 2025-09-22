-- 为角色分配IDC运行报告菜单权限
-- 这个脚本将IDC运行报告菜单权限分配给相关角色
-- 修正版本：使用正确的menu_id = 25

-- 1. 首先查看当前有哪些角色和用户
SELECT '=== 当前角色列表 ===' as info;
SELECT role_id, role_name, description FROM rbac_roles ORDER BY role_id;

SELECT '=== 当前用户及其角色 ===' as info;
SELECT u.user_id, u.username, r.role_id, r.role_name 
FROM rbac_users u
JOIN rbac_users_roles ur ON u.user_id = ur.user_id
JOIN rbac_roles r ON ur.role_id = r.role_id
ORDER BY u.user_id;

-- 2. 检查menu_id=25的菜单是否存在且配置正确
SELECT '=== IDC报告菜单配置检查 ===' as info;
SELECT menu_id, menu_name, route_path, menu_component, show_menu, parent_id 
FROM rbac_menus 
WHERE menu_id = 25;

-- 3. 为所有现有角色分配IDC报告菜单权限
-- 这样可以确保任何角色的用户都能看到该菜单
INSERT INTO rbac_roles_permissions (
    role_id,
    front_permission_id,     -- 对应菜单的menu_id
    back_permission_id,      -- 设置为-1表示仅菜单权限
    permission_type,         -- 1表示菜单权限，2表示API权限  
    create_by,
    update_by,
    create_time,
    update_time
) 
SELECT 
    r.role_id,               -- 为每个角色分配
    25,                      -- IDC报告菜单的menu_id
    -1,                      -- back_permission_id设为-1
    1,                       -- permission_type: 1表示菜单权限
    'system',                -- create_by
    'system',                -- update_by
    NOW(),                   -- create_time
    NOW()                    -- update_time
FROM rbac_roles r
WHERE NOT EXISTS (
    -- 避免重复插入
    SELECT 1 FROM rbac_roles_permissions rp 
    WHERE rp.role_id = r.role_id 
    AND rp.front_permission_id = 25 
    AND rp.permission_type = 1
);

-- 4. 验证权限分配是否成功
SELECT '=== 权限分配验证 ===' as info;
SELECT 
    rp.role_id,
    r.role_name,
    rp.front_permission_id,
    m.menu_name,
    rp.permission_type
FROM rbac_roles_permissions rp
JOIN rbac_roles r ON rp.role_id = r.role_id
JOIN rbac_menus m ON rp.front_permission_id = m.menu_id
WHERE rp.front_permission_id = 25
ORDER BY rp.role_id;