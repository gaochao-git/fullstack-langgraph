/**
 * 扫描配置API
 */
import { omind_get, omind_post, omind_put, omind_del } from '@/utils/base_api';
import type { ScanConfig, ScanConfigCreate, ScanConfigUpdate } from '../types/scanConfig';

export const ScanConfigApi = {
  /**
   * 创建扫描配置
   */
  createConfig: (data: ScanConfigCreate) => {
    return omind_post('/api/v1/scan/configs', data);
  },

  /**
   * 更新扫描配置
   */
  updateConfig: (configId: string, data: ScanConfigUpdate) => {
    return omind_put(`/api/v1/scan/configs/${configId}`, data);
  },

  /**
   * 删除扫描配置
   */
  deleteConfig: (configId: string) => {
    return omind_del(`/api/v1/scan/configs/${configId}`);
  },

  /**
   * 获取配置详情
   */
  getConfig: (configId: string) => {
    return omind_get(`/api/v1/scan/configs/${configId}`);
  },

  /**
   * 获取默认配置
   */
  getDefaultConfig: () => {
    return omind_get('/api/v1/scan/configs/default/get');
  },

  /**
   * 查询配置列表
   */
  listConfigs: (params: {
    page: number;
    size: number;
    config_name?: string;
    status?: string;
  }) => {
    return omind_get('/api/v1/scan/configs', { body: params });
  },
};
