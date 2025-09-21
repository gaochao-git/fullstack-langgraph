import { useState, useEffect, useCallback } from 'react';
import { omind_get } from '@/utils/base_api';
import { Message } from './useStream';
import { message as antMessage } from 'antd';

export interface CheckpointMessage extends Message {
  token_count?: number;
}

export interface CheckpointMessagesData {
  messages: CheckpointMessage[];
  total_tokens: number;
  message_count: number;
  thread_id: string;
}

export interface UseCheckpointMessagesOptions {
  threadId: string | null;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export interface UseCheckpointMessagesReturn {
  messages: CheckpointMessage[];
  totalTokens: number;
  messageCount: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

/**
 * Hook for fetching messages from checkpoint
 * This returns the actual message history stored in checkpoint,
 * which is what will be sent to the LLM.
 */
export const useCheckpointMessages = ({
  threadId,
  autoRefresh = false,
  refreshInterval = 5000
}: UseCheckpointMessagesOptions): UseCheckpointMessagesReturn => {
  const [messages, setMessages] = useState<CheckpointMessage[]>([]);
  const [totalTokens, setTotalTokens] = useState(0);
  const [messageCount, setMessageCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMessages = useCallback(async () => {
    if (!threadId) {
      setMessages([]);
      setTotalTokens(0);
      setMessageCount(0);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await omind_get(
        `/api/v1/chat/threads/${threadId}/messages`
      );

      if (response.status === 'ok' && response.data) {
        const data = response.data as CheckpointMessagesData;
        setMessages(data.messages);
        setTotalTokens(data.total_tokens);
        setMessageCount(data.message_count);
      } else {
        throw new Error(response.msg || '获取消息失败');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '获取消息失败';
      setError(errorMsg);
      console.error('获取checkpoint消息失败:', err);
    } finally {
      setIsLoading(false);
    }
  }, [threadId]);

  // Initial fetch and auto refresh
  useEffect(() => {
    fetchMessages();

    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(fetchMessages, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchMessages, autoRefresh, refreshInterval]);

  return {
    messages,
    totalTokens,
    messageCount,
    isLoading,
    error,
    refresh: fetchMessages
  };
};

/**
 * Hook for comparing frontend messages with checkpoint messages
 * Useful for debugging and ensuring consistency
 */
export const useMessageComparison = (
  frontendMessages: Message[],
  checkpointMessages: CheckpointMessage[]
) => {
  const [differences, setDifferences] = useState<{
    onlyInFrontend: Message[];
    onlyInCheckpoint: CheckpointMessage[];
    contentMismatch: Array<{
      id: string;
      frontend: string;
      checkpoint: string;
    }>;
  }>({
    onlyInFrontend: [],
    onlyInCheckpoint: [],
    contentMismatch: []
  });

  useEffect(() => {
    const frontendMap = new Map(
      frontendMessages.map(msg => [msg.id || '', msg])
    );
    const checkpointMap = new Map(
      checkpointMessages.map(msg => [msg.id || '', msg])
    );

    const onlyInFrontend: Message[] = [];
    const onlyInCheckpoint: CheckpointMessage[] = [];
    const contentMismatch: Array<{
      id: string;
      frontend: string;
      checkpoint: string;
    }> = [];

    // Find messages only in frontend
    frontendMessages.forEach(msg => {
      if (msg.id && !checkpointMap.has(msg.id)) {
        onlyInFrontend.push(msg);
      }
    });

    // Find messages only in checkpoint and content mismatches
    checkpointMessages.forEach(msg => {
      if (msg.id) {
        const frontendMsg = frontendMap.get(msg.id);
        if (!frontendMsg) {
          onlyInCheckpoint.push(msg);
        } else if (frontendMsg.content !== msg.content) {
          contentMismatch.push({
            id: msg.id,
            frontend: frontendMsg.content,
            checkpoint: msg.content
          });
        }
      }
    });

    setDifferences({
      onlyInFrontend,
      onlyInCheckpoint,
      contentMismatch
    });
  }, [frontendMessages, checkpointMessages]);

  return differences;
};