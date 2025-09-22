# IDC运行报告选项卡实施指南

## 概述

本文档详细说明如何在当前项目中添加"IDC运行报告"选项卡。该项目使用动态菜单系统，通过数据库配置菜单项，前端根据后端返回的菜单数据自动生成路由和导航。

## 已完成的工作

### 1. 前端组件创建
- ✅ 创建了 `IDCReportManagement.tsx` 主页面组件
- ✅ 创建了 `pages/idc_research/index.ts` 模块导出文件
- ✅ 更新了 `componentRegistry.ts` 注册新组件
- ✅ 创建了 `idcReportApi.ts` API服务文件

### 2. 数据库脚本准备
- ✅ 创建了 `add_idc_report_menu.sql` 菜单添加脚本
- ✅ 创建了 `assign_idc_report_permission.sql` 权限分配脚本

### 3. 后端模块初始化
- ✅ 更新了 `backend/src/apps/idc_research/` 模块文档

## 下一步操作

### 第一步：执行数据库脚本

1. **连接到您的数据库**（MySQL/PostgreSQL）

2. **查询当前最大菜单ID**：
   ```sql
   SELECT MAX(menu_id) FROM rbac_menus;
   ```

3. **执行菜单添加脚本**：
   - 打开 `backend/migrations/add_idc_report_menu.sql`
   - 根据步骤2的结果修改脚本中的 `menu_id` 值（如果当前最大值是48，则使用49）
   - 执行该脚本

4. **分配菜单权限**：
   - 查询当前角色：`SELECT role_id, role_name FROM rbac_roles;`
   - 打开 `backend/migrations/assign_idc_report_permission.sql`
   - 修改脚本中的 `role_id` 为您想要分配权限的角色ID
   - 执行该脚本

### 第二步：验证前端显示

1. **启动开发环境**：
   ```bash
   # 在项目根目录
   make dev
   ```

2. **检查菜单显示**：
   - 登录系统
   - 检查左侧导航菜单是否出现"IDC运行报告"选项卡
   - 点击菜单项验证页面是否正常加载

### 第三步：功能完善（可选）

如果您需要实际的后端API支持，可以：

1. **创建后端API**：
   - 在 `backend/src/apps/idc_research/` 中添加实际的API端点
   - 实现报告生成、查询、下载等功能

2. **数据库表设计**：
   ```sql
   -- 创建IDC报告表
   CREATE TABLE idc_reports (
       id BIGINT PRIMARY KEY AUTO_INCREMENT,
       report_name VARCHAR(200) NOT NULL,
       idc_location VARCHAR(100) NOT NULL,
       report_type VARCHAR(50) NOT NULL,
       generate_time DATETIME NOT NULL,
       status VARCHAR(20) NOT NULL DEFAULT 'pending',
       power_usage DECIMAL(10,2),
       energy_efficiency DECIMAL(4,2),
       availability_rate DECIMAL(5,2),
       alert_count INT DEFAULT 0,
       file_path VARCHAR(500),
       file_size VARCHAR(20),
       create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
       update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
   );
   ```

3. **更新前端API调用**：
   - 修改 `IDCReportManagement.tsx` 中的模拟数据调用
   - 使用实际的 `idcReportApi` 服务

## 项目架构说明

### 菜单系统工作原理

1. **数据库存储**：菜单信息存储在 `rbac_menus` 表中
2. **后端API**：`/api/v1/auth/me/menus` 返回用户有权限的菜单树
3. **前端处理**：
   - `useMenus` Hook 获取菜单数据
   - `DynamicRouter` 根据菜单数据生成路由
   - `componentRegistry` 将组件名映射到实际组件
   - `MenuLayout` 渲染导航菜单

### 权限控制

1. **菜单权限**：通过 `rbac_roles_permissions` 表控制用户能看到哪些菜单
2. **API权限**：可以进一步控制用户能调用哪些API接口
3. **用户角色**：通过 `rbac_users_roles` 表关联用户和角色

## 常见问题排查

### 菜单不显示
1. 检查数据库中菜单记录的 `show_menu` 字段是否为 1
2. 确认用户角色是否有该菜单的权限
3. 检查 `componentRegistry.ts` 中是否正确注册了组件

### 页面无法加载
1. 检查组件导入路径是否正确
2. 确认组件文件是否存在语法错误
3. 查看浏览器控制台是否有错误信息

### 路由不匹配
1. 确认菜单的 `route_path` 字段值正确
2. 检查是否与现有路由冲突

## 扩展建议

### 1. 图标优化
可以在 `frontend/src/icons/` 中添加专门的IDC相关图标。

### 2. 主题适配
确保新页面在明暗主题下都能正常显示。

### 3. 移动端适配
考虑在移动设备上的显示效果和交互体验。

### 4. 国际化
如果项目支持多语言，添加相应的翻译文件。

## 总结

通过以上步骤，您就可以成功添加"IDC运行报告"选项卡。该实现方案完全符合项目的现有架构，利用了动态菜单系统的优势，后续维护和扩展都会很方便。