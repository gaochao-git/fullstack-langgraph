/**
 * 记忆管理 API 服务
 */

import { omind_get, omind_post, omind_put, omind_del } from '../utils/base_api';

// 记忆数据类型定义
export interface Memory {
  id: string;
  content: string;
  score?: number;
  metadata: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
  memory_type?: string;  // 添加记忆类型属性
  namespace_label?: string;  // 添加命名空间标签属性
}

export interface MemoryCreate {
  namespace: string;
  content: string;
  metadata?: Record<string, any>;
  namespace_params: Record<string, string>;
}

export interface MemorySearch {
  namespace: string;
  query: string;
  limit?: number;
  namespace_params: Record<string, string>;
}

export interface MemoryUpdate {
  namespace: string;
  memory_id: string;
  content: string;
  namespace_params: Record<string, string>;
}

export interface MemoryStats {
  current_user: string;
  user_memory_count: {
    profile: number;
    expertise: number;
    preferences: number;
  };
  status: string;
}

export interface UserProfileMemories {
  profile: Memory[];
  expertise: Memory[];
  preferences: Memory[];
  user_id: string;
}

export interface NamespaceInfo {
  user: Record<string, string>;
  architecture: Record<string, string>;
  business: Record<string, string>;
  operations: Record<string, string>;
}

export interface SystemArchitectureCreate {
  system_id: string;
  architecture_info: Record<string, any>;
}

export interface IncidentCreate {
  system_id: string;
  incident: Record<string, any>;
}

export interface UserPreferenceCreate {
  user_id?: string;
  preference: Record<string, any>;
}

export interface DiagnosisContext {
  system_context: Memory[];
  similar_incidents: Memory[];
  solution_patterns: Memory[];
  user_preferences: Memory[];
  current_issue: string;
  timestamp: string;
}

/**
 * 记忆管理 API
 */
export const memoryApi = {
  // 删除手动添加记忆 - 应通过 AI 对话自动学习

  /**
   * 搜索记忆
   */
  async searchMemories(data: MemorySearch) {
    return omind_post('/api/v1/memory/search', data);
  },

  // 删除手动更新/删除记忆 - Mem0 应通过对话自动管理

  // 删除记忆管理接口 - 改用数据库直接管理用户档案

  /**
   * 检索指定命名空间的记忆（用于AI诊断）
   */
  async searchMemoriesByNamespace(namespaceType: string, query: string, params?: { user_name?: string; system_id?: string; limit?: number }) {
    const queryParams = new URLSearchParams();
    queryParams.append('query', query);
    if (params?.user_name) queryParams.append('user_name', params.user_name);
    if (params?.system_id) queryParams.append('system_id', params.system_id);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    const queryString = queryParams.toString();
    return omind_get(`/api/v1/memory/search/${namespaceType}?${queryString}`);
  },

  /**
   * 获取所有可用的命名空间
   */
  async getNamespaces() {
    return omind_get('/api/v1/memory/namespaces');
  },

  /**
   * 获取记忆统计信息
   */
  async getMemoryStats() {
    return omind_get('/api/v1/memory/stats');
  },

  /**
   * 获取当前用户的个人档案记忆
   */
  async getUserProfileMemories() {
    return omind_get('/api/v1/memory/user/profile');
  },

  /**
   * 批量创建记忆
   */
  async batchCreateMemories(memories: MemoryCreate[]) {
    return omind_post('/api/v1/memory/batch', memories);
  },

  /**
   * 存储系统架构信息
   */
  async storeSystemArchitecture(data: SystemArchitectureCreate) {
    return omind_post('/api/v1/memory/system-architecture', data);
  },

  /**
   * 存储故障案例
   */
  async storeIncident(data: IncidentCreate) {
    return omind_post('/api/v1/memory/incident', data);
  },

  /**
   * 存储用户偏好
   */
  async storeUserPreference(data: UserPreferenceCreate) {
    return omind_post('/api/v1/memory/user-preference', data);
  },

  /**
   * 获取诊断上下文
   */
  async getDiagnosisContext(issue: string, systemId: string, userId?: string) {
    const params = new URLSearchParams();
    params.append('issue', issue);
    params.append('system_id', systemId);
    if (userId) params.append('user_id', userId);
    return omind_get(`/api/v1/memory/diagnosis-context?${params.toString()}`);
  }
};

export default memoryApi;