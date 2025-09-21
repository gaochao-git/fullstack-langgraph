/**
 * 智能体运行日志相关 API
 */

import { omind_get, UnifiedResponse } from '@/utils/base_api';

export interface RunLog {
  id: number;
  agent_id: string;
  thread_id: string;
  user_name: string;
  user_display_name: string;
  run_status: 'running' | 'success' | 'failed';
  start_time: string;
  end_time?: string;
  duration_ms?: number;
  error_message?: string;
  token_usage?: number;
  message_count: number;
  ip_address?: string;
  user_agent?: string;
  create_time: string;
}

export interface RunLogStats {
  unique_users: number;
  total_runs: number;
  success_runs: number;
  failed_runs: number;
  success_rate: number;
  avg_duration_ms: number;
  total_tokens: number;
}

export interface UserRunStats {
  user_name: string;
  user_display_name: string;
  run_count: number;
  last_run_time?: string;
}

export interface RunLogsResponse {
  logs: RunLog[];
  total: number;
  stats: RunLogStats;
  user_stats: UserRunStats[];
}

export interface UserRunSummary {
  user_name: string;
  user_display_name: string;
  total_runs: number;
  success_runs: number;
  success_rate: number;
  avg_duration_ms: number;
  total_tokens: number;
  last_run_time?: string;
}

export interface RunSummaryResponse {
  agent_id: string;
  days: number;
  user_stats: UserRunSummary[];
}

/**
 * 运行日志 API
 */
export const runLogApi = {
  /**
   * 获取智能体运行日志
   */
  async getRunLogs(
    agentId: string,
    params?: {
      limit?: number;
      offset?: number;
      user_name?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<UnifiedResponse<RunLogsResponse>> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const queryString = queryParams.toString();
    const url = `/api/v1/agents/${agentId}/run-logs${queryString ? `?${queryString}` : ''}`;
    
    return omind_get<RunLogsResponse>(url);
  },

  /**
   * 获取智能体运行统计摘要
   */
  async getRunSummary(
    agentId: string,
    days: number = 7
  ): Promise<UnifiedResponse<RunSummaryResponse>> {
    return omind_get<RunSummaryResponse>(
      `/api/v1/agents/${agentId}/run-summary?days=${days}`
    );
  },
};