/**
 * MCP API服务 - 真实API调用，适配统一响应格式
 */

import { baseFetchJson } from '../utils/baseFetch';

// MCP服务器类型定义
export interface MCPServer {
  id: number;
  server_id: string;
  server_name: string;
  server_uri: string;
  server_description?: string;
  is_enabled: string;
  connection_status: string;
  auth_type?: string;
  auth_token?: string;
  api_key_header?: string;
  read_timeout_seconds: number;
  server_tools?: string;
  server_config?: string;
  team_name: string;
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

export interface MCPServerCreateRequest {
  server_id: string;
  server_name: string;
  server_uri: string;
  server_description?: string;
  is_enabled?: 'on' | 'off';
  connection_status?: 'connected' | 'disconnected' | 'error';
  auth_type?: string;
  auth_token?: string;
  api_key_header?: string;
  read_timeout_seconds?: number;
  server_tools?: string[];
  server_config?: Record<string, any>;
  team_name: string;
}

export interface MCPServerUpdateRequest {
  server_name?: string;
  server_uri?: string;
  server_description?: string;
  is_enabled?: 'on' | 'off';
  connection_status?: 'connected' | 'disconnected' | 'error';
  auth_type?: string;
  auth_token?: string;
  api_key_header?: string;
  read_timeout_seconds?: number;
  server_tools?: string[];
  server_config?: Record<string, any>;
  team_name?: string;
}

export interface MCPListParams {
  page?: number;
  size?: number;
  search?: string;
  is_enabled?: 'on' | 'off';
  connection_status?: 'connected' | 'disconnected' | 'error';
  team_name?: string;
}

export interface MCPTestRequest {
  server_uri: string;
  timeout?: number;
}

export interface MCPTestResponse {
  healthy: boolean;
  tools: Array<{
    name: string;
    description: string;
    inputSchema?: any;
  }>;
  error?: string;
}

/**
 * 处理统一响应格式
 */
function handleUnifiedResponse<T>(response: any): T {
  if (response.status === 'ok') {
    return response.data;
  } else {
    throw new Error(response.msg || '请求失败');
  }
}

// MCP API接口类
export class MCPApi {
  // 获取MCP服务器列表
  static async getMCPServers(params: MCPListParams = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.size) queryParams.append('size', params.size.toString());
      if (params.search) queryParams.append('search', params.search);
      if (params.is_enabled) queryParams.append('is_enabled', params.is_enabled);
      if (params.connection_status) queryParams.append('connection_status', params.connection_status);
      if (params.team_name) queryParams.append('team_name', params.team_name);

      const url = `/api/v1/mcp/servers${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await baseFetchJson(url);
      
      // 处理分页响应格式
      const result = handleUnifiedResponse(response);
      
      // 转换为前端期望的格式
      return {
        success: true,
        data: {
          data: result.items,
          total: result.pagination.total
        }
      };
    } catch (error) {
      console.error('Failed to fetch MCP servers:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取MCP服务器列表失败'
      };
    }
  }

  // 获取单个MCP服务器
  static async getMCPServerById(serverId: string) {
    try {
      const response = await baseFetchJson(`/api/v1/mcp/servers/${serverId}`);
      const result = handleUnifiedResponse<MCPServer>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to fetch MCP server ${serverId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'MCP服务器不存在'
      };
    }
  }

  // 创建MCP服务器
  static async createMCPServer(serverData: MCPServerCreateRequest) {
    try {
      const response = await baseFetchJson('/api/v1/mcp/servers', {
        method: 'POST',
        body: JSON.stringify(serverData),
      });
      const result = handleUnifiedResponse<MCPServer>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to create MCP server:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '创建MCP服务器失败'
      };
    }
  }

  // 更新MCP服务器
  static async updateMCPServer(serverId: string, serverData: MCPServerUpdateRequest) {
    try {
      const response = await baseFetchJson(`/api/v1/mcp/servers/${serverId}`, {
        method: 'PUT',
        body: JSON.stringify(serverData),
      });
      const result = handleUnifiedResponse<MCPServer>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to update MCP server ${serverId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新MCP服务器失败'
      };
    }
  }

  // 删除MCP服务器
  static async deleteMCPServer(serverId: string) {
    try {
      const response = await baseFetchJson(`/api/v1/mcp/servers/${serverId}`, {
        method: 'DELETE',
      });
      handleUnifiedResponse(response);
      return {
        success: true,
        data: true
      };
    } catch (error) {
      console.error(`Failed to delete MCP server ${serverId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '删除MCP服务器失败'
      };
    }
  }

  // 测试MCP服务器连接
  static async testMCPServer(serverId: string) {
    try {
      const response = await baseFetchJson(`/api/v1/mcp/servers/${serverId}/test`, {
        method: 'POST',
      });
      const result = handleUnifiedResponse<MCPTestResponse>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to test MCP server ${serverId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'MCP服务器连接测试失败'
      };
    }
  }

  // 通用连接测试
  static async testConnection(testData: MCPTestRequest) {
    try {
      const response = await baseFetchJson('/api/v1/mcp/test', {
        method: 'POST',
        body: JSON.stringify(testData),
      });
      const result = handleUnifiedResponse<MCPTestResponse>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to test MCP connection:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'MCP连接测试失败'
      };
    }
  }

  // 更新服务器状态
  static async updateServerStatus(serverId: string, status: 'connected' | 'disconnected' | 'error') {
    try {
      const response = await baseFetchJson(`/api/v1/mcp/servers/${serverId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      const result = handleUnifiedResponse<MCPServer>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to update server status ${serverId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新服务器状态失败'
      };
    }
  }

  // 启用/禁用服务器
  static async toggleServerEnable(serverId: string, enabled: 'on' | 'off') {
    try {
      const response = await baseFetchJson(`/api/v1/mcp/servers/${serverId}/enable`, {
        method: 'PATCH',
        body: JSON.stringify({ enabled }),
      });
      const result = handleUnifiedResponse<MCPServer>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to toggle server enable ${serverId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '切换服务器状态失败'
      };
    }
  }

  // 获取团队列表
  static async getTeams() {
    try {
      const response = await baseFetchJson('/api/v1/mcp/servers/meta/teams');
      const result = handleUnifiedResponse<string[]>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to fetch MCP teams:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取团队列表失败'
      };
    }
  }

  // 获取统计信息
  static async getStatistics() {
    try {
      const response = await baseFetchJson('/api/v1/mcp/servers/meta/statistics');
      const result = handleUnifiedResponse<Array<{status: string, count: number}>>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to fetch MCP statistics:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取统计信息失败'
      };
    }
  }
}

export default MCPApi;