# Frontend 开发说明

## 快速开始
1. **安装依赖**: `npm install`
2. **启动开发服务器**: `npm run dev` (端口3000，支持热更新)
3. **构建生产版本**: `npm run build`

## 技术栈
React 19 + TypeScript + Vite + Ant Design + TailwindCSS + React Router v7

## 项目结构
- `src/components/` - 公共组件(UI组件、布局、路由保护等)
- `src/hooks/` - 自定义Hooks(认证、菜单、主题等)
- `src/icons/` - 图标组件
- `src/pages/` - 页面组件，按功能模块组织(auth/user/agent/kb等，每个组件里面必须要有index.js负责导出组件)
- `src/services/` - API服务层，所有的API文件放在这里便于统一管理和互相调用
- `src/types/` - 类型定义(接口、枚举等)
- `src/utils/` - 工具函数(日期格式化、权限判断等)

## 开发要点
- API代理配置在 `vite.config.ts`，默认代理 `/api` 到后端8000端口
- 动态路由基于后端菜单配置，见 `DynamicRouter` 组件
- 认证使用JWT，通过 `useAuth` Hook管理登录状态
- 支持明暗主题切换，使用 `ThemeContext` 管理