/**
 * SOP模块统一入口
 * 
 * 模块结构:
 * - pages/: 页面级组件
 * - components/: 可复用组件  
 * - hooks/: 模块专用hooks
 * - services/: API服务
 * - types/: 类型定义
 */

// === 页面组件 ===
export { default as SOPList } from './pages/SOPList';
export { default as SOPManagement } from './pages/SOPManagement';
export { default as SOPProblemRuleManagement } from './pages/SOPProblemRuleManagement';

// === 可复用组件 ===
export { default as SOPFormWithTreeModal } from './components/SOPFormWithTreeModal';
export { default as SOPDetailModal } from './components/SOPDetailModal';
export { default as FaultTreeEditor } from './components/FaultTreeEditor';

// === Hooks ===
export { useSOPList } from './hooks/useSOPList';

// === 服务 ===
export { SOPApi, SOPUtils } from '@/services/sopApi';

// === 类型定义 ===
export * from './types/sop';
export * from './types/sopProblemRule';

