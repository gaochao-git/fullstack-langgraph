import { useState, useCallback, useRef, useEffect } from 'react';
import { getBaseUrl, omind_get, omind_post, omind_chat_stream } from '@/utils/base_api';

// 消息类型定义
export interface Message {
  id?: string;
  type: 'human' | 'ai' | 'system' | 'tool';
  content: string;
  tool_calls?: any[];
  additional_kwargs?: {
    file_ids?: string[];
    file_names?: Record<string, string>;
    [key: string]: any;
  };
  name?: string; // 工具消息的名称
  tool_call_id?: string; // 工具调用ID
}

// Hook 配置选项
interface UseStreamOptions {
  apiUrl: string;
  assistantId: string;
  threadId: string | null;
  messagesKey?: string;
  onError?: (error: any) => void;
}

// Token使用情况类型
export interface TokenUsageInfo {
  used: number;
  total: number;
  percentage: number;
  remaining: number;
}

// Hook 返回类型
interface UseStreamReturn {
  messages: Message[];
  isLoading: boolean;
  interrupt: any;
  tokenUsage: TokenUsageInfo | null;
  submit: (data: any, options?: any) => void;
  stop: () => void;
}

// 自定义 useStream Hook
export const useStream = <T extends { messages: Message[] }>(options: UseStreamOptions): UseStreamReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [interrupt, setInterrupt] = useState<any>(null);
  const [tokenUsage, setTokenUsage] = useState<TokenUsageInfo | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const accumulatedMessagesRef = useRef<Message[]>([]);
  const streamingMessageRef = useRef<{ id?: string; content: string } | null>(null);

  // 从后端恢复线程消息历史
  useEffect(() => {
    if (options.threadId) {
      // 从后端获取线程历史消息
      const loadHistory = async () => {
        try {
          // 构建查询参数
          const params = new URLSearchParams();
          if (options.assistantId) {
            params.append('agent_id', options.assistantId);
          }
          const url = params.toString() 
            ? `/api/v1/chat/threads/${options.threadId}?${params.toString()}`
            : `/api/v1/chat/threads/${options.threadId}`;
          const response = await omind_get(url);
          
          // 检查响应状态
          if (response.status === 'ok' && response.data) {
            const data = response.data;
            // 后端返回的是数组格式 [{values: {messages: [...]}}, ...]
            if (Array.isArray(data) && data.length > 0) {
              // 获取最新的checkpoint中的消息
              const latestCheckpoint = data[data.length - 1];
              if (latestCheckpoint?.values?.messages) {
                setMessages(latestCheckpoint.values.messages);
                accumulatedMessagesRef.current = latestCheckpoint.values.messages;
              }
            } else if (data.messages) {
              // 兼容旧格式
              setMessages(data.messages);
              accumulatedMessagesRef.current = data.messages;
            }
          } else if (response.status === 'error') {
            // 处理错误响应
            console.error('Failed to load thread history:', response.msg);
            options.onError?.({ message: response.msg || '加载历史消息失败' });
          }
        } catch (err) {
          console.error('Failed to load thread history:', err);
          options.onError?.({ message: '加载历史消息失败' });
        }
      };
      
      loadHistory();
    }
  }, [options.threadId]);

  // 处理SSE事件
  const handleStreamEvent = useCallback((eventType: string, eventData: any) => {
    try {
      switch (eventType) {
        case 'messages':
          // 处理消息流（AIMessageChunk）
          // LangGraph 发送数组格式：[AIMessageChunk, metadata]
          if (Array.isArray(eventData) && eventData.length > 0) {
            const messageChunk = eventData[0];
            
            // 转换消息类型（参考 SDK 的做法）
            if (messageChunk.type && messageChunk.type.endsWith('MessageChunk')) {
              messageChunk.type = messageChunk.type
                .slice(0, -'MessageChunk'.length)
                .toLowerCase();
            }
            
            // 处理不同的消息类型
            if (messageChunk.type === 'ai' && messageChunk.content !== undefined) {
              // 检查是否需要创建新消息还是更新现有消息
              const shouldCreateNew = !streamingMessageRef.current || 
                                     streamingMessageRef.current.id !== messageChunk.id;
              
              if (shouldCreateNew) {
                // 开始新的流式消息
                streamingMessageRef.current = {
                  id: messageChunk.id,
                  content: messageChunk.content
                };
                const newMessage: Message = {
                  id: messageChunk.id,
                  type: 'ai',
                  content: messageChunk.content,
                  additional_kwargs: messageChunk.additional_kwargs
                };
                setMessages(prev => {
                  const updated = [...prev, newMessage];
                  return updated;
                });
              } else {
                // 累积消息内容到当前流式消息
                streamingMessageRef.current.content += messageChunk.content;
                setMessages(prev => {
                  const newMessages = [...prev];
                  // 查找具有相同 ID 的消息进行更新
                  const targetIndex = newMessages.findIndex(
                    msg => msg.type === 'ai' && msg.id === streamingMessageRef.current?.id
                  );
                  if (targetIndex >= 0) {
                    newMessages[targetIndex] = {
                      ...newMessages[targetIndex],
                      content: streamingMessageRef.current!.content
                    };
                  }
                  return newMessages;
                });
              }
            }
          }
          break;

        case 'updates':
          // 处理状态更新
          if (eventData.messages) {
            // 完整的消息列表更新
            setMessages(eventData.messages);
            accumulatedMessagesRef.current = eventData.messages;
            streamingMessageRef.current = null;
          } else if (eventData.__interrupt__) {
            // 处理中断
            setInterrupt(eventData.__interrupt__);
          } else {
            // 处理节点更新
            Object.entries(eventData).forEach(([nodeName, nodeData]: [string, any]) => {
              if (nodeData.messages && Array.isArray(nodeData.messages)) {
                // 处理消息
                const processedMessages = nodeData.messages.map((msg: any) => {
                  // 如果是 HumanMessage 格式，转换为我们的格式
                  if (msg.type === 'HumanMessage' || msg.type === 'human') {
                    return {
                      id: msg.id,
                      type: 'human' as const,
                      content: msg.content,
                      additional_kwargs: msg.additional_kwargs
                    };
                  }
                  // 如果是 AIMessage 或 AIMessageChunk 格式，转换为我们的格式
                  else if (msg.type === 'AIMessage' || msg.type === 'AIMessageChunk' || msg.type === 'ai') {
                    return {
                      id: msg.id,
                      type: 'ai' as const,
                      content: msg.content,
                      additional_kwargs: msg.additional_kwargs,
                      tool_calls: msg.tool_calls
                    };
                  }
                  // 处理工具消息
                  else if (msg.type === 'ToolMessage' || msg.type === 'tool') {
                    return {
                      id: msg.id,
                      type: 'tool' as const,
                      content: msg.content,
                      name: msg.name,
                      tool_call_id: msg.tool_call_id
                    };
                  }
                  // 其他消息类型保持不变
                  return msg;
                });
                
                // 合并新消息
                const newMessages = [...accumulatedMessagesRef.current, ...processedMessages];
                setMessages(newMessages);
                accumulatedMessagesRef.current = newMessages;
                
                // 如果有新的 AI 消息，可能需要重置流式消息引用
                const hasNewAIMessage = processedMessages.some(msg => msg.type === 'ai');
                if (hasNewAIMessage) {
                  streamingMessageRef.current = null;
                }
              }
            });
          }
          break;

        case 'values':
          // 处理完整状态值
          if (eventData.messages) {
            setMessages(eventData.messages);
            accumulatedMessagesRef.current = eventData.messages;
          }
          break;

        case 'error':
          options.onError?.(eventData);
          break;

        case 'heartbeat':
          // 心跳事件，仅用于保持连接，不做处理
          console.debug('SSE heartbeat received:', eventData.timestamp);
          break;

        case 'token_usage':
          // 处理token使用情况
          if (eventData.token_usage) {
            setTokenUsage(eventData.token_usage);
          }
          break;

        case 'end':
          // 流结束
          streamingMessageRef.current = null;
          break;
      }
    } catch (error) {
      console.error('Error handling stream event:', error, { eventType, eventData });
    }
  }, [options]);

  // 提交消息
  const submit = useCallback(async (data: any, submitOptions?: any) => {
    if (!options.threadId) {
      options.onError?.({ code: 400, message: '缺少线程ID' });
      return;
    }

    // 清理之前的流
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    streamingMessageRef.current = null;
    
    setIsLoading(true);
    setInterrupt(null);

    // 从 data 中提取用户消息和文件信息
    let userQuery = '';
    let fileIds: string[] = [];
    
    if (data.messages && Array.isArray(data.messages)) {
      const userMessage = data.messages[0]; // 假设只有一条用户消息
      userQuery = userMessage.content || '';
      fileIds = userMessage.file_ids || [];
      
      // 立即添加用户消息到消息列表
      const userMessages = data.messages.map((msg: any) => ({
        id: msg.id || `user-${Date.now()}`,
        type: msg.type || 'human',
        content: msg.content,
        additional_kwargs: msg.additional_kwargs || {},
        file_ids: msg.file_ids
      }));
      setMessages(prev => [...prev, ...userMessages]);
      accumulatedMessagesRef.current = [...accumulatedMessagesRef.current, ...userMessages];
    }

    try {
      // 构建新的请求格式
      const requestBody: any = {
        agent_id: options.assistantId,
        user_name: submitOptions?.config?.configurable?.user_name || 'anonymous',
        query: userQuery,
      };

      // 添加可选参数
      if (fileIds.length > 0) {
        requestBody.file_ids = fileIds;
      }

      // 构建 config 对象
      const config: any = {};
      if (submitOptions?.config?.configurable?.selected_model) {
        config.selected_model = submitOptions.config.configurable.selected_model;
      }
      config.stream_mode = submitOptions?.streamMode || ["updates", "messages", "values"];
      
      requestBody.config = config;
      // 添加 chat_mode
      requestBody.chat_mode = "streaming";

      // 使用统一的聊天流式请求方法
      await omind_chat_stream(`/api/v1/chat/threads/${options.threadId}/completion`, {
        body: requestBody,
        signal: abortControllerRef.current.signal,
        onEvent: handleStreamEvent,
        onError: (error) => {
          options.onError?.(error);
        },
        onComplete: () => {
          // 流结束
          streamingMessageRef.current = null;
        }
      });
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        options.onError?.(error);
      }
    } finally {
      setIsLoading(false);
    }
  }, [options, handleStreamEvent]);

  // 停止流
  const stop = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
    streamingMessageRef.current = null;
  }, []);


  return {
    messages,
    isLoading,
    interrupt,
    tokenUsage,
    submit,
    stop
  };
};