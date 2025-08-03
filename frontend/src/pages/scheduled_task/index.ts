/**
 * Scheduled Task模块统一入口
 * 
 * 模块结构:
 * - pages/: 页面级组件
 * - components/: 可复用组件
 * - services/: API服务
 */

// === 页面组件 ===
export { default as TasksManagement } from './pages/TasksManagement';

// === 可复用组件 ===
export { default as ScheduledTaskManager } from './components/ScheduledTaskManager';

// === 服务 ===
export { ScheduledTaskApi } from '../../services/scheduledTaskApi';

// === 类型定义 (从服务中导出) ===
export type { 
  ScheduledTask, 
  ScheduledTaskCreateRequest, 
  ScheduledTaskUpdateRequest, 
  ScheduledTaskListParams
} from '../../services/scheduledTaskApi';

// === 默认导出 ===
export { default } from './pages/TasksManagement';