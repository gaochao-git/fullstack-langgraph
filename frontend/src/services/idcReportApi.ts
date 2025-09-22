/**
 * IDC运行报告 API 服务
 */

import { omind_get, omind_post, omind_put, omind_del } from '@/utils/base_api';
import type { IDCReport } from '@/pages/idc_research';

export interface IDCReportListParams {
  page?: number;
  pageSize?: number;
  keyword?: string;
  idcLocation?: string;
  reportType?: string;
  status?: string;
  dateRange?: [string, string];
}

export interface CreateReportRequest {
  reportName: string;
  idcLocation: string;
  reportType: string;
  dateRange: [string, string];
}

export class IDCReportApi {
  private static baseUrl = '/api/v1/idc-reports';

  /**
   * 获取IDC报告列表
   */
  static async getReports(params: IDCReportListParams = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.pageSize) queryParams.append('page_size', params.pageSize.toString());
    if (params.keyword) queryParams.append('keyword', params.keyword);
    if (params.idcLocation) queryParams.append('idc_location', params.idcLocation);
    if (params.reportType) queryParams.append('report_type', params.reportType);
    if (params.status) queryParams.append('status', params.status);
    if (params.dateRange) {
      queryParams.append('start_date', params.dateRange[0]);
      queryParams.append('end_date', params.dateRange[1]);
    }
    
    const url = `${this.baseUrl}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  /**
   * 获取单个报告详情
   */
  static async getReport(reportId: string) {
    return await omind_get(`${this.baseUrl}/${reportId}`);
  }

  /**
   * 创建新的IDC报告生成任务
   */
  static async createReport(data: CreateReportRequest) {
    return await omind_post(`${this.baseUrl}`, data);
  }

  /**
   * 删除报告
   */
  static async deleteReport(reportId: string) {
    return await omind_del(`${this.baseUrl}/${reportId}`);
  }

  /**
   * 下载报告文件
   */
  static async downloadReport(reportId: string) {
    // 这里可以使用 fetch 直接下载文件
    const response = await fetch(`${this.baseUrl}/${reportId}/download`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('下载失败');
    }
    
    return response.blob();
  }

  /**
   * 获取IDC位置列表
   */
  static async getIDCLocations() {
    return await omind_get(`${this.baseUrl}/locations`);
  }

  /**
   * 获取报告统计信息
   */
  static async getReportStats() {
    return await omind_get(`${this.baseUrl}/stats`);
  }
}

export default IDCReportApi;