-- 添加IDC运行报告菜单项
-- 这个脚本需要在数据库中执行以添加新的菜单项

-- 首先查询当前最大的menu_id，为新菜单分配一个唯一的ID
-- SELECT MAX(menu_id) FROM rbac_menus;

-- 假设当前最大menu_id是48，我们使用49作为新菜单的ID
-- 如果您的数据库中已有其他menu_id，请相应调整这个值

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
) VALUES (
    49,                           -- menu_id: 新菜单的唯一ID
    'IDC运行报告',                -- menu_name: 菜单显示名称
    'file-text',                  -- menu_icon: 菜单图标（Ant Design图标名）
    -1,                          -- parent_id: 父菜单ID，-1表示根菜单
    '/idc/reports',              -- route_path: 前端路由路径
    '',                          -- redirect_path: 重定向路径（可选）
    'IDCReportManagement',       -- menu_component: 对应的React组件名
    1,                           -- show_menu: 是否显示菜单（1显示，0隐藏）
    100,                         -- sort_order: 排序顺序
    'system',                    -- create_by: 创建人
    'system',                    -- update_by: 更新人
    NOW(),                       -- create_time: 创建时间
    NOW()                        -- update_time: 更新时间
);

-- 如果您希望将此菜单作为子菜单添加到某个现有的父菜单下，
-- 请修改上面的parent_id为对应的父菜单的menu_id

-- 例如，如果您想将其添加到"系统管理"菜单下，可以这样做：
-- UPDATE rbac_menus SET parent_id = (SELECT menu_id FROM rbac_menus WHERE menu_name = '系统管理' LIMIT 1) 
-- WHERE menu_id = 49;

-- 验证插入是否成功
SELECT menu_id, menu_name, route_path, menu_component, show_menu 
FROM rbac_menus 
WHERE menu_id = 49;