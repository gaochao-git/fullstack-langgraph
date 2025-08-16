/**
 * 会话线程相关API
 */
import { omind_get } from '@/utils/base_api';

export interface ThreadFiles {
  file_ids: string[];
}

export const threadApi = {
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