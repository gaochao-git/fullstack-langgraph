/**
 * 定时任务 API服务 - API层透传，不处理业务逻辑
 */

import { omind_get, omind_post, omind_put, omind_del } from '@/utils/base_api';

// 定时任务类型定义
export interface ScheduledTask {
  id: number;
  name: string;
  task: string;
  description?: string;
  enabled: boolean;
  args?: string;
  kwargs?: string;
  extra?: string;
  interval?: number;
  crontab_minute?: string;
  crontab_hour?: string;
  crontab_day_of_week?: string;
  crontab_day_of_month?: string;
  crontab_month_of_year?: string;
  date_created: string;
  date_changed: string;
}

export interface ScheduledTaskCreateRequest {
  task_name: string;
  task_path: string;
  task_description?: string;
  task_extra_config?: string;
  task_interval?: number;
  task_crontab_minute?: string;
  task_crontab_hour?: string;
  task_crontab_day_of_week?: string;
  task_crontab_day_of_month?: string;
  task_crontab_month_of_year?: string;
  task_args?: string;
  task_kwargs?: string;
  task_enabled?: boolean;
}

export interface ScheduledTaskUpdateRequest {
  task_name?: string;
  task_path?: string;
  task_description?: string;
  task_extra_config?: string;
  task_interval?: number;
  task_crontab_minute?: string;
  task_crontab_hour?: string;
  task_crontab_day_of_week?: string;
  task_crontab_day_of_month?: string;
  task_crontab_month_of_year?: string;
  task_args?: string;
  task_kwargs?: string;
  task_enabled?: boolean;
}

export interface ScheduledTaskListParams {
  page?: number;
  size?: number;
  search?: string;
  enabled_only?: boolean;
  agent_id?: string;
}

export interface TaskExecutionLog {
  task_id: string;
  task_name: string;
  status: string;
  result?: string;
  date_created: string;
  date_done?: string;
  traceback?: string;
}

export interface CeleryTaskRecord {
  id: number;
  task_id: string;
  task_name: string;
  task_status: string;
  task_args?: string;
  task_kwargs?: string;
  task_result?: string;
  task_traceback?: string;
  create_time: string;
  update_time: string;
}

export interface CeleryTaskRecordListParams {
  page?: number;
  size?: number;
  task_name?: string;
  task_status?: string;
}


// 定时任务 API接口类
export class ScheduledTaskApi {
  // 获取定时任务列表
  static async getScheduledTasks(params: ScheduledTaskListParams = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.enabled_only !== undefined) queryParams.append('enabled_only', params.enabled_only.toString());
    if (params.agent_id) queryParams.append('agent_id', params.agent_id);

    const url = `/api/v1/scheduled-tasks${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取单个定时任务
  static async getScheduledTaskById(taskId: number) {
    return await omind_get(`/api/v1/scheduled-tasks/${taskId}`);
  }

  // 创建定时任务
  static async createScheduledTask(taskData: ScheduledTaskCreateRequest) {
    return await omind_post('/api/v1/scheduled-tasks', taskData);
  }

  // 更新定时任务
  static async updateScheduledTask(taskId: number, taskData: ScheduledTaskUpdateRequest) {
    return await omind_put(`/api/v1/scheduled-tasks/${taskId}`, taskData);
  }

  // 删除定时任务
  static async deleteScheduledTask(taskId: number) {
    return await omind_del(`/api/v1/scheduled-tasks/${taskId}`);
  }

  // 启用定时任务
  static async enableScheduledTask(taskId: number) {
    return await omind_post(`/api/v1/scheduled-tasks/${taskId}/enable`);
  }

  // 禁用定时任务
  static async disableScheduledTask(taskId: number) {
    return await omind_post(`/api/v1/scheduled-tasks/${taskId}/disable`);
  }

  // 手动触发定时任务
  static async triggerScheduledTask(taskId: number) {
    return await omind_post(`/api/v1/scheduled-tasks/${taskId}/trigger`);
  }

  // 获取任务执行日志
  static async getTaskExecutionLogs(taskId: number, skip: number = 0, limit: number = 50) {
    const queryParams = new URLSearchParams();
    queryParams.append('skip', skip.toString());
    queryParams.append('limit', limit.toString());

    return await omind_get(`/api/v1/scheduled-tasks/${taskId}/logs?${queryParams.toString()}`);
  }

  // 获取Celery任务记录列表
  static async getCeleryTaskRecords(params: CeleryTaskRecordListParams = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.task_name) queryParams.append('task_name', params.task_name);
    if (params.task_status) queryParams.append('task_status', params.task_status);

    const url = `/api/v1/scheduled-tasks/records${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // 获取单个任务记录详情
  static async getCeleryTaskRecordById(recordId: number) {
    return await omind_get(`/api/v1/scheduled-tasks/records/${recordId}`);
  }

  // 获取统计信息
  static async getStatistics() {
    return await omind_get('/api/v1/scheduled-tasks/meta/statistics');
  }
}

export default ScheduledTaskApi;