import { useState, useCallback } from 'react';
import { omind_post } from '@/utils/base_api';
import { Message } from '@/hooks/useStream';
import { message as antMessage } from 'antd';

interface CompressOptions {
  compressionLevel?: 'light' | 'medium' | 'heavy'; // 压缩程度
  preserveContext?: boolean; // 是否保留上下文关系
  targetTokenRatio?: number; // 目标压缩比例 (0.3 = 压缩到30%)
}

interface UseMessageCompressionReturn {
  compressMessages: (messages: Message[], options?: CompressOptions) => Promise<Message[]>;
  compressSingleMessage: (message: Message, options?: CompressOptions) => Promise<Message>;
  isCompressing: boolean;
  compressionError: Error | null;
}

export const useMessageCompression = (): UseMessageCompressionReturn => {
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressionError, setCompressionError] = useState<Error | null>(null);

  // 压缩单条消息
  const compressSingleMessage = useCallback(async (
    message: Message, 
    options: CompressOptions = {}
  ): Promise<Message> => {
    const {
      compressionLevel = 'medium',
      preserveContext = true,
      targetTokenRatio = 0.5
    } = options;

    try {
      setIsCompressing(true);
      setCompressionError(null);

      // 构建压缩请求
      const response = await omind_post('/api/v1/agent/v1/chat/compress-message', {
        message: {
          id: message.id,
          type: message.type,
          content: message.content,
          additional_kwargs: message.additional_kwargs
        },
        options: {
          compression_level: compressionLevel,
          preserve_context: preserveContext,
          target_token_ratio: targetTokenRatio
        }
      });

      if (response.status === 'ok' && response.data) {
        return response.data.compressed_message;
      } else {
        throw new Error(response.msg || '消息压缩失败');
      }
    } catch (error) {
      const err = error as Error;
      setCompressionError(err);
      antMessage.error(`压缩失败: ${err.message}`);
      throw err;
    } finally {
      setIsCompressing(false);
    }
  }, []);

  // 批量压缩消息
  const compressMessages = useCallback(async (
    messages: Message[],
    options: CompressOptions = {}
  ): Promise<Message[]> => {
    const {
      compressionLevel = 'medium',
      preserveContext = true,
      targetTokenRatio = 0.5
    } = options;

    try {
      setIsCompressing(true);
      setCompressionError(null);

      // 过滤可压缩的消息（主要是AI消息，用户消息通常不压缩）
      const compressibleMessages = messages.filter(msg => 
        msg.type === 'ai' && msg.content && msg.content.length > 100
      );

      if (compressibleMessages.length === 0) {
        antMessage.warning('没有可压缩的消息');
        return messages;
      }

      // 批量压缩请求
      const response = await omind_post('/api/v1/agent/v1/chat/compress-messages', {
        messages: compressibleMessages.map(msg => ({
          id: msg.id,
          type: msg.type,
          content: msg.content,
          additional_kwargs: msg.additional_kwargs
        })),
        options: {
          compression_level: compressionLevel,
          preserve_context: preserveContext,
          target_token_ratio: targetTokenRatio
        }
      });

      if (response.status === 'ok' && response.data) {
        const compressedMap = new Map<string, Message>();
        response.data.compressed_messages.forEach((msg: Message) => {
          if (msg.id) {
            compressedMap.set(msg.id, msg);
          }
        });

        // 替换原消息数组中的压缩消息
        return messages.map(msg => {
          if (msg.id && compressedMap.has(msg.id)) {
            return compressedMap.get(msg.id)!;
          }
          return msg;
        });
      } else {
        throw new Error(response.msg || '批量消息压缩失败');
      }
    } catch (error) {
      const err = error as Error;
      setCompressionError(err);
      antMessage.error(`批量压缩失败: ${err.message}`);
      throw err;
    } finally {
      setIsCompressing(false);
    }
  }, []);

  return {
    compressMessages,
    compressSingleMessage,
    isCompressing,
    compressionError
  };
};

// 导出压缩级别的中文映射
export const COMPRESSION_LEVEL_MAP = {
  light: '轻度压缩',
  medium: '中度压缩',
  heavy: '重度压缩'
};

// 辅助函数：估算消息的token数量（粗略估算）
export const estimateTokenCount = (content: string): number => {
  // 中文约1.5字符/token，英文约4字符/token
  const chineseChars = (content.match(/[\u4e00-\u9fff]/g) || []).length;
  const englishChars = content.length - chineseChars;
  return Math.ceil(chineseChars / 1.5 + englishChars / 4);
};