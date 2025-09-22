-- 更新IDC运行报告菜单，将组件从IDCReportManagement改为IDCAnalysisPage
-- 此脚本将IDC运行报告的首页映射到新的分析页面

SELECT '========== 更新IDC运行报告菜单组件开始 ==========' as status;

-- 1. 检查当前菜单配置
SELECT '1. 检查当前菜单配置...' as step;
SELECT
    menu_id,
    menu_name,
    route_path,
    menu_component as current_component,
    show_menu,
    parent_id
FROM rbac_menus
WHERE menu_id = 25;

-- 2. 更新菜单组件为新的IDCAnalysisPage
UPDATE rbac_menus
SET
    menu_component = 'IDCAnalysisPage',
    menu_name = 'IDC运行状况分析',
    update_time = NOW(),
    update_by = 'system'
WHERE menu_id = 25;

SELECT '2. 菜单组件更新完成' as step;

-- 3. 验证更新结果
SELECT '3. 验证更新结果...' as step;
SELECT
    menu_id,
    menu_name,
    route_path,
    menu_component as updated_component,
    show_menu,
    parent_id,
    update_time
FROM rbac_menus
WHERE menu_id = 25;

-- 4. 检查权限是否仍然有效
SELECT '4. 检查权限配置...' as step;
SELECT
    rp.role_id,
    r.role_name,
    rp.front_permission_id,
    m.menu_name,
    m.menu_component,
    rp.permission_type
FROM rbac_roles_permissions rp
JOIN rbac_roles r ON rp.role_id = r.role_id
JOIN rbac_menus m ON rp.front_permission_id = m.menu_id
WHERE rp.front_permission_id = 25
ORDER BY rp.role_id;

SELECT '========== IDC运行报告菜单组件更新完成 ==========' as status;

-- 重要提示
SELECT '⚠️ 重要提示:' as notice, '更新完成后请刷新浏览器缓存，或重新登录以查看新的分析页面!' as action;