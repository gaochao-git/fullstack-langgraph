/**
 * SOP问题规则相关API
 */
import base_api from '@/utils/base_api';
import type { 
  SOPProblemRule, 
  SOPProblemRuleRequest,
  SOPProblemRuleQueryParams,
  ZabbixItemOption 
} from '@/pages/sop/types/sopProblemRule';

export const sopProblemRuleApi = {
  /**
   * 获取SOP问题规则列表
   */
  getRules: async (params: SOPProblemRuleQueryParams) => {
    const queryString = new URLSearchParams(params as any).toString();
    return base_api.omind_get(`/api/v1/sop-problem-rules?${queryString}`);
  },

  /**
   * 获取单个SOP问题规则
   */
  getRule: async (id: number) => {
    return base_api.omind_get(`/api/v1/sop-problem-rules/${id}`);
  },

  /**
   * 创建SOP问题规则
   */
  createRule: async (data: SOPProblemRuleRequest) => {
    return base_api.omind_post('/api/v1/sop-problem-rules', data);
  },

  /**
   * 更新SOP问题规则
   */
  updateRule: async (id: number, data: Partial<SOPProblemRuleRequest>) => {
    return base_api.omind_put(`/api/v1/sop-problem-rules/${id}`, data);
  },

  /**
   * 删除SOP问题规则
   */
  deleteRule: async (id: number) => {
    return base_api.omind_del(`/api/v1/sop-problem-rules/${id}`);
  },

  /**
   * 获取Zabbix监控项列表
   */
  getZabbixItems: async (params?: { search?: string; limit?: number }) => {
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    return base_api.omind_get(`/api/v1/sops/zabbix/items${queryString ? '?' + queryString : ''}`);
  }
};