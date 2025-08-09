/**
 * AI Model API服务 - API层透传，不处理业务逻辑
 */

import { omind_get, omind_post, omind_put, omind_del, omind_patch } from '@/utils/base_api';

// AI模型类型定义
export interface AIModel {
  id: number;
  model_id: string;
  model_name: string;
  model_provider: string;
  model_type: string;
  endpoint_url: string;
  api_key_value?: string;
  model_description?: string;
  model_status: string;
  config_data?: string;
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

export interface AIModelCreateRequest {
  model_name: string;
  model_provider: string;
  model_type: string;
  endpoint_url: string;
  api_key_value?: string;
  model_description?: string;
  config_data?: Record<string, any>;
}

export interface AIModelUpdateRequest {
  model_name?: string;
  model_provider?: string;
  model_type?: string;
  endpoint_url?: string;
  api_key_value?: string;
  model_description?: string;
  model_status?: 'active' | 'inactive' | 'error';
  config_data?: Record<string, any>;
}

export interface AIModelListParams {
  page?: number;
  size?: number;
  search?: string;
  provider?: string;
  status?: 'active' | 'inactive' | 'error';
  model_type?: string;
}

export interface AIModelTestRequest {
  model_provider: string;
  model_type: string;
  endpoint_url: string;
  api_key_value?: string;
  timeout?: number;
}

export interface AIModelTestResponse {
  status: string;
  message: string;
  latency_ms?: number;
  error_details?: string;
}

export interface OllamaDiscoverRequest {
  endpoint_url: string;
  timeout?: number;
}

export interface OllamaDiscoverResponse {
  models: string[];
  count: number;
}


// AI Model API接口类
export class AIModelApi {
  // 获取AI模型列表
  static async getAIModels(params: AIModelListParams = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.provider) queryParams.append('provider', params.provider);
    if (params.status) queryParams.append('status', params.status);
    if (params.model_type) queryParams.append('model_type', params.model_type);

    const url = `/api/v1/ai-models${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取单个AI模型
  static async getAIModelById(modelId: string) {
    return await omind_get(`/api/v1/ai-models/${modelId}`);
  }

  // 创建AI模型
  static async createAIModel(modelData: AIModelCreateRequest) {
    return await omind_post('/api/v1/ai-models', modelData);
  }

  // 更新AI模型
  static async updateAIModel(modelId: string, modelData: AIModelUpdateRequest) {
    return await omind_put(`/api/v1/ai-models/${modelId}`, modelData);
  }

  // 删除AI模型
  static async deleteAIModel(modelId: string) {
    return await omind_del(`/api/v1/ai-models/${modelId}`);
  }

  // 测试AI模型连接
  static async testAIModel(testData: AIModelTestRequest) {
    return await omind_post('/api/v1/ai-models/test-connection', testData);
  }

  // 发现Ollama模型
  static async discoverOllamaModels(discoverData: OllamaDiscoverRequest) {
    return await omind_post('/api/v1/ai-models/discover-ollama', discoverData);
  }

  // 更新模型状态
  static async updateModelStatus(modelId: string, status: 'active' | 'inactive' | 'error') {
    return await omind_patch(`/api/v1/ai-models/${modelId}/status`, { status });
  }

  // 获取提供商列表
  static async getProviders() {
    return await omind_get('/api/v1/ai-models/meta/providers');
  }

  // 获取模型类型列表
  static async getModelTypes() {
    return await omind_get('/api/v1/ai-models/meta/types');
  }

  // 获取统计信息
  static async getStatistics() {
    return await omind_get('/api/v1/ai-models/meta/statistics');
  }
}

export default AIModelApi;