/**
 * 会话线程相关API
 */
import { omind_get, omind_post } from '@/utils/base_api';

export interface ThreadFiles {
  file_ids: string[];
}

export interface ThreadCreateRequest {
  assistant_id: string;  // 使用 assistant_id，与 LangGraph SDK 保持一致
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
    const response = await omind_post('/api/chat/threads', data);
    return response;
  },

  /**
   * 获取会话关联的文件ID列表
   * @param threadId 会话ID
   * @returns 文件ID列表
   */
  async getThreadFiles(threadId: string): Promise<ThreadFiles> {
    const response = await omind_get(`/api/v1/agents/threads/${threadId}/files`);
    return response.data;
  }
};