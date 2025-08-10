/**
 * API Key 管理服务
 */

import { omind_del, omind_get, omind_post } from '@/utils/base_api';

export interface CreateAPIKeyRequest {
  user_id: string;
  key_name: string;
  scopes?: string[];
  allowed_ips?: string[];
  expires_in_days?: number;
  mark_comment?: string;
}

export interface APIKeyInfo {
  key_id: string;
  user_id: string;
  user_name?: string;
  key_name: string;
  key_prefix: string;
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
  is_active: boolean;
  scopes?: string[];
  allowed_ips?: string[];
  mark_comment?: string;
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
   * 撤销API密钥
   */
  async revokeAPIKey(keyId: string): Promise<void> {
    return await omind_del(`${this.baseUrl}/api-keys/${keyId}`);
  }
}

export const apiKeyService = new APIKeyService();