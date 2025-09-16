/**
 * 敏感数据扫描 API
 */
import { omind_get, omind_post, getBaseUrl } from '@/utils/base_api';
import { 
  ScanTask, 
  TaskDetail, 
  TaskResult 
} from '../types/scanTask';

export class ScanApi {
  /**
   * 创建扫描任务
   */
  static async createTask(fileIds: string[]) {
    const response = await omind_post('/api/v1/scan/tasks', {
      file_ids: fileIds
    });
    return { data: response };
  }

  /**
   * 获取任务进度
   */
  static async getTaskProgress(taskId: string) {
    const response = await omind_get(`/api/v1/scan/tasks/${taskId}/progress`);
    return { data: response };
  }

  /**
   * 获取任务结果
   */
  static async getTaskResult(taskId: string) {
    const response = await omind_get(`/api/v1/scan/tasks/${taskId}/result`);
    return { data: response };
  }

  /**
   * 获取任务列表
   */
  static async listTasks(params: {
    page?: number;
    size?: number;
    create_by?: string;
  }) {
    const response = await omind_get('/api/v1/scan/tasks', { body: params });
    return { data: response };
  }

  /**
   * 获取JSONL结果内容
   */
  static async getJsonlContent(taskId: string, fileId: string) {
    const response = await omind_get(`/api/v1/scan/results/${taskId}/${fileId}/jsonl`);
    return { data: response };
  }

  /**
   * 获取HTML报告URL
   */
  static getHtmlReportUrl(taskId: string, fileId: string) {
    const baseUrl = getBaseUrl();
    return `${baseUrl}/api/v1/scan/results/${taskId}/${fileId}/html`;
  }

  /**
   * 下载HTML报告
   */
  static async downloadHtmlReport(taskId: string, fileId: string) {
    const response = await omind_get(`/api/v1/scan/results/${taskId}/${fileId}/html`);
    return response;
  }
}