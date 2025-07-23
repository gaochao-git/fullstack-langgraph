/**
 * 智能体管理API服务
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
}

export interface UpdateMCPConfigRequest {
  enabled_servers: string[];
  selected_tools: string[];
}

class AgentApiService {
  /**
   * 获取所有智能体
   */
  async getAgents(): Promise<Agent[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/`);
      if (!response.ok) {
        throw new Error(`获取智能体列表失败: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('获取智能体列表失败:', error);
      throw error;
    }
  }

  /**
   * 获取MCP服务器信息
   */
  async getMCPServers(): Promise<MCPServer[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/mcp-servers`);
      if (!response.ok) {
        throw new Error(`获取MCP服务器信息失败: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('获取MCP服务器信息失败:', error);
      throw error;
    }
  }

  /**
   * 更新智能体MCP配置
   */
  async updateAgentMCPConfig(agentId: string, config: UpdateMCPConfigRequest): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/mcp-config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        throw new Error(`更新MCP配置失败: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('更新MCP配置失败:', error);
      throw error;
    }
  }

  /**
   * 切换智能体启用状态
   */
  async toggleAgentStatus(agentId: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/toggle`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`切换智能体状态失败: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('切换智能体状态失败:', error);
      throw error;
    }
  }
}

export const agentApi = new AgentApiService();