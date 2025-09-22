-- IDC报告菜单问题一键修复脚本
-- 此脚本会检查并修复所有可能导致菜单不显示的问题

SELECT '========== IDC报告菜单问题诊断开始 ==========' as status;

-- 1. 检查菜单记录是否存在且配置正确
SELECT '1. 检查菜单记录...' as step;
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN '❌ ERROR: 菜单记录不存在!'
        WHEN MAX(show_menu) = 0 THEN '❌ ERROR: 菜单被隐藏 (show_menu=0)!'
        WHEN MAX(CHAR_LENGTH(TRIM(menu_component))) = 0 THEN '❌ ERROR: 组件名为空!'
        WHEN MAX(CHAR_LENGTH(TRIM(route_path))) = 0 THEN '❌ ERROR: 路由路径为空!'
        ELSE '✅ 菜单记录配置正确'
    END as menu_status,
    COUNT(*) as record_count,
    MAX(menu_name) as menu_name,
    MAX(route_path) as route_path,
    MAX(menu_component) as component_name,
    MAX(show_menu) as show_menu_value
FROM rbac_menus 
WHERE menu_id = 25;

-- 2. 如果菜单不存在，创建它
INSERT INTO rbac_menus (
    menu_id,
    menu_name,
    menu_icon,
    parent_id,
    route_path,
    redirect_path,
    menu_component,
    show_menu,
    sort_order,
    create_by,
    update_by,
    create_time,
    update_time
)
SELECT 
    25,
    'IDC运行报告',
    'file-text',
    -1,
    '/idc/reports',
    '',
    'IDCReportManagement',
    1,
    100,
    'system',
    'system',
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM rbac_menus WHERE menu_id = 25);

-- 3. 修复菜单配置（如果存在但配置错误）
UPDATE rbac_menus 
SET 
    show_menu = 1,
    menu_component = 'IDCReportManagement',
    route_path = '/idc/reports',
    menu_name = 'IDC运行报告',
    update_time = NOW()
WHERE menu_id = 25 
AND (show_menu != 1 OR menu_component != 'IDCReportManagement' OR route_path != '/idc/reports');

SELECT '2. 菜单记录修复完成' as step;

-- 4. 检查角色权限
SELECT '3. 检查角色权限...' as step;
SELECT 
    r.role_id,
    r.role_name,
    CASE 
        WHEN rp.role_id IS NULL THEN '❌ 缺少权限'
        ELSE '✅ 已有权限'
    END as permission_status
FROM rbac_roles r
LEFT JOIN rbac_roles_permissions rp ON (
    r.role_id = rp.role_id 
    AND rp.front_permission_id = 25 
    AND rp.permission_type = 1
)
ORDER BY r.role_id;

-- 5. 为所有角色分配权限（如果缺少）
INSERT INTO rbac_roles_permissions (
    role_id,
    front_permission_id,
    back_permission_id,
    permission_type,
    create_by,
    update_by,
    create_time,
    update_time
)
SELECT 
    r.role_id,
    25,
    -1,
    1,
    'system',
    'system',
    NOW(),
    NOW()
FROM rbac_roles r
WHERE NOT EXISTS (
    SELECT 1 FROM rbac_roles_permissions rp 
    WHERE rp.role_id = r.role_id 
    AND rp.front_permission_id = 25 
    AND rp.permission_type = 1
);

SELECT '4. 权限分配完成' as step;

-- 6. 最终验证
SELECT '5. 最终验证结果...' as step;

-- 验证菜单记录
SELECT 
    '✅ 菜单记录验证' as check_type,
    menu_id,
    menu_name,
    route_path,
    menu_component,
    show_menu,
    parent_id
FROM rbac_menus 
WHERE menu_id = 25;

-- 验证权限分配
SELECT 
    '✅ 权限分配验证' as check_type,
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

-- 检查用户角色关联
SELECT 
    '✅ 用户角色关联检查' as check_type,
    u.user_id,
    u.username,
    r.role_id,
    r.role_name,
    CASE 
        WHEN rp.role_id IS NOT NULL THEN '✅ 有权限'
        ELSE '❌ 无权限'
    END as has_permission
FROM rbac_users u
JOIN rbac_users_roles ur ON u.user_id = ur.user_id
JOIN rbac_roles r ON ur.role_id = r.role_id
LEFT JOIN rbac_roles_permissions rp ON (
    r.role_id = rp.role_id 
    AND rp.front_permission_id = 25 
    AND rp.permission_type = 1
)
ORDER BY u.user_id;

SELECT '========== IDC报告菜单问题修复完成 ==========' as status;

-- 重要提示
SELECT '⚠️ 重要提示:' as notice, '修复完成后请重启后端服务，清除前端浏览器缓存，然后重新登录测试!' as action;