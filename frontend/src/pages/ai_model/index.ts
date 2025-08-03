/**
 * AI Model模块统一入口
 * 
 * 模块结构:
 * - pages/: 页面级组件
 * - services/: API服务
 */

// === 页面组件 ===
export { default as ModelsManagement } from './pages/ModelsManagement';

// === 服务 ===
export { AIModelApi } from '../../services/aiModelApi';

// === 类型定义 (从服务中导出) ===
export type { 
  AIModel, 
  AIModelCreateRequest, 
  AIModelUpdateRequest, 
  AIModelListParams
} from '../../services/aiModelApi';

// === 默认导出 ===
export { default } from './pages/ModelsManagement';