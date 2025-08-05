/**
 * 定时任务 API服务 - 真实API调用，适配统一响应格式
 */

import { omind_get, omind_post, omind_put, omind_del } from '../utils/base_api';

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

/**
 * 处理统一响应格式
 */
function handleUnifiedResponse<T>(response: any): T {
  if (response.status === 'ok') {
    return response.data;
  } else {
    throw new Error(response.msg || '请求失败');
  }
}

// 定时任务 API接口类
export class ScheduledTaskApi {
  // 获取定时任务列表
  static async getScheduledTasks(params: ScheduledTaskListParams = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.size) queryParams.append('size', params.size.toString());
      if (params.search) queryParams.append('search', params.search);
      if (params.enabled_only !== undefined) queryParams.append('enabled_only', params.enabled_only.toString());
      if (params.agent_id) queryParams.append('agent_id', params.agent_id);

      const url = `/api/v1/scheduled-tasks${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await omind_get(url);
      
      // 处理分页响应格式
      const result = handleUnifiedResponse(response);
      
      // 转换为前端期望的格式
      return {
        success: true,
        data: {
          data: result.items,
          total: result.pagination.total
        }
      };
    } catch (error) {
      console.error('Failed to fetch scheduled tasks:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取定时任务列表失败'
      };
    }
  }

  // 获取单个定时任务
  static async getScheduledTaskById(taskId: number) {
    try {
      const response = await omind_get(`/api/v1/scheduled-tasks/${taskId}`);
      const result = handleUnifiedResponse<ScheduledTask>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to fetch scheduled task ${taskId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '定时任务不存在'
      };
    }
  }

  // 创建定时任务
  static async createScheduledTask(taskData: ScheduledTaskCreateRequest) {
    try {
      const response = await omind_post('/api/v1/scheduled-tasks', taskData);
      const result = handleUnifiedResponse<ScheduledTask>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to create scheduled task:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '创建定时任务失败'
      };
    }
  }

  // 更新定时任务
  static async updateScheduledTask(taskId: number, taskData: ScheduledTaskUpdateRequest) {
    try {
      const response = await omind_put(`/api/v1/scheduled-tasks/${taskId}`, taskData);
      const result = handleUnifiedResponse<ScheduledTask>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to update scheduled task ${taskId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新定时任务失败'
      };
    }
  }

  // 删除定时任务
  static async deleteScheduledTask(taskId: number) {
    try {
      const response = await omind_del(`/api/v1/scheduled-tasks/${taskId}`);
      handleUnifiedResponse(response);
      return {
        success: true,
        data: true
      };
    } catch (error) {
      console.error(`Failed to delete scheduled task ${taskId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '删除定时任务失败'
      };
    }
  }

  // 启用定时任务
  static async enableScheduledTask(taskId: number) {
    try {
      const response = await omind_post(`/api/v1/scheduled-tasks/${taskId}/enable`);
      handleUnifiedResponse(response);
      return {
        success: true,
        data: true
      };
    } catch (error) {
      console.error(`Failed to enable scheduled task ${taskId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '启用任务失败'
      };
    }
  }

  // 禁用定时任务
  static async disableScheduledTask(taskId: number) {
    try {
      const response = await omind_post(`/api/v1/scheduled-tasks/${taskId}/disable`);
      handleUnifiedResponse(response);
      return {
        success: true,
        data: true
      };
    } catch (error) {
      console.error(`Failed to disable scheduled task ${taskId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '禁用任务失败'
      };
    }
  }

  // 手动触发定时任务
  static async triggerScheduledTask(taskId: number) {
    try {
      const response = await omind_post(`/api/v1/scheduled-tasks/${taskId}/trigger`);
      const result = handleUnifiedResponse(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to trigger scheduled task ${taskId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '触发任务失败'
      };
    }
  }

  // 获取任务执行日志
  static async getTaskExecutionLogs(taskId: number, skip: number = 0, limit: number = 50) {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('skip', skip.toString());
      queryParams.append('limit', limit.toString());

      const response = await omind_get(`/api/v1/scheduled-tasks/${taskId}/logs?${queryParams.toString()}`);
      const result = handleUnifiedResponse<TaskExecutionLog[]>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to fetch task execution logs ${taskId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取执行日志失败'
      };
    }
  }

  // 获取Celery任务记录列表
  static async getCeleryTaskRecords(params: CeleryTaskRecordListParams = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.size) queryParams.append('size', params.size.toString());
      if (params.task_name) queryParams.append('task_name', params.task_name);
      if (params.task_status) queryParams.append('task_status', params.task_status);

      const url = `/api/v1/scheduled-tasks/records${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await omind_get(url);
      
      // 处理分页响应格式
      const result = handleUnifiedResponse(response);
      
      // 转换为前端期望的格式
      return {
        success: true,
        data: {
          data: result.items,
          total: result.pagination.total
        }
      };
    } catch (error) {
      console.error('Failed to fetch celery task records:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取任务记录失败'
      };
    }
  }

  // 获取单个任务记录详情
  static async getCeleryTaskRecordById(recordId: number) {
    try {
      const response = await omind_get(`/api/v1/scheduled-tasks/records/${recordId}`);
      const result = handleUnifiedResponse<CeleryTaskRecord>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error(`Failed to fetch celery task record ${recordId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '任务记录不存在'
      };
    }
  }

  // 获取统计信息
  static async getStatistics() {
    try {
      const response = await omind_get('/api/v1/scheduled-tasks/meta/statistics');
      const result = handleUnifiedResponse<{
        task_statistics: Array<{enabled: boolean, count: number}>;
        record_statistics: Array<{status: string, count: number}>;
      }>(response);
      return {
        success: true,
        data: result
      };
    } catch (error) {
      console.error('Failed to fetch scheduled task statistics:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取统计信息失败'
      };
    }
  }
}

export default ScheduledTaskApi;