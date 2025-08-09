/**
 * MCP API服务 - API层透传，不处理业务逻辑
 */

import { omind_get, omind_post, omind_put, omind_del, omind_patch } from '../utils/base_api';

// MCP服务器类型定义
export interface MCPServer {
  id: number;
  server_id: string;
  server_name: string;
  server_uri: string;
  transport_type?: string;
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
  transport_type?: string;
  server_description?: string;
  is_enabled?: 'on' | 'off';
  connection_status?: 'connected' | 'disconnected' | 'error';
  auth_type?: string;
  auth_token?: string;
  api_key_header?: string;
  read_timeout_seconds?: number;
  server_tools?: any[];
  server_config?: Record<string, any>;
  team_name: string;
}

export interface MCPServerUpdateRequest {
  server_name?: string;
  server_uri?: string;
  transport_type?: string;
  server_description?: string;
  is_enabled?: 'on' | 'off';
  connection_status?: 'connected' | 'disconnected' | 'error';
  auth_type?: string;
  auth_token?: string;
  api_key_header?: string;
  read_timeout_seconds?: number;
  server_tools?: any[];
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


// MCP API接口类
export class MCPApi {
  // 获取MCP服务器列表
  static async getMCPServers(params: MCPListParams = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.is_enabled) queryParams.append('is_enabled', params.is_enabled);
    if (params.connection_status) queryParams.append('connection_status', params.connection_status);
    if (params.team_name) queryParams.append('team_name', params.team_name);

    const url = `/api/v1/mcp/servers${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取单个MCP服务器
  static async getMCPServerById(serverId: string) {
    return await omind_get(`/api/v1/mcp/servers/${serverId}`);
  }

  // 创建MCP服务器
  static async createMCPServer(serverData: MCPServerCreateRequest) {
    return await omind_post('/api/v1/mcp/servers', serverData);
  }

  // 更新MCP服务器
  static async updateMCPServer(serverId: string, serverData: MCPServerUpdateRequest) {
    return await omind_put(`/api/v1/mcp/servers/${serverId}`, serverData);
  }

  // 删除MCP服务器
  static async deleteMCPServer(serverId: string) {
    return await omind_del(`/api/v1/mcp/servers/${serverId}`);
  }

  // 测试MCP服务器连接
  static async testMCPServer(serverId: string) {
    return await omind_post(`/api/v1/mcp/servers/${serverId}/test`, {});
  }

  // 通用连接测试
  static async testConnection(testData: MCPTestRequest) {
    return await omind_post('/api/v1/mcp/test', testData);
  }

  // 更新服务器状态
  static async updateServerStatus(serverId: string, status: 'connected' | 'disconnected' | 'error') {
    return await omind_patch(`/api/v1/mcp/servers/${serverId}/status`, { status });
  }

  // 启用/禁用服务器
  static async toggleServerEnable(serverId: string, enabled: 'on' | 'off') {
    return await omind_patch(`/api/v1/mcp/servers/${serverId}/enable`, { enabled });
  }

  // 获取团队列表
  static async getTeams() {
    return await omind_get('/api/v1/mcp/servers/meta/teams');
  }

  // 获取统计信息
  static async getStatistics() {
    return await omind_get('/api/v1/mcp/servers/meta/statistics');
  }
}

export default MCPApi;