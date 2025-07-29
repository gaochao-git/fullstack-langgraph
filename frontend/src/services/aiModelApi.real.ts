/**
 * AI Model API服务 - 真实API调用，适配统一响应格式
 */

import { omind_get, omind_post, omind_put, omind_del, omind_patch } from '../utils/base_api';

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

// AI Model API接口类
export class AIModelApi {
  // 获取AI模型列表
  static async getAIModels(params: AIModelListParams = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.size) queryParams.append('size', params.size.toString());
      if (params.search) queryParams.append('search', params.search);
      if (params.provider) queryParams.append('provider', params.provider);
      if (params.status) queryParams.append('status', params.status);
      if (params.model_type) queryParams.append('model_type', params.model_type);

      const url = `/api/v1/ai-models${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await omind_get(url);
      const responseData = await response.json();
      
      // 处理分页响应格式
      const result = handleUnifiedResponse(responseData);
      
      // 转换为前端期望的格式
      return {
        success: true,
        data: {
          data: result.items,
          total: result.pagination.total
        }
      };
    } catch (error) {
      console.error('Failed to fetch AI models:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取AI模型列表失败'
      };
    }
  }

  // 获取单个AI模型
  static async getAIModelById(modelId: string) {
    try {
      const response = await omind_get(`/api/v1/ai-models/${modelId}`);
      const responseData = await response.json();
      const result = handleUnifiedResponse<AIModel>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to fetch AI model ${modelId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'AI模型不存在'
      };
    }
  }

  // 创建AI模型
  static async createAIModel(modelData: AIModelCreateRequest) {
    try {
      const response = await omind_post('/api/v1/ai-models', modelData);
      const responseData = await response.json();
      const result = handleUnifiedResponse<AIModel>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to create AI model:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '创建AI模型失败'
      };
    }
  }

  // 更新AI模型
  static async updateAIModel(modelId: string, modelData: AIModelUpdateRequest) {
    try {
      const response = await omind_put(`/api/v1/ai-models/${modelId}`, modelData);
      const responseData = await response.json();
      const result = handleUnifiedResponse<AIModel>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to update AI model ${modelId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新AI模型失败'
      };
    }
  }

  // 删除AI模型
  static async deleteAIModel(modelId: string) {
    try {
      const response = await omind_del(`/api/v1/ai-models/${modelId}`);
      const responseData = await response.json();
      handleUnifiedResponse(responseData);
      return {
        success: true,
        data: true
      };
    } catch (error) {
      console.error(`Failed to delete AI model ${modelId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '删除AI模型失败'
      };
    }
  }

  // 测试AI模型连接
  static async testAIModel(testData: AIModelTestRequest) {
    try {
      const response = await omind_post('/api/v1/ai-models/test-connection', testData);
      const responseData = await response.json();
      const result = handleUnifiedResponse<AIModelTestResponse>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to test AI model connection:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'AI模型连接测试失败'
      };
    }
  }

  // 发现Ollama模型
  static async discoverOllamaModels(discoverData: OllamaDiscoverRequest) {
    try {
      const response = await omind_post('/api/v1/ai-models/discover-ollama', discoverData);
      const responseData = await response.json();
      const result = handleUnifiedResponse<OllamaDiscoverResponse>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to discover Ollama models:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '发现Ollama模型失败'
      };
    }
  }

  // 更新模型状态
  static async updateModelStatus(modelId: string, status: 'active' | 'inactive' | 'error') {
    try {
      const response = await omind_patch(`/api/v1/ai-models/${modelId}/status`, { status });
      const responseData = await response.json();
      const result = handleUnifiedResponse<AIModel>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to update model status ${modelId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新模型状态失败'
      };
    }
  }

  // 获取提供商列表
  static async getProviders() {
    try {
      const response = await omind_get('/api/v1/ai-models/meta/providers');
      const responseData = await response.json();
      const result = handleUnifiedResponse<string[]>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to fetch AI model providers:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取提供商列表失败'
      };
    }
  }

  // 获取模型类型列表
  static async getModelTypes() {
    try {
      const response = await omind_get('/api/v1/ai-models/meta/types');
      const responseData = await response.json();
      const result = handleUnifiedResponse<string[]>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to fetch AI model types:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取模型类型列表失败'
      };
    }
  }

  // 获取统计信息
  static async getStatistics() {
    try {
      const response = await omind_get('/api/v1/ai-models/meta/statistics');
      const responseData = await response.json();
      const result = handleUnifiedResponse<{
        status_statistics: Array<{status: string, count: number}>;
        provider_statistics: Array<{provider: string, count: number}>;
      }>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to fetch AI model statistics:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取统计信息失败'
      };
    }
  }
}

export default AIModelApi;