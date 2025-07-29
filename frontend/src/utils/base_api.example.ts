/**
 * base_api 使用示例
 */

import { omind_fetch, omind_fetch_stream, omind_get, omind_post, omind_put, omind_del } from './base_api';

// ===== 1. 普通HTTP请求示例 =====

// 示例1：GET请求获取智能体列表
export async function getAgentsList() {
  try {
    const response = await omind_get('/api/v1/agents');
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('获取智能体列表失败:', error);
    throw error;
  }
}

// 示例2：POST请求创建智能体
export async function createAgent(agentData: any) {
  try {
    const response = await omind_post('/api/v1/agents', agentData);
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('创建智能体失败:', error);
    throw error;
  }
}

// 示例3：使用omind_fetch进行自定义请求
export async function customRequest() {
  try {
    const response = await omind_fetch('/api/v1/agents/diagnostic_agent', {
      method: 'GET',
      headers: {
        'Custom-Header': 'custom-value'
      },
      timeout: 10000 // 10秒超时
    });
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('自定义请求失败:', error);
    throw error;
  }
}

// ===== 2. 流式请求示例 =====

// 示例1：与大模型进行流式对话
export async function streamChat(threadId: string, messages: any[]) {
  const requestBody = {
    assistant_id: "diagnostic_agent",
    input: {
      messages: messages,
      user_name: "zhangsan123"
    },
    config: {
      configurable: {
        selected_model: "qwen2.5-72b-instruct"
      }
    },
    stream_mode: ["messages-tuple", "values", "updates"],
    on_disconnect: "cancel"
  };

  try {
    await omind_fetch_stream(`/api/chat/threads/${threadId}/runs/stream`, {
      method: 'POST',
      body: requestBody,
      onData: (data: string) => {
        // 处理流式数据
        try {
          const parsedData = JSON.parse(data);
          console.log('收到流式数据:', parsedData);
          // 更新UI状态
          // updateMessages(parsedData);
        } catch (e) {
          console.log('收到非JSON数据:', data);
        }
      },
      onError: (error: Error) => {
        console.error('流式请求错误:', error);
        // 显示错误信息
        // showError(error.message);
      },
      onComplete: () => {
        console.log('流式请求完成');
        // 标记对话完成
        // setIsStreaming(false);
      }
    });
  } catch (error) {
    console.error('启动流式请求失败:', error);
    throw error;
  }
}

// 示例2：React Hook中使用流式请求
export function useStreamChat() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);

  const startStream = async (threadId: string, userMessage: string) => {
    setIsStreaming(true);
    
    const requestBody = {
      assistant_id: "diagnostic_agent",
      input: {
        messages: [{ type: "human", content: userMessage }],
        user_name: "zhangsan123"
      },
      config: {
        configurable: {
          selected_model: "qwen2.5-72b-instruct"
        }
      },
      stream_mode: ["messages-tuple", "values", "updates"],
      on_disconnect: "cancel"
    };

    try {
      await omind_fetch_stream(`/api/chat/threads/${threadId}/runs/stream`, {
        body: requestBody,
        onData: (data: string) => {
          try {
            const parsedData = JSON.parse(data);
            // 更新消息列表
            setMessages(prev => [...prev, parsedData]);
          } catch (e) {
            console.log('非JSON数据:', data);
          }
        },
        onError: (error: Error) => {
          console.error('流式对话错误:', error);
          setIsStreaming(false);
        },
        onComplete: () => {
          console.log('对话完成');
          setIsStreaming(false);
        }
      });
    } catch (error) {
      console.error('启动对话失败:', error);
      setIsStreaming(false);
    }
  };

  return {
    isStreaming,
    messages,
    startStream
  };
}

// ===== 3. 错误处理示例 =====

// 带重试机制的请求
export async function requestWithRetry<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      console.log(`请求失败，${delay}ms后重试... (${i + 1}/${maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= 2; // 指数退避
    }
  }
  throw new Error('重试次数已用完');
}

// 使用重试机制的示例
export async function getAgentWithRetry(agentId: string) {
  return requestWithRetry(async () => {
    const response = await omind_get(`/api/v1/agents/${agentId}`);
    return response.json();
  });
}