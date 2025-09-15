/**
 * API Key 管理服务
 */

import { omind_del, omind_get, omind_post, omind_put } from '@/utils/base_api';

export interface CreateAPIKeyRequest {
  user_id: string;
  key_name: string;
  scopes?: number[];  // 权限ID列表
  allowed_ips?: string[];
  expires_in_days?: number;
  mark_comment?: string;
}

export interface APIKeyInfo {
  key_id: string;
  user_id: string;
  user_name?: string;
  key_name: string;
  api_key?: string;  // 完整的API密钥（明文）
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
  revoked_at?: string;
  revoke_reason?: string;
  is_active: boolean;
  scopes?: number[];  // 权限ID列表
  allowed_ips?: string[];
  mark_comment?: string;
  create_by?: string;
  update_by?: string;
}

export interface CreateAPIKeyResponse {
  api_key: string;  // 完整的key，只在创建时返回一次
  key_info: APIKeyInfo;
}

class APIKeyService {
  private baseUrl = '/api/v1/auth';

  /**
   * 创建API密钥
   */
  async createAPIKey(data: CreateAPIKeyRequest): Promise<CreateAPIKeyResponse> {
    return await omind_post(`${this.baseUrl}/api-keys`, data);
  }

  /**
   * 获取API密钥列表
   */
  async listAPIKeys(): Promise<APIKeyInfo[]> {
    return await omind_get(`${this.baseUrl}/api-keys`);
  }

  /**
   * 撤销API密钥（永久操作）
   */
  async revokeAPIKey(keyId: string, reason?: string): Promise<any> {
    const url = reason 
      ? `${this.baseUrl}/api-keys/${keyId}?reason=${encodeURIComponent(reason)}`
      : `${this.baseUrl}/api-keys/${keyId}`;
    return await omind_del(url);
  }

  /**
   * 切换API密钥激活状态
   */
  async toggleAPIKeyStatus(keyId: string): Promise<any> {
    return await omind_put(`${this.baseUrl}/api-keys/${keyId}/toggle`);
  }

  /**
   * 更新API密钥权限
   */
  async updateAPIKeyScopes(keyId: string, scopes: number[]): Promise<any> {
    return await omind_put(`${this.baseUrl}/api-keys/${keyId}/scopes`, scopes);
  }
}

export const apiKeyService = new APIKeyService();