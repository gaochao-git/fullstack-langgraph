/**
 * SOP API服务 - API层透传，不处理业务逻辑
 */

import {
  SOPTemplate,
  SOPTemplateRequest,
  SOPListParams
} from '@/pages/sop/types/sop';
import { omind_get, omind_post, omind_put, omind_del } from '@/utils/base_api';

// 工具函数
export class SOPUtils {
  // 解析步骤JSON字符串
  static parseSteps(stepsJson: string | any) {
    try {
      // 如果已经是对象，直接返回
      if (typeof stepsJson === 'object' && stepsJson !== null) {
        return stepsJson;
      }
      // 如果是字符串，尝试解析
      if (typeof stepsJson === 'string') {
        return JSON.parse(stepsJson);
      }
      // 返回默认根节点
      return {
        step: '开始',
        description: '',
        execution_status: 'pending',
        health_status: 'unknown',
        children: []
      };
    } catch (error) {
      // Failed to parse SOP steps - 返回默认根节点
      return {
        step: '开始',
        description: '',
        execution_status: 'pending',
        health_status: 'unknown',
        children: []
      };
    }
  }

  // 将步骤对象转换为JSON字符串
  static stringifySteps(steps: any): string {
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
      // Failed to parse tools
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
    if (params.severity && params.severity !== 'all') queryParams.append('severity', params.severity);
    if (params.team_name) queryParams.append('team_name', params.team_name);

    const url = `/api/v1/sops${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }
  
  // 查询SOP模板（使用查询参数）
  static async querySOPTemplates(params: any = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.search) queryParams.append('search', params.search);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.offset) queryParams.append('offset', params.offset.toString());

    const url = `/api/v1/sops/query${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取单个SOP
  static async getSOPById(sopId: string) {
    return await omind_get(`/api/v1/sops/${sopId}`);
  }

  // 创建SOP模板
  static async createTemplate(sopData: SOPTemplateRequest) {
    return await omind_post('/api/v1/sops', sopData);
  }
  
  // 更新SOP模板
  static async updateTemplate(sopId: string, sopData: Partial<SOPTemplateRequest>) {
    return await omind_put(`/api/v1/sops/${sopId}`, sopData);
  }

  // 创建SOP（兼容旧接口）
  static async createSOP(sopData: SOPTemplateRequest) {
    return await omind_post('/api/v1/sops', sopData);
  }

  // 更新SOP（兼容旧接口）
  static async updateSOP(sopId: string, sopData: Partial<SOPTemplateRequest>) {
    return await omind_put(`/api/v1/sops/${sopId}`, sopData);
  }

  // 删除SOP
  static async deleteSOP(sopId: string) {
    return await omind_del(`/api/v1/sops/${sopId}`);
  }


  // 获取团队列表
  static async getTeams() {
    return await omind_get('/api/v1/sops/meta/teams');
  }

  // 获取报警 - 通用接口
  static async getAlarms(params: {
    alarm_level?: string[];
    alarm_time?: string;
    team_tag?: string[];
    idc_tag?: string[];
    alarm_ip?: string;
    page?: number;
    page_size?: number;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    // 处理数组参数
    if (params.alarm_level) {
      params.alarm_level.forEach(level => queryParams.append('alarm_level', level));
    }
    if (params.team_tag) {
      params.team_tag.forEach(tag => queryParams.append('team_tag', tag));
    }
    if (params.idc_tag) {
      params.idc_tag.forEach(tag => queryParams.append('idc_tag', tag));
    }
    
    // 处理单值参数
    if (params.alarm_time) queryParams.append('alarm_time', params.alarm_time);
    if (params.alarm_ip) queryParams.append('alarm_ip', params.alarm_ip);
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());
    
    const url = `/api/v1/sops/alarms${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }


  // 获取Zabbix监控项（保留以兼容）
  static async getZabbixItems(params: { search?: string; limit?: number } = {}) {
    const queryParams = new URLSearchParams();
    if (params.search) queryParams.append('search', params.search);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    const url = `/api/v1/sops/zabbix/items${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取Zabbix问题（保留作为Zabbix专用）
  static async getZabbixProblems(params: {
    host_id?: string;
    severity_min?: number;
    recent_only?: boolean;
    limit?: number;
  } = {}) {
    const queryParams = new URLSearchParams();
    if (params.host_id) queryParams.append('host_id', params.host_id);
    if (params.severity_min !== undefined) queryParams.append('severity_min', params.severity_min.toString());
    if (params.recent_only !== undefined) queryParams.append('recent_only', params.recent_only.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    const url = `/api/v1/sops/zabbix/problems${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取Zabbix问题监控项
  static async getZabbixProblemItems(params: { limit?: number } = {}) {
    const queryParams = new URLSearchParams();
    if (params.limit) queryParams.append('limit', params.limit.toString());
    const url = `/api/v1/sops/zabbix/problem-items${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取Zabbix主机列表
  static async getZabbixHosts() {
    return await omind_get('/api/v1/sops/zabbix/hosts');
  }
}

// 导出实例
export const sopApi = new SOPApi();

export default SOPApi;