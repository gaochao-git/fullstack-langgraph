/**
 * SOP API服务 - API层透传，不处理业务逻辑
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


// SOP API接口类
export class SOPApi {
  // 获取SOP列表 - 改为GET请求
  static async getSOPs(params: SOPListParams = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.category) queryParams.append('category', params.category);
    if (params.severity && params.severity !== 'all') queryParams.append('severity', params.severity);
    if (params.team_name) queryParams.append('team_name', params.team_name);

    const url = `/api/v1/sops${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取单个SOP
  static async getSOPById(sopId: string) {
    return await omind_get(`/api/v1/sops/${sopId}`);
  }

  // 创建SOP
  static async createSOP(sopData: SOPTemplateRequest) {
    return await omind_post('/api/v1/sops', sopData);
  }

  // 更新SOP
  static async updateSOP(sopId: string, sopData: Partial<SOPTemplateRequest>) {
    return await omind_put(`/api/v1/sops/${sopId}`, sopData);
  }

  // 删除SOP
  static async deleteSOP(sopId: string) {
    return await omind_del(`/api/v1/sops/${sopId}`);
  }

  // 获取分类列表
  static async getCategories() {
    return await omind_get('/api/v1/sops/meta/categories');
  }

  // 获取团队列表
  static async getTeams() {
    return await omind_get('/api/v1/sops/meta/teams');
  }
}

export default SOPApi;