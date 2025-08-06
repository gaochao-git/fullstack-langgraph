/**
 * 智能体管理API服务 - 使用统一响应格式
 */

import { omind_get, omind_post, omind_put, omind_del } from '../utils/base_api';

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
  agent_type: string; // 智能体分类：办公、研发、运维、安全、审计、运营等
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
  };
  prompt_info?: {
    system_prompt: string;
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
  total_queries?: number;
  success_queries?: number;
  failed_queries?: number;
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
  };
  prompt_info?: {
    system_prompt: string;
  };
  mcp_config?: {
    total_tools: number;
    selected_tools: string[];
    servers: string[];
  };
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

/**
 * 处理统一响应格式
 */
function handleUnifiedResponse<T>(response: any): T {
  // 如果响应已经是期望的格式，直接返回
  if ('items' in response && 'pagination' in response) {
    return response;
  }
  
  // 如果是统一格式，提取数据
  if (response.status === 'ok') {
    return response.data;
  } else if (response.status === 'error') {
    throw new Error(response.msg || '请求失败');
  }
  
  // 兼容其他格式
  return response;
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
    include_builtin?: boolean;
  }): Promise<PaginatedResponse<Agent>> {
    try {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.size) searchParams.set('size', params.size.toString());
      if (params?.search) searchParams.set('search', params.search);
      if (params?.status) searchParams.set('status', params.status);
      if (params?.enabled_only) searchParams.set('enabled_only', params.enabled_only.toString());
      if (params?.include_builtin !== undefined) searchParams.set('include_builtin', params.include_builtin.toString());

      const url = `/api/v1/agents${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
      const result = await omind_get(url);
      return handleUnifiedResponse<PaginatedResponse<Agent>>(result);
    } catch (error) {
      console.error('获取智能体列表失败:', error);
      throw error;
    }
  }

  /**
   * 获取所有智能体（简化接口，兼容现有代码）
   */
  async getAllAgents(): Promise<Agent[]> {
    const result = await this.getAgents({ size: 100 });
    return result.items;
  }

  /**
   * 获取智能体详情
   */
  async getAgent(agentId: string): Promise<Agent> {
    try {
      const url = `/api/v1/agents/${agentId}`;
      const result = await omind_get(url);
      return handleUnifiedResponse<Agent>(result);
    } catch (error) {
      console.error('获取智能体失败:', error);
      throw error;
    }
  }

  /**
   * 创建智能体
   */
  async createAgent(agentData: CreateAgentRequest): Promise<Agent> {
    try {
      const result = await omind_post('/api/v1/agents', agentData);
      return handleUnifiedResponse<Agent>(result);
    } catch (error) {
      console.error('创建智能体失败:', error);
      throw error;
    }
  }

  /**
   * 更新智能体
   */
  async updateAgent(agentId: string, agentData: UpdateAgentRequest): Promise<Agent> {
    try {
      const result = await omind_put(`/api/v1/agents/${agentId}`, agentData);
      return handleUnifiedResponse<Agent>(result);
    } catch (error) {
      console.error('更新智能体失败:', error);
      throw error;
    }
  }

  /**
   * 删除智能体
   */
  async deleteAgent(agentId: string): Promise<{ deleted_id: string }> {
    try {
      const result = await omind_del(`/api/v1/agents/${agentId}`);
      return handleUnifiedResponse<{ deleted_id: string }>(result);
    } catch (error) {
      console.error('删除智能体失败:', error);
      throw error;
    }
  }

  /**
   * 更新智能体MCP配置
   */
  async updateAgentMCPConfig(agentId: string, config: UpdateMCPConfigRequest): Promise<Agent> {
    try {
      const result = await omind_put(`/api/v1/agents/${agentId}/mcp-config`, config);
      return handleUnifiedResponse<Agent>(result);
    } catch (error) {
      console.error('更新MCP配置失败:', error);
      throw error;
    }
  }

  /**
   * 更新智能体状态
   */
  async updateAgentStatus(agentId: string, status: string): Promise<Agent> {
    try {
      const result = await omind_put(`/api/v1/agents/${agentId}/status`, { status });
      return handleUnifiedResponse<Agent>(result);
    } catch (error) {
      console.error('更新智能体状态失败:', error);
      throw error;
    }
  }

  /**
   * 更新智能体统计信息
   */
  async updateAgentStatistics(
    agentId: string,
    stats: UpdateStatisticsRequest
  ): Promise<Agent> {
    try {
      const result = await omind_put(`/api/v1/agents/${agentId}/statistics`, stats);
      return handleUnifiedResponse<Agent>(result);
    } catch (error) {
      console.error('更新智能体统计信息失败:', error);
      throw error;
    }
  }

  /**
   * 获取智能体统计信息
   */
  async getAgentStatistics(): Promise<AgentStatistics> {
    try {
      const result = await omind_get('/api/v1/agents/meta/statistics');
      return handleUnifiedResponse<AgentStatistics>(result);
    } catch (error) {
      console.error('获取智能体统计信息失败:', error);
      throw error;
    }
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
  }): Promise<PaginatedResponse<Agent>> {
    try {
      const searchParams = new URLSearchParams({
        q: params.query,
        ...(params.page && { page: params.page.toString() }),
        ...(params.size && { size: params.size.toString() }),
        ...(params.filters?.status && { status: params.filters.status }),
        ...(params.filters?.enabled !== undefined && { enabled: params.filters.enabled.toString() }),
        ...(params.filters?.builtin !== undefined && { builtin: params.filters.builtin.toString() }),
      });

      const result = await omind_get(`/api/v1/agents/search?${searchParams}`);
      return handleUnifiedResponse<PaginatedResponse<Agent>>(result);
    } catch (error) {
      console.error('搜索智能体失败:', error);
      throw error;
    }
  }

  /**
   * 刷新后端智能体配置（兼容接口）
   */
  async refreshAssistants(): Promise<any> {
    try {
      return await omind_post('/api/admin/refresh-assistants');
    } catch (error) {
      console.error('刷新智能体配置失败:', error);
      throw error;
    }
  }

  /**
   * 获取后端智能体状态（兼容接口）
   */
  async getAssistantsStatus(): Promise<any> {
    try {
      return await omind_get('/api/admin/assistants-status');
    } catch (error) {
      console.error('获取智能体状态失败:', error);
      throw error;
    }
  }

  /**
   * 获取MCP服务器信息（兼容接口）
   */
  async getMCPServers(): Promise<MCPServer[]> {
    try {
      const result = await omind_get('/api/v1/mcp/servers?size=100');
      const paginatedResult = handleUnifiedResponse<{items: MCPServer[], total: number}>(result);
      return paginatedResult.items;
    } catch (error) {
      console.error('获取MCP服务器信息失败:', error);
      return [];
    }
  }

  /**
   * 获取智能体可用模型（兼容接口）
   */
  async getAgentAvailableModels(agentId: string): Promise<any[]> {
    try {
      return await omind_get(`/api/v1/agents/${agentId}/available-models`);
    } catch (error) {
      console.error('获取可用模型失败:', error);
      return [];
    }
  }
}

// 导出服务实例
export const agentApi = new AgentApiService();

// 默认导出
export default agentApi;