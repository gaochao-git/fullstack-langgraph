/**
 * SOP API服务 - 适配新的统一响应格式
 */

import {
  SOPTemplate,
  SOPTemplateRequest,
  SOPListParams,
  SOPStep,
  SOPSeverity
} from '../types/sop';
import { PaginatedData } from '../types/api';
import { ApiClient, ErrorHandler } from '../utils/apiClient';

// 工具函数
export class SOPUtils {
  // 解析步骤JSON字符串
  static parseSteps(stepsJson: string): SOPStep[] {
    try {
      return JSON.parse(stepsJson);
    } catch (error) {
      console.error('Failed to parse SOP steps:', error);
      return [];
    }
  }

  // 将步骤数组转换为JSON字符串
  static stringifySteps(steps: SOPStep[]): string {
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

/**
 * SOP API接口类 - 使用新的统一响应格式
 */
export class SOPApi {
  private static readonly BASE_PATH = '/api/v1/sops';

  /**
   * 获取SOP列表 - 分页查询
   */
  static async getSOPs(params: SOPListParams = {}): Promise<PaginatedData<SOPTemplate>> {
    try {
      const queryParams = {
        page: params.page || 1,
        size: params.size || 10,
        ...(params.search && { search: params.search }),
        ...(params.category && { category: params.category }),
        ...(params.severity && params.severity !== "all" && { severity: params.severity }),
        ...(params.team_name && { team_name: params.team_name }),
      };

      return await ApiClient.get<PaginatedData<SOPTemplate>>(
        this.BASE_PATH,
        queryParams
      );
    } catch (error) {
      console.error('Failed to fetch SOPs:', error);
      throw error;
    }
  }

  /**
   * 根据ID获取单个SOP
   */
  static async getSOPById(sopId: string): Promise<SOPTemplate> {
    try {
      return await ApiClient.get<SOPTemplate>(`${this.BASE_PATH}/${sopId}`);
    } catch (error) {
      console.error(`Failed to fetch SOP ${sopId}:`, error);
      throw error;
    }
  }

  /**
   * 创建SOP
   */
  static async createSOP(sopData: SOPTemplateRequest): Promise<SOPTemplate> {
    try {
      return await ApiClient.post<SOPTemplate>(this.BASE_PATH, sopData);
    } catch (error) {
      console.error('Failed to create SOP:', error);
      throw error;
    }
  }

  /**
   * 更新SOP
   */
  static async updateSOP(sopId: string, sopData: Partial<SOPTemplateRequest>): Promise<SOPTemplate> {
    try {
      return await ApiClient.put<SOPTemplate>(`${this.BASE_PATH}/${sopId}`, sopData);
    } catch (error) {
      console.error(`Failed to update SOP ${sopId}:`, error);
      throw error;
    }
  }

  /**
   * 删除SOP
   */
  static async deleteSOP(sopId: string): Promise<{ deleted_id: string }> {
    try {
      return await ApiClient.delete<{ deleted_id: string }>(`${this.BASE_PATH}/${sopId}`);
    } catch (error) {
      console.error(`Failed to delete SOP ${sopId}:`, error);
      throw error;
    }
  }

  /**
   * 获取分类列表
   */
  static async getCategories(): Promise<string[]> {
    try {
      return await ApiClient.get<string[]>(`${this.BASE_PATH}/meta/categories`);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      throw error;
    }
  }

  /**
   * 获取团队列表
   */
  static async getTeams(): Promise<string[]> {
    try {
      return await ApiClient.get<string[]>(`${this.BASE_PATH}/meta/teams`);
    } catch (error) {
      console.error('Failed to fetch teams:', error);
      throw error;
    }
  }

  /**
   * 获取统计信息
   */
  static async getStatistics(): Promise<Array<{ category: string; count: number }>> {
    try {
      return await ApiClient.get<Array<{ category: string; count: number }>>(
        `${this.BASE_PATH}/meta/statistics`
      );
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
      throw error;
    }
  }
}

/**
 * SOP相关的错误处理工具
 */
export class SOPErrorHandler {
  /**
   * 处理SOP相关错误并返回用户友好的消息
   */
  static handleError(error: unknown): string {
    if (ErrorHandler.isNotFoundError(error)) {
      return "SOP模板不存在";
    }
    
    if (ErrorHandler.isValidationError(error)) {
      return "SOP数据验证失败，请检查输入内容";
    }
    
    if (ErrorHandler.isUnauthorizedError(error)) {
      return "没有权限访问此SOP";
    }
    
    return ErrorHandler.handle(error);
  }

  /**
   * 检查是否为SOP不存在错误
   */
  static isSOPNotFound(error: unknown): boolean {
    return ErrorHandler.isNotFoundError(error);
  }
}

export default SOPApi;