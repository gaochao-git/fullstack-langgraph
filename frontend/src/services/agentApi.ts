/**
 * 智能体管理API服务
 */

import { baseFetch } from '../utils/baseFetch';

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

export interface AgentMCPConfig {
  enabled_servers: string[];
  selected_tools: string[];
  total_tools: number;
}

export interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string;
  status: string;
  enabled: boolean;
  version: string;
  last_used?: string;
  total_runs: number;
  success_rate: number;
  avg_response_time: number;
  capabilities: string[];
  mcp_config: AgentMCPConfig;
  is_builtin: string; // 'yes' | 'no'
  tools_info?: any;
  llm_info?: any;
  prompt_info?: any;
}

export interface UpdateMCPConfigRequest {
  enabled_servers: string[];
  selected_tools: string[];
}

export interface CreateAgentRequest {
  agent_id?: string; // 改为可选
  agent_name: string;
  description: string;
  capabilities: string[];
  tools_info?: any;
  llm_info?: any;
  prompt_info?: any;
}

export interface UpdateAgentRequest {
  agent_name?: string;
  description?: string;
  capabilities?: string[];
  tools_info?: any;
  llm_info?: any;
  prompt_info?: any;
}

class AgentApiService {
  /**
   * 获取所有智能体
   */
  async getAgents(): Promise<Agent[]> {
    try {
      const response = await baseFetch('/api/v1/agents');
      if (!response.ok) {
        throw new Error(`获取智能体列表失败: ${response.statusText}`);
      }
      const result = await response.json();
      
      // 处理统一响应格式
      if (result.status === 'ok') {
        return result.data.items || result.data;
      } else {
        throw new Error(result.msg || '获取智能体列表失败');
      }
    } catch (error) {
      console.error('获取智能体列表失败:', error);
      throw error;
    }
  }

  /**
   * 获取所有智能体（简化接口，兼容现有代码）
   */
  async getAllAgents(): Promise<Agent[]> {
    try {
      const response = await baseFetch('/api/v1/agents?size=100');
      if (!response.ok) {
        throw new Error(`获取智能体列表失败: ${response.statusText}`);
      }
      const result = await response.json();
      
      // 处理统一响应格式
      if (result.status === 'ok') {
        return result.data.items || result.data;
      } else {
        throw new Error(result.msg || '获取智能体列表失败');
      }
    } catch (error) {
      console.error('获取智能体列表失败:', error);
      throw error;
    }
  }

  /**
   * 刷新后端智能体配置（无需重启服务）
   */
  async refreshAssistants(): Promise<any> {
    try {
      const response = await baseFetch('/api/admin/refresh-assistants', {
        method: 'POST',
      });
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
   * 获取后端智能体状态
   */
  async getAssistantsStatus(): Promise<any> {
    try {
      const response = await baseFetch('/api/admin/assistants-status');
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
   * 获取MCP服务器信息
   */
  async getMCPServers(): Promise<MCPServer[]> {
    try {
      const response = await baseFetch('/api/v1/mcp/servers');
      if (!response.ok) {
        throw new Error(`获取MCP服务器信息失败: ${response.statusText}`);
      }
      const result = await response.json();
      
      // 处理统一响应格式
      if (result.status === 'ok') {
        return result.data.items || result.data;
      } else {
        throw new Error(result.msg || '获取MCP服务器信息失败');
      }
    } catch (error) {
      console.error('获取MCP服务器信息失败:', error);
      throw error;
    }
  }

  /**
   * 更新智能体MCP配置
   */
  async updateAgentMCPConfig(agentId: string, config: UpdateMCPConfigRequest): Promise<Agent> {
    try {
      const response = await baseFetch(`/api/v1/agents/${agentId}/mcp-config`, {
        method: 'PUT',
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        throw new Error(`更新MCP配置失败: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // 处理统一响应格式
      if (result.status === 'ok') {
        return result.data;
      } else {
        throw new Error(result.msg || '更新MCP配置失败');
      }
    } catch (error) {
      console.error('更新MCP配置失败:', error);
      throw error;
    }
  }

  /**
   * 切换智能体启用状态
   */
  async toggleAgentStatus(agentId: string): Promise<Agent> {
    try {
      // 先获取当前状态
      const currentResponse = await baseFetch(`/api/v1/agents/${agentId}`);
      if (!currentResponse.ok) {
        throw new Error(`获取智能体状态失败: ${currentResponse.statusText}`);
      }
      
      const currentResult = await currentResponse.json();
      if (currentResult.status !== 'ok') {
        throw new Error(currentResult.msg || '获取智能体状态失败');
      }
      
      const currentAgent = currentResult.data;
      const newStatus = currentAgent.status === 'running' ? 'stopped' : 'running';
      
      // 更新状态
      const response = await baseFetch(`/api/v1/agents/${agentId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus }),
      });
      
      if (!response.ok) {
        throw new Error(`切换智能体状态失败: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // 处理统一响应格式
      if (result.status === 'ok') {
        return result.data;
      } else {
        throw new Error(result.msg || '切换智能体状态失败');
      }
    } catch (error) {
      console.error('切换智能体状态失败:', error);
      throw error;
    }
  }

  /**
   * 创建新智能体
   */
  async createAgent(agentData: CreateAgentRequest): Promise<Agent> {
    try {
      const response = await baseFetch('/api/v1/agents', {
        method: 'POST',
        body: JSON.stringify(agentData),
      });
      
      if (!response.ok) {
        throw new Error(`创建智能体失败: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // 处理统一响应格式
      if (result.status === 'ok') {
        return result.data;
      } else {
        throw new Error(result.msg || '创建智能体失败');
      }
    } catch (error) {
      console.error('创建智能体失败:', error);
      throw error;
    }
  }

  /**
   * 更新智能体信息
   */
  async updateAgent(agentId: string, agentData: UpdateAgentRequest): Promise<Agent> {
    try {
      const response = await baseFetch(`/api/v1/agents/${agentId}`, {
        method: 'PUT',
        body: JSON.stringify(agentData),
      });
      
      if (!response.ok) {
        throw new Error(`更新智能体失败: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // 处理统一响应格式
      if (result.status === 'ok') {
        return result.data;
      } else {
        throw new Error(result.msg || '更新智能体失败');
      }
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
      const response = await baseFetch(`/api/v1/agents/${agentId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`删除智能体失败: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // 处理统一响应格式
      if (result.status === 'ok') {
        return result.data;
      } else {
        throw new Error(result.msg || '删除智能体失败');
      }
    } catch (error) {
      console.error('删除智能体失败:', error);
      throw error;
    }
  }

  /**
   * 获取智能体可用模型
   */
  async getAgentAvailableModels(agentId: string): Promise<any[]> {
    try {
      const response = await baseFetch(`/api/agents/${agentId}/available-models`);
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