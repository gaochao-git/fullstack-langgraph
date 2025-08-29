/**
 * 智能体管理API服务 - API层透传，不处理业务逻辑
 */

import { omind_get, omind_post, omind_put, omind_del } from '@/utils/base_api';

// 类型定义
export interface MCPTool {
  name: string;
  description: string;
  enabled: boolean;
  category: string;
  server_id: string;
  server_name: string;
}

export interface MCPServer {
  id: string;
  name: string;
  status: string;
  tools: MCPTool[];
}


export interface Agent {
  id: number;
  agent_id: string;
  agent_name: string;
  agent_type: string; // 智能体分类：日志分析、监控告警、故障诊断、性能优化、资源管理、运维部署、安全防护、合规审计、合同履约、变更管理、其他
  agent_description: string;
  agent_capabilities: string[];
  agent_version: string;
  agent_status: string; // 'running' | 'stopped' | 'error'
  agent_enabled: string; // 'yes' | 'no'
  agent_icon?: string; // 智能体图标
  is_builtin: string; // 'yes' | 'no'
  tools_info?: {
    system_tools: string[];
    mcp_tools: any[];
  };
  llm_info?: {
    model_name: string;
    temperature: number;
    max_tokens: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  } | Array<{
    model_name: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  }>;
  prompt_info?: {
    system_prompt: string;
    user_prompt_template?: string;
    assistant_prompt_template?: string;
  };
  mcp_config?: {
    total_tools: number;
    selected_tools: string[];
    servers: string[];
  };
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time?: string;
  last_used_at?: string;
  total_runs?: number;
  success_rate?: number;
  avg_response_time?: number;
  // 权限相关字段
  agent_owner?: string;
  visibility_type?: string;
  visibility_additional_users?: string[];
  favorite_users?: string[];
  is_favorited?: boolean; // 当前用户是否收藏
  // API调用密钥
  agent_key?: string;
}

export interface CreateAgentRequest {
  agent_name: string;
  agent_type: string;
  agent_description: string;
  agent_capabilities: string[];
  agent_version?: string;
  agent_status?: string;
  agent_enabled?: string;
  agent_icon?: string;
  is_builtin?: string;
  tools_info?: {
    system_tools: string[];
    mcp_tools: any[];
  };
  llm_info?: {
    model_name: string;
    temperature: number;
    max_tokens: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  } | Array<{
    model_name: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  }>;
  prompt_info?: {
    system_prompt: string;
    user_prompt_template?: string;
    assistant_prompt_template?: string;
  };
  mcp_config?: {
    total_tools: number;
    selected_tools: string[];
    servers: string[];
  };
  // 权限相关字段
  visibility_type?: string;
  visibility_additional_users?: string[];
}

export interface UpdateAgentRequest extends Partial<CreateAgentRequest> {}

export interface UpdateMCPConfigRequest {
  mcp_config: {
    total_tools: number;
    selected_tools: string[];
    servers: string[];
  };
}

export interface UpdateStatisticsRequest {
  total_queries?: number;
  success_queries?: number;
  failed_queries?: number;
  last_used_at?: string;
}

export interface AgentStatistics {
  total_agents: number;
  active_agents: number;
  builtin_agents: number;
  custom_agents: number;
  status_distribution: {
    running: number;
    stopped: number;
    error: number;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    total: number;
    page: number;
    size: number;
    pages: number;
  };
}


// 智能体API服务类
class AgentApiService {
  /**
   * 获取智能体列表
   */
  async getAgents(params?: {
    page?: number;
    size?: number;
    search?: string;
    status?: string;
    enabled_only?: boolean;
    create_by?: string;
    owner_filter?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.size) searchParams.set('size', params.size.toString());
    if (params?.search) searchParams.set('search', params.search);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.enabled_only) searchParams.set('enabled_only', params.enabled_only.toString());
    if (params?.create_by) searchParams.set('create_by', params.create_by);
    if (params?.owner_filter) searchParams.set('owner_filter', params.owner_filter);

    const url = `/api/v1/agents${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    return await omind_get(url);
  }

  /**
   * 获取所有智能体（简化接口，兼容现有代码）
   */
  async getAllAgents() {
    return await this.getAgents({ size: 100 });
  }

  /**
   * 获取智能体详情
   */
  async getAgent(agentId: string) {
    const url = `/api/v1/agents/${agentId}`;
    return await omind_get(url);
  }

  /**
   * 创建智能体
   */
  async createAgent(agentData: CreateAgentRequest) {
    return await omind_post('/api/v1/agents', agentData);
  }

  /**
   * 更新智能体
   */
  async updateAgent(agentId: string, agentData: UpdateAgentRequest) {
    return await omind_put(`/api/v1/agents/${agentId}`, agentData);
  }

  /**
   * 删除智能体
   */
  async deleteAgent(agentId: string) {
    return await omind_del(`/api/v1/agents/${agentId}`);
  }

  /**
   * 更新智能体MCP配置
   */
  async updateAgentMCPConfig(agentId: string, config: UpdateMCPConfigRequest) {
    return await omind_put(`/api/v1/agents/${agentId}/mcp-config`, config);
  }

  /**
   * 更新智能体状态
   */
  async updateAgentStatus(agentId: string, status: string) {
    return await omind_put(`/api/v1/agents/${agentId}/status`, { status });
  }

  /**
   * 更新智能体统计信息
   */
  async updateAgentStatistics(
    agentId: string,
    stats: UpdateStatisticsRequest
  ) {
    return await omind_put(`/api/v1/agents/${agentId}/statistics`, stats);
  }

  /**
   * 获取智能体统计信息
   */
  async getAgentStatistics() {
    return await omind_get('/api/v1/agents/meta/statistics');
  }

  /**
   * 搜索智能体
   */
  async searchAgents(params: {
    query: string;
    page?: number;
    size?: number;
    filters?: {
      status?: string;
      enabled?: boolean;
      builtin?: boolean;
    };
  }) {
    const searchParams = new URLSearchParams({
      q: params.query,
      ...(params.page && { page: params.page.toString() }),
      ...(params.size && { size: params.size.toString() }),
      ...(params.filters?.status && { status: params.filters.status }),
      ...(params.filters?.enabled !== undefined && { enabled: params.filters.enabled.toString() }),
      ...(params.filters?.builtin !== undefined && { builtin: params.filters.builtin.toString() }),
    });

    return await omind_get(`/api/v1/agents/search?${searchParams}`);
  }

  /**
   * 刷新后端智能体配置（兼容接口）
   */
  async refreshAssistants() {
    return await omind_post('/api/admin/refresh-assistants');
  }

  /**
   * 获取后端智能体状态（兼容接口）
   */
  async getAssistantsStatus() {
    return await omind_get('/api/admin/assistants-status');
  }

  /**
   * 获取MCP服务器信息（兼容接口）
   */
  async getMCPServers() {
    return await omind_get('/api/v1/mcp/servers?size=100');
  }

  /**
   * 获取智能体可用模型（兼容接口）
   */
  async getAgentAvailableModels(agentId: string) {
    return await omind_get(`/api/v1/agents/${agentId}/available-models`);
  }

  /**
   * 切换智能体收藏状态
   */
  async toggleFavorite(agentId: string, isFavorite: boolean) {
    return await omind_post(`/api/v1/agents/${agentId}/favorite?is_favorite=${isFavorite}`);
  }

  /**
   * 转移智能体所有权
   */
  async transferOwnership(agentId: string, data: {
    new_owner: string;
    reason?: string;
  }) {
    return await omind_post(`/api/v1/agents/${agentId}/transfer-ownership`, data);
  }

  /**
   * 获取用户收藏的智能体列表
   */
  async getFavoriteAgents(params?: {
    page?: number;
    size?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.size) searchParams.set('size', params.size.toString());

    const url = `/api/v1/agents/favorites${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    return await omind_get(url);
  }

  /**
   * 重置智能体调用密钥
   */
  async resetAgentKey(agentId: string) {
    return await omind_post(`/api/v1/agents/${agentId}/reset-key`);
  }

  /**
   * 创建智能体权限
   */
  async createAgentPermission(agentId: string, userName: string, markComment?: string) {
    const params = new URLSearchParams({
      user_name: userName,
      ...(markComment && { mark_comment: markComment })
    });
    return await omind_post(`/api/v1/agents/${agentId}/permissions?${params}`);
  }

  /**
   * 获取智能体权限列表
   */
  async listAgentPermissions(agentId: string, params?: {
    page?: number;
    size?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.size) searchParams.set('size', params.size.toString());

    const url = `/api/v1/agents/${agentId}/permissions${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    return await omind_get(url);
  }

  /**
   * 撤销智能体权限
   */
  async revokeAgentPermission(permissionId: number) {
    return await omind_del(`/api/v1/agents/permissions/${permissionId}`);
  }

  /**
   * 重新生成权限密钥
   */
  async regeneratePermissionKey(permissionId: number) {
    return await omind_post(`/api/v1/agents/permissions/${permissionId}/regenerate-key`);
  }

  /**
   * 切换权限状态
   */
  async togglePermissionStatus(permissionId: number, isActive: boolean) {
    const params = new URLSearchParams({
      is_active: isActive.toString()
    });
    return await omind_put(`/api/v1/agents/permissions/${permissionId}/status?${params}`);
  }

}

// 导出服务实例
export const agentApi = new AgentApiService();

// 默认导出
export default agentApi;