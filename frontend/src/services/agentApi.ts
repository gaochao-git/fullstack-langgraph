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
  agent_description: string;
  agent_capabilities: string[];
  agent_version: string;
  agent_status: string; // 'running' | 'stopped' | 'error'
  agent_enabled: string; // 'yes' | 'no'
  agent_icon?: string; // 智能体图标
  is_builtin: string; // 'yes' | 'no'
  tools_info?: any;
  llm_info?: any;
  prompt_info?: any;
  total_runs: number;
  success_rate: number;
  avg_response_time: number;
  last_used?: string;
  config_version: string;
  is_active: boolean;
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

export interface CreateAgentRequest {
  agent_id?: string;
  agent_name: string;
  agent_description?: string;
  agent_capabilities?: string[];
  agent_version?: string;
  agent_status?: string;
  agent_enabled?: string;
  agent_icon?: string; // 智能体图标
  is_builtin?: string;
  tools_info?: any;
  llm_info?: any;
  prompt_info?: any;
  config_version?: string;
  is_active?: boolean;
  create_by?: string;
}

export interface UpdateAgentRequest {
  agent_name?: string;
  agent_description?: string;
  agent_capabilities?: string[];
  agent_version?: string;
  agent_status?: string;
  agent_enabled?: string;
  agent_icon?: string; // 智能体图标
  is_builtin?: string;
  tools_info?: any;
  llm_info?: any;
  prompt_info?: any;
  config_version?: string;
  is_active?: boolean;
  update_by?: string;
}

export interface UpdateMCPConfigRequest {
  enabled_servers: string[];
  selected_tools: string[];
}

export interface AgentStatusUpdate {
  status: string;
}

export interface AgentStatisticsUpdate {
  total_runs: number;
  success_rate: number;
  avg_response_time: number;
}

export interface AgentStatistics {
  total: number;
  enabled: number;
  running: number;
  builtin: number;
  custom: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// 统一响应处理函数
function handleUnifiedResponse<T>(response: any): T {
  if (response.status === 'ok') {
    return response.data;
  } else {
    throw new Error(response.msg || '请求失败');
  }
}

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
      const response = await omind_get(url);
      
      if (!response.ok) {
        throw new Error(`获取智能体列表失败: ${response.statusText}`);
      }
      
      const result = await response.json();
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
   * 获取指定智能体
   */
  async getAgent(agentId: string): Promise<Agent> {
    try {
      const url = `/api/v1/agents/${agentId}`;
      const response = await omind_get(url);
      
      if (!response.ok) {
        throw new Error(`获取智能体失败: ${response.statusText}`);
      }
      
      const result = await response.json();
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
      const response = await omind_post('/api/v1/agents', agentData);
      
      if (!response.ok) {
        throw new Error(`创建智能体失败: ${response.statusText}`);
      }
      
      const result = await response.json();
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
      const response = await omind_put(`/api/v1/agents/${agentId}`, agentData);
      
      if (!response.ok) {
        throw new Error(`更新智能体失败: ${response.statusText}`);
      }
      
      const result = await response.json();
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
      const response = await omind_del(`/api/v1/agents/${agentId}`);
      
      if (!response.ok) {
        throw new Error(`删除智能体失败: ${response.statusText}`);
      }
      
      const result = await response.json();
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
      const response = await omind_put(`/api/v1/agents/${agentId}/mcp-config`, config);
      
      if (!response.ok) {
        throw new Error(`更新MCP配置失败: ${response.statusText}`);
      }
      
      const result = await response.json();
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
      const response = await omind_put(`/api/v1/agents/${agentId}/status`, { status });
      
      if (!response.ok) {
        throw new Error(`更新智能体状态失败: ${response.statusText}`);
      }
      
      const result = await response.json();
      return handleUnifiedResponse<Agent>(result);
    } catch (error) {
      console.error('更新智能体状态失败:', error);
      throw error;
    }
  }

  /**
   * 切换智能体启用状态（兼容现有接口）
   */
  async toggleAgentStatus(agentId: string): Promise<Agent> {
    try {
      // 先获取当前状态
      const currentAgent = await this.getAgent(agentId);
      const newEnabled = currentAgent.agent_enabled === 'yes' ? 'no' : 'yes';
      
      return await this.updateAgent(agentId, { agent_enabled: newEnabled });
    } catch (error) {
      console.error('切换智能体状态失败:', error);
      throw error;
    }
  }

  /**
   * 更新智能体统计信息
   */
  async updateAgentStatistics(
    agentId: string, 
    stats: AgentStatisticsUpdate
  ): Promise<Agent> {
    try {
      const response = await omind_put(`/api/v1/agents/${agentId}/statistics`, stats);
      
      if (!response.ok) {
        throw new Error(`更新智能体统计信息失败: ${response.statusText}`);
      }
      
      const result = await response.json();
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
      const response = await omind_get('/api/v1/agents/meta/statistics');
      
      if (!response.ok) {
        throw new Error(`获取智能体统计信息失败: ${response.statusText}`);
      }
      
      const result = await response.json();
      return handleUnifiedResponse<AgentStatistics>(result);
    } catch (error) {
      console.error('获取智能体统计信息失败:', error);
      throw error;
    }
  }

  /**
   * 搜索智能体
   */
  async searchAgents(
    keyword: string, 
    page: number = 1, 
    size: number = 10
  ): Promise<PaginatedResponse<Agent>> {
    try {
      const searchParams = new URLSearchParams({
        keyword,
        page: page.toString(),
        size: size.toString()
      });

      const response = await omind_get(`/api/v1/agents/search?${searchParams}`);
      
      if (!response.ok) {
        throw new Error(`搜索智能体失败: ${response.statusText}`);
      }
      
      const result = await response.json();
      return handleUnifiedResponse<PaginatedResponse<Agent>>(result);
    } catch (error) {
      console.error('搜索智能体失败:', error);
      throw error;
    }
  }

  // ==================== 兼容现有接口 ====================

  /**
   * 刷新后端智能体配置（兼容接口）
   */
  async refreshAssistants(): Promise<any> {
    try {
      const response = await omind_post('/api/admin/refresh-assistants');
      if (!response.ok) {
        throw new Error(`刷新智能体配置失败: ${response.statusText}`);
      }
      return await response.json();
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
      const response = await omind_get('/api/admin/assistants-status');
      if (!response.ok) {
        throw new Error(`获取智能体状态失败: ${response.statusText}`);
      }
      return await response.json();
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
      const response = await omind_get('/api/v1/mcp/servers?size=100');
      if (!response.ok) {
        throw new Error(`获取MCP服务器信息失败: ${response.statusText}`);
      }
      const result = await response.json();
      const paginatedResult = handleUnifiedResponse<{items: MCPServer[], total: number}>(result);
      return paginatedResult.items;
    } catch (error) {
      console.error('获取MCP服务器信息失败:', error);
      throw error;
    }
  }

  /**
   * 获取智能体可用模型（兼容接口）
   */
  async getAgentAvailableModels(agentId: string): Promise<any[]> {
    try {
      const response = await omind_get(`/api/v1/agents/${agentId}/available-models`);
      if (!response.ok) {
        throw new Error(`获取可用模型失败: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('获取可用模型失败:', error);
      return [];
    }
  }
}

export const agentApi = new AgentApiService();