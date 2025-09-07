/**
 * 会话线程相关API
 */
import { omind_post } from '@/utils/base_api';

export interface ThreadCreateRequest {
  agent_id: string;  // 使用 agent_id，与系统命名保持一致
  user_name: string;
  metadata?: Record<string, any>;  // 保留用于其他扩展信息
}

export interface ThreadResponse {
  thread_id: string;
  created_at: string;
  metadata: Record<string, any>;
}

export const threadApi = {
  /**
   * 创建新的对话线程
   * @param data 线程创建参数
   * @returns 线程信息
   */
  async create(data: ThreadCreateRequest): Promise<ThreadResponse> {
    const response = await omind_post('/api/v1/chat/threads', data);
    // 处理统一响应格式，实际数据在 response.data 中
    if (response && response.status === 'ok' && response.data) {
      return response.data;
    }
    return response;
  }
};