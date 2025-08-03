/**
 * SOP API服务 - 真实API调用，适配统一响应格式
 */

import {
  SOPTemplate,
  SOPTemplateRequest,
  SOPListParams
} from '../pages/sop/types/sop';
import { omind_get, omind_post, omind_put, omind_del } from '../utils/base_api';

// 工具函数
export class SOPUtils {
  // 解析步骤JSON字符串
  static parseSteps(stepsJson: string | any) {
    try {
      // 如果已经是对象，直接返回
      if (typeof stepsJson === 'object' && stepsJson !== null) {
        return Array.isArray(stepsJson) ? stepsJson : [];
      }
      // 如果是字符串，尝试解析
      if (typeof stepsJson === 'string') {
        return JSON.parse(stepsJson);
      }
      return [];
    } catch (error) {
      console.error('Failed to parse SOP steps:', error);
      return [];
    }
  }

  // 将步骤数组转换为JSON字符串
  static stringifySteps(steps: any[]): string {
    return JSON.stringify(steps, null, 2);
  }

  // 解析工具JSON字符串
  static parseTools(toolsJson: string | any): string[] {
    try {
      // 如果已经是数组，直接返回
      if (Array.isArray(toolsJson)) {
        return toolsJson;
      }
      // 如果是其他对象，返回空数组
      if (typeof toolsJson === 'object' && toolsJson !== null) {
        return [];
      }
      // 如果是字符串，尝试解析
      if (typeof toolsJson === 'string') {
        const parsed = JSON.parse(toolsJson);
        return Array.isArray(parsed) ? parsed : [];
      }
      return [];
    } catch (error) {
      console.error('Failed to parse tools:', error);
      return [];
    }
  }

  // 将工具数组转换为JSON字符串
  static stringifyTools(tools: string[]): string {
    return JSON.stringify(tools);
  }
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

// SOP API接口类
export class SOPApi {
  // 获取SOP列表 - 改为GET请求
  static async getSOPs(params: SOPListParams = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.size) queryParams.append('size', params.size.toString());
      if (params.search) queryParams.append('search', params.search);
      if (params.category) queryParams.append('category', params.category);
      if (params.severity && params.severity !== 'all') queryParams.append('severity', params.severity);
      if (params.team_name) queryParams.append('team_name', params.team_name);

      const url = `/api/v1/sops${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await omind_get(url);
      const responseData = await response.json();
      
      // 处理分页响应格式
      const result = handleUnifiedResponse<{items: any[], pagination: {total: number}}>(responseData);
      
      // 转换为前端期望的格式
      return {
        success: true,
        data: {
          data: result.items,
          total: result.pagination.total
        }
      };
    } catch (error) {
      console.error('Failed to fetch SOPs:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取SOP数据失败'
      };
    }
  }

  // 获取单个SOP
  static async getSOPById(sopId: string) {
    try {
      const response = await omind_get(`/api/v1/sops/${sopId}`);
      const responseData = await response.json();
      const result = handleUnifiedResponse<SOPTemplate>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to fetch SOP ${sopId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'SOP不存在'
      };
    }
  }

  // 创建SOP
  static async createSOP(sopData: SOPTemplateRequest) {
    try {
      const response = await omind_post('/api/v1/sops', sopData);
      const responseData = await response.json();
      const result = handleUnifiedResponse<SOPTemplate>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to create SOP:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '创建SOP失败'
      };
    }
  }

  // 更新SOP
  static async updateSOP(sopId: string, sopData: Partial<SOPTemplateRequest>) {
    try {
      const response = await omind_put(`/api/v1/sops/${sopId}`, sopData);
      const responseData = await response.json();
      const result = handleUnifiedResponse<SOPTemplate>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to update SOP ${sopId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新SOP失败'
      };
    }
  }

  // 删除SOP
  static async deleteSOP(sopId: string) {
    try {
      const response = await omind_del(`/api/v1/sops/${sopId}`);
      const responseData = await response.json();
      handleUnifiedResponse(responseData);
      return {
        success: true,
        data: true
      };
    } catch (error) {
      console.error(`Failed to delete SOP ${sopId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '删除SOP失败'
      };
    }
  }

  // 获取分类列表
  static async getCategories() {
    try {
      const response = await omind_get('/api/v1/sops/meta/categories');
      const responseData = await response.json();
      const result = handleUnifiedResponse<string[]>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取分类列表失败'
      };
    }
  }

  // 获取团队列表
  static async getTeams() {
    try {
      const response = await omind_get('/api/v1/sops/meta/teams');
      const responseData = await response.json();
      const result = handleUnifiedResponse<string[]>(responseData);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to fetch teams:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取团队列表失败'
      };
    }
  }
}

export default SOPApi;