/**
 * 记忆管理 API 服务 - 完全符合Mem0标准
 */

import { omind_get, omind_post, omind_put, omind_del } from '../utils/base_api';

// ==================== Mem0标准数据类型 ====================

export interface Memory {
  id: string;
  memory: string;  // Mem0使用memory字段而不是content
  hash?: string;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  user_id?: string;
  agent_id?: string;
  run_id?: string;
}

export interface MemoryAddRequest {
  messages: Array<{role: string, content: string}>;
  user_id?: string;
  agent_id?: string;
  run_id?: string;
  metadata?: Record<string, any>;
  infer?: boolean;
}

export interface MemoryUpdateRequest {
  content: string;  // 只能更新内容，metadata保持不变
}

export interface MemorySearchParams {
  query: string;
  user_id?: string;
  agent_id?: string;
  run_id?: string;
  limit?: number;
  threshold?: number;
}

// ==================== Mem0标准API ====================

/**
 * 记忆管理 API - 完全符合Mem0标准
 */
export const memoryApi = {
  /**
   * 添加记忆 (Mem0: memory.add())
   */
  async addMemory(data: MemoryAddRequest) {
    return omind_post('/api/v1/memory', data);
  },

  /**
   * 获取所有记忆 (Mem0: memory.get_all())
   */
  async getAllMemories(userId?: string, agentId?: string, runId?: string, limit: number = 100) {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (agentId) params.append('agent_id', agentId);
    if (runId) params.append('run_id', runId);
    params.append('limit', limit.toString());
    return omind_get(`/api/v1/memory?${params.toString()}`);
  },

  /**
   * 搜索记忆 (Mem0: memory.search())
   */
  async searchMemories(searchParams: MemorySearchParams) {
    const params = new URLSearchParams();
    params.append('query', searchParams.query);
    if (searchParams.user_id) params.append('user_id', searchParams.user_id);
    if (searchParams.agent_id) params.append('agent_id', searchParams.agent_id);
    if (searchParams.run_id) params.append('run_id', searchParams.run_id);
    if (searchParams.limit) params.append('limit', searchParams.limit.toString());
    if (searchParams.threshold) params.append('threshold', searchParams.threshold.toString());
    return omind_get(`/api/v1/memory/search?${params.toString()}`);
  },

  /**
   * 获取单个记忆 (Mem0: memory.get())
   */
  async getMemory(memoryId: string) {
    return omind_get(`/api/v1/memory/${memoryId}`);
  },

  /**
   * 更新记忆 (Mem0: memory.update())
   */
  async updateMemory(memoryId: string, data: MemoryUpdateRequest) {
    return omind_put(`/api/v1/memory/${memoryId}`, data);
  },

  /**
   * 删除单个记忆 (Mem0: memory.delete())
   */
  async deleteMemory(memoryId: string) {
    return omind_del(`/api/v1/memory/${memoryId}`);
  },

  /**
   * 删除所有记忆 (Mem0: memory.delete_all())
   */
  async deleteAllMemories(userId?: string, agentId?: string, runId?: string) {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (agentId) params.append('agent_id', agentId);
    if (runId) params.append('run_id', runId);
    return omind_del(`/api/v1/memory?${params.toString()}`);
  },

  /**
   * 获取记忆历史 (Mem0: memory.history())
   */
  async getMemoryHistory(memoryId: string) {
    return omind_get(`/api/v1/memory/${memoryId}/history`);
  },

  /**
   * 重置记忆系统 (Mem0: memory.reset())
   * 危险操作：删除所有记忆
   */
  async resetMemory() {
    return omind_post('/api/v1/memory/reset', {});
  },

  // ==================== 便捷方法 ====================

  /**
   * 按层级获取记忆（便捷方法）
   */
  async getMemoriesByLevel(level: 'user' | 'agent' | 'session' | 'user_agent', params?: {
    userId?: string;
    agentId?: string;
    runId?: string;
    limit?: number;
  }) {
    switch(level) {
      case 'user':
        // 用户记忆：仅user_id
        return this.getAllMemories(params?.userId, undefined, undefined, params?.limit);

      case 'agent':
        // 智能体记忆：仅agent_id
        return this.getAllMemories(undefined, params?.agentId, undefined, params?.limit);

      case 'session':
        // 会话记忆：user_id + run_id
        return this.getAllMemories(params?.userId, undefined, params?.runId, params?.limit);

      case 'user_agent':
        // 交互记忆：user_id + agent_id
        return this.getAllMemories(params?.userId, params?.agentId, undefined, params?.limit);

      default:
        return this.getAllMemories(params?.userId, params?.agentId, params?.runId, params?.limit);
    }
  },

  /**
   * 从对话中添加记忆（便捷方法）
   */
  async addConversationMemory(messages: Array<{role: string, content: string}>, params?: {
    userId?: string;
    agentId?: string;
    runId?: string;
    metadata?: Record<string, any>;
  }) {
    return this.addMemory({
      messages,
      user_id: params?.userId,
      agent_id: params?.agentId,
      run_id: params?.runId,
      metadata: params?.metadata,
      infer: true
    });
  },

  /**
   * 简化的搜索接口（便捷方法）
   */
  async simpleSearch(query: string, limit: number = 20) {
    return this.searchMemories({ query, limit });
  }
};

// ==================== 迁移提示 ====================

/**
 * @deprecated 请使用 memoryApi.addMemory 代替
 */
export const addConversationMemory = (messages: any, userId?: string, agentId?: string) => {
  console.warn('addConversationMemory 已废弃，请使用 memoryApi.addMemory');
  return memoryApi.addConversationMemory(messages, { userId, agentId });
};

/**
 * @deprecated 请使用 memoryApi.getAllMemories 代替
 */
export const listAllMemories = (userId?: string, agentId?: string) => {
  console.warn('listAllMemories 已废弃，请使用 memoryApi.getAllMemories');
  return memoryApi.getAllMemories(userId, agentId);
};

/**
 * @deprecated 请使用 memoryApi.deleteAllMemories 代替
 */
export const deleteAllMemories = (userId?: string, agentId?: string) => {
  console.warn('deleteAllMemories 已废弃，请使用 memoryApi.deleteAllMemories');
  return memoryApi.deleteAllMemories(userId, agentId);
};

export default memoryApi;