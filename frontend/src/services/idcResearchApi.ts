/**
 * IDC 运行分析/监控 API 服务
 */

import { omind_get } from '@/utils/base_api';

class IDCResearchApi {
  private static base = '/api/v1/idc-research';

  static async getIDCs() {
    return omind_get(`${this.base}/idcs`);
  }

  static async getOverviewStats() {
    return omind_get(`${this.base}/overview/stats`);
  }

  static async getApplications() {
    return omind_get(`${this.base}/applications`);
  }

  static async getBusinessTypes() {
    return omind_get(`${this.base}/applications/business-types`);
  }

  static async getHardwareProducts(params: { category?: string } = {}) {
    const qs = new URLSearchParams();
    if (params.category) qs.append('category', params.category);
    const url = `${this.base}/hardware/products${qs.toString() ? `?${qs.toString()}` : ''}`;
    return omind_get(url);
  }

  static async getHardwareMetrics() {
    return omind_get(`${this.base}/hardware/metrics`);
  }

  static async getHardwarePlans() {
    return omind_get(`${this.base}/hardware/plans`);
  }

  static async getServerFailures(params: { months?: number } = {}) {
    const qs = new URLSearchParams();
    if (params.months) qs.append('months', String(params.months));
    const url = `${this.base}/server-failures${qs.toString() ? `?${qs.toString()}` : ''}`;
    return omind_get(url);
  }
}

export default IDCResearchApi;

