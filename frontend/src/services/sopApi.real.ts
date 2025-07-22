import {
  SOPTemplate,
  SOPTemplateRequest,
  SOPQueryParams,
  SOPListResponse,
  ApiResponse
} from '../types/sop';

// API基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 工具函数
export class SOPUtils {
  // 解析步骤JSON字符串
  static parseSteps(stepsJson: string) {
    try {
      return JSON.parse(stepsJson);
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
  static parseTools(toolsJson: string): string[] {
    try {
      return JSON.parse(toolsJson);
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

// 真实API接口类
export class SOPApi {
  // 获取SOP列表
  static async getSOPs(params: SOPQueryParams = {}): Promise<ApiResponse<SOPListResponse>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sops/list`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to fetch SOPs:', error);
      return {
        success: false,
        error: '获取SOP数据失败'
      };
    }
  }

  // 根据ID获取单个SOP
  static async getSOPById(sopId: string): Promise<ApiResponse<SOPTemplate>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sops/${sopId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to fetch SOP:', error);
      return {
        success: false,
        error: '获取SOP详情失败'
      };
    }
  }

  // 创建SOP
  static async createSOP(sopData: SOPTemplateRequest): Promise<ApiResponse<SOPTemplate>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sops`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sopData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to create SOP:', error);
      return {
        success: false,
        error: '创建SOP失败'
      };
    }
  }

  // 更新SOP
  static async updateSOP(sopId: string, sopData: Partial<SOPTemplateRequest>): Promise<ApiResponse<SOPTemplate>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sops/${sopId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...sopData,
          steps: sopData.steps || undefined,
          tools_required: sopData.tools_required || undefined
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to update SOP:', error);
      return {
        success: false,
        error: '更新SOP失败'
      };
    }
  }

  // 删除SOP
  static async deleteSOP(sopId: string): Promise<ApiResponse<boolean>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sops/${sopId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return {
        success: true,
        data: true
      };
    } catch (error) {
      console.error('Failed to delete SOP:', error);
      return {
        success: false,
        error: '删除SOP失败'
      };
    }
  }

  // 获取分类列表
  static async getCategories(): Promise<ApiResponse<string[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sops/meta/categories`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      return {
        success: false,
        error: '获取分类列表失败'
      };
    }
  }

  // 获取团队列表
  static async getTeams(): Promise<ApiResponse<string[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sops/meta/teams`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to fetch teams:', error);
      return {
        success: false,
        error: '获取团队列表失败'
      };
    }
  }
}

export default SOPApi;