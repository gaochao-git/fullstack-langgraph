/**
 * MCP模块统一入口
 * 
 * 模块结构:
 * - pages/: 页面级组件
 * - services/: API服务
 */

// === 页面组件 ===
export { default as MCPManagement } from './pages/MCPManagement';

// === 服务 ===
export { MCPApi } from '../../services/mcpApi';

// === 类型定义 (从服务中导出) ===
export type { 
  MCPServer, 
  MCPServerCreateRequest, 
  MCPServerUpdateRequest, 
  MCPListParams,
  MCPTestRequest,
  MCPTestResponse
} from '../../services/mcpApi';

