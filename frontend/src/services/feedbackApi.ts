/**
 * 消息反馈相关 API
 */

import { omind_post, UnifiedResponse } from '@/utils/base_api';

export interface MessageFeedbackRequest {
  feedback_type: 'thumbs_up' | 'thumbs_down';
  feedback_content?: string;
}

export interface MessageFeedbackResponse {
  thread_id: string;
  message_id: string;
  agent_id: string;
  user_name: string;
  feedback_type: string;
  feedback_content?: string;
  agent_stats: {
    thumbs_up_count: number;
    thumbs_down_count: number;
    total_runs: number;
    satisfaction_rate: number;
    total_feedback: number;
  };
}

/**
 * 提交消息反馈
 */
export const feedbackApi = {
  /**
   * 提交消息反馈（点赞/点踩）
   */
  async submitFeedback(
    threadId: string,
    messageId: string,
    feedback: MessageFeedbackRequest
  ): Promise<UnifiedResponse<MessageFeedbackResponse>> {
    return omind_post<MessageFeedbackResponse>(
      `/api/v1/chat/threads/${threadId}/messages/${messageId}/feedback`,
      feedback
    );
  },
};