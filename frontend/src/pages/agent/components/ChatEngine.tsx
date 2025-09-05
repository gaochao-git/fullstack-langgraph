import { useStream, type Message } from "@/hooks/useStream";
import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import ChatMessages from "./ChatMessage";
import { Drawer, App } from "antd";
import { useTheme } from "@/hooks/ThemeContext";
import { cn } from "@/utils/lib-utils";
import { omind_get, getBaseUrl } from "@/utils/base_api";
import { type Agent } from "@/services/agentApi";
import { threadApi } from "@/services/threadApi";
import { getCurrentUsername } from "@/utils/authInterceptor";

// 历史会话类型定义
interface HistoryThread {
  thread_id: string;
  thread_title: string;
  create_at: string;
  update_at: string;
}

// 模型信息类型定义
interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  type: string;
}

// 欢迎页面组件接口
interface WelcomeComponentProps {
  agent: Agent | null;
  onSubmit: (message: string, fileIds?: string[]) => void;
}

// 聊天引擎组件属性
interface ChatEngineProps {
  agentId: string;
  agent: Agent | null;
  WelcomeComponent?: React.ComponentType<WelcomeComponentProps>;
  onNewSession: () => void;
}

export default function ChatEngine({ 
  agentId, 
  agent, 
  WelcomeComponent,
  onNewSession 
}: ChatEngineProps) {
  const { isDark } = useTheme();
  const { message } = App.useApp();
  const [error, setError] = useState<string | null>(null);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [historyThreads, setHistoryThreads] = useState<HistoryThread[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [threadFileIds, setThreadFileIds] = useState<string[]>([]);
  // 分页相关状态
  const [currentOffset, setCurrentOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  
  // 模型管理状态
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [currentModel, setCurrentModel] = useState<string>('');
  
  // 用于跟踪当前线程ID的状态 - 先不初始化，稍后在定义getThreadIdFromUrl后再设置
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  
  // 新增：正在发送的用户消息
  const [sendingUserMessage, setSendingUserMessage] = useState<{content: string; fileIds?: string[]} | null>(null);

  // 获取agentId，用于LangGraph SDK的assistantId字段
  const getAgentId = (): string => {
    // 如果agent不存在，使用传入的agentId参数
    if (!agent) {
      return agentId;
    }
    
    // 优先使用agent_id（来自API的agent对象），如果没有则使用id（硬编码的agent对象）
    const id = agent.agent_id || (agent.id ? agent.id.toString() : '');
    if (!id) {
      // 如果agent对象中没有id，使用传入的agentId参数
      return agentId;
    }
    
    return id;
  };

  // 从URL参数中获取线程ID
  const getThreadIdFromUrl = () => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('thread_id') || null;
  };

  // 构造完整的 API URL
  const baseUrl = getBaseUrl() || window.location.origin;
  const apiUrl = `${baseUrl}/api/v1/chat`;
  
  // 初始化currentThreadId
  useEffect(() => {
    const threadIdFromUrl = getThreadIdFromUrl();
    if (threadIdFromUrl) {
      setCurrentThreadId(threadIdFromUrl);
    }
  }, []);
  
  // 在组件初始化时创建线程（如果没有URL中的thread_id）
  useEffect(() => {
    const initThread = async () => {
      const threadIdFromUrl = getThreadIdFromUrl();
      if (!threadIdFromUrl) {
        try {
          const newThread = await threadApi.create({
            assistant_id: getAgentId()
          });
          // 更新URL
          const url = new URL(window.location.href);
          url.searchParams.set('thread_id', newThread.thread_id);
          window.history.replaceState({}, '', url.toString());
          
          // 更新线程ID状态，这将触发useStream重新初始化
          setCurrentThreadId(newThread.thread_id);
          
          console.log('✅ 初始化时创建新线程成功:', newThread.thread_id);
        } catch (error) {
          console.error('创建线程失败:', error);
          message.error('创建会话失败，请重试');
        }
      }
    };
    
    initThread();
  }, []); // 只在组件挂载时运行一次
  
  // 如果agent不存在，使用占位的agent_id
  const thread = useStream<{
    messages: Message[];
  }>({
    apiUrl: apiUrl,
    assistantId: getAgentId(),
    messagesKey: "messages",
    threadId: currentThreadId,  // 使用状态中的线程ID
    onError: (error: any) => {
      // 检查是否是智能体密钥错误
      if (error.code === 461 || error.status === 461) {
        message.error(error.message || '智能体调用密钥错误');
      } else {
        // 其他错误显示错误消息
        message.error(error.message || '请求失败');
      }
      setError(error.message);
    },
  });
  
  // 监听消息变化，当用户消息出现在流中时，清除发送中状态
  useEffect(() => {
    if (sendingUserMessage && thread.messages.length > 0) {
      // 查找是否有匹配的用户消息
      const lastUserMessage = [...thread.messages].reverse().find(msg => msg.type === 'human');
      if (lastUserMessage && lastUserMessage.content === sendingUserMessage.content) {
        // 用户消息已经在流中了，清除发送中状态
        setSendingUserMessage(null);
      }
    }
  }, [thread.messages, sendingUserMessage]);

  // 使用传入的agent数据获取配置信息，避免重复API请求
  useEffect(() => {
    if (!agent) return;
    
    try {
      let availableModelNames: string[] = [];
      
      // 只处理新的数据结构
      if (Array.isArray(agent.llm_info)) {
        // 新格式：从数组中提取所有model_name
        availableModelNames = agent.llm_info.map((config: any) => config.model_name).filter(Boolean);
      } else {
        // 旧格式，显示错误
        console.error('智能体使用旧版LLM配置格式，需要更新配置');
        setAvailableModels([]);
        return;
      }
      
      // 转换为ModelInfo格式
      const models: ModelInfo[] = availableModelNames.map((modelName: string) => ({
        id: modelName,
        name: modelName,
        provider: 'default',
        type: modelName
      }));
      
      setAvailableModels(models);
      
      // 设置默认选中的模型
      if (!currentModel && Array.isArray(agent.llm_info) && agent.llm_info.length > 0) {
        // 新格式：使用第一个配置的模型
        const defaultModelName = agent.llm_info[0].model_name;
        if (defaultModelName) {
          setCurrentModel(defaultModelName);
        }
      }
    } catch (error) {
      console.error('处理agent配置信息失败:', error);
    }
  }, [agent]); // 移除 currentModel 依赖，避免循环更新


  // 当有线程ID时，获取关联的文件ID
  useEffect(() => {
    if (currentThreadId) {
      threadApi.getThreadFiles(currentThreadId)
        .then(result => {
          setThreadFileIds(result.file_ids || []);
          console.log('✅ 获取会话文件成功:', result.file_ids);
        })
        .catch(err => {
          console.error('获取会话文件失败:', err);
          setThreadFileIds([]);
        });
    }
  }, [currentThreadId]);


  const handleSubmit = useCallback(
    (submittedInputValue: string, fileIds?: string[]) => {
      if (!submittedInputValue.trim() && !fileIds?.length) return;

      // 立即设置发送中的消息，用于显示loading
      setSendingUserMessage({
        content: submittedInputValue,
        fileIds: fileIds
      });

      // 构建消息对象，将 file_ids 作为消息的一部分
      const currentMessage: Message = {
        type: "human",
        content: submittedInputValue,
        ...(fileIds && fileIds.length > 0 && { file_ids: fileIds })
      } as Message;
      
      // 调试日志
      if (fileIds && fileIds.length > 0) {
        console.log('📎 提交文件数量:', fileIds.length, '文件IDs:', fileIds);
      }
      
      // 构建提交数据，只包含当前消息
      const submitData = {messages: [currentMessage]};
      
      const submitConfig = {
        configurable: {
          ...(currentModel && { selected_model: currentModel }),
          ...(getCurrentUsername() && { user_name: getCurrentUsername() }),
        }
      };
      
      // 构建提交选项
      const submitOptions = {
        config: submitConfig,
        streamMode: ["updates", "messages", "values"]
      };
      
      // 最终提交
      thread.submit(submitData as any, submitOptions as any);
    },
    [thread, currentModel, agentId]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
  }, [thread]);

  // 模型切换处理函数
  const handleModelChange = useCallback((modelType: string) => {
    setCurrentModel(modelType);
    // 切换到模型: modelType
  }, []);

  const handleInterruptResume = useCallback((approved: boolean | string[]) => {
    thread.submit(undefined, { 
      command: { resume: approved }
    } as any);
  }, [thread]);

  // 加载历史线程数据
  const loadHistoryThreads = useCallback(async (append = false) => {
    // 如果是追加加载，使用loadingMore状态
    if (append) {
      setLoadingMore(true);
    } else {
      setLoadingHistory(true);
    }
    
    try {
      // 使用新的API路径
      const username = getCurrentUsername();
      const offset = append ? currentOffset : 0;
      const params = new URLSearchParams({
        limit: '20',
        offset: offset.toString(),
        assistant_id: agentId,
        user_name: username
      });
      const url = `/api/v1/chat/threads?${params.toString()}`;
      const response = await omind_get(url);
      
      // 检查响应状态
      if (response.status !== 'ok') {
        throw new Error(response.msg || '获取历史会话失败');
      }
      
      const data = response.data || {};
      const threads = data.threads || [];
      
      if (append) {
        // 追加到现有列表
        setHistoryThreads(prev => [...prev, ...threads]);
      } else {
        // 替换列表（初始加载或刷新）
        setHistoryThreads(threads);
        setCurrentOffset(0);
      }
      
      // 更新分页状态
      setCurrentOffset(offset + threads.length);
      setHasMore(threads.length === 20); // 如果返回少于20条，说明没有更多了
      setError(null); // 清除错误状态
    } catch (error) {
      // 获取历史线程出错
      setError('获取历史线程出错');
    } finally {
      setLoadingHistory(false);
      setLoadingMore(false);
    }
  }, [agentId, currentOffset]);

  // 加载更多历史线程
  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore) {
      loadHistoryThreads(true);
    }
  }, [loadingMore, hasMore, loadHistoryThreads]);

  // 切换历史会话抽屉显示/隐藏
  const handleToggleHistoryDrawer = useCallback(() => {
    setShowHistoryDrawer(prev => !prev);
    // 如果抽屉要打开，加载历史数据
    if (!showHistoryDrawer) {
      // 重置分页状态并加载第一页
      setCurrentOffset(0);
      setHasMore(true);
      loadHistoryThreads(false);
    }
  }, [showHistoryDrawer, loadHistoryThreads]);

  // 切换到历史会话
  const handleSwitchToThread = useCallback((threadId: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set('thread_id', threadId);
    window.location.href = url.toString();
  }, []);
  
  return (
    <>
      {error ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className={cn(
              "flex flex-col items-center justify-center gap-4 p-8 rounded-lg shadow-lg border",
              isDark 
                ? "bg-gray-800 border-red-600 text-red-400" 
                : "bg-white border-red-400 text-red-600"
            )}>
              <h1 className="text-2xl font-bold">错误</h1>
              <p className={cn(isDark ? "text-red-300" : "text-red-500")}>
                {JSON.stringify(error)}
              </p>
              <Button
                variant="destructive"
                onClick={() => window.location.reload()}
              >
                重试
              </Button>
            </div>
          </div>
        ) : (
          // 显示标准对话视图，如果有自定义欢迎组件则传递给ChatMessages
          <ChatMessages
            messages={thread.messages}
            isLoading={thread.isLoading}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            interrupt={thread.interrupt}
            onInterruptResume={handleInterruptResume}
            onNewSession={onNewSession}
            onHistoryToggle={handleToggleHistoryDrawer}
            availableModels={availableModels}
            currentModel={currentModel}
            onModelChange={handleModelChange}
            WelcomeComponent={WelcomeComponent}
            agent={agent}
            threadFileIds={threadFileIds}
            sendingUserMessage={sendingUserMessage}
          />
        )}
      
      {/* 历史会话抽屉 */}
      <Drawer
        title="历史会话"
        placement="right"
        onClose={() => setShowHistoryDrawer(false)}
        open={showHistoryDrawer}
        width={400}
        styles={{
          header: {
            backgroundColor: isDark ? '#111827' : '#ffffff',
            color: isDark ? '#ffffff' : '#111827',
            borderBottom: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`
          },
          body: {
            backgroundColor: isDark ? '#1F2937' : '#f9fafb',
            padding: '16px'
          }
        }}
      >
        <div className="space-y-3">
          {loadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <div className={cn(isDark ? "text-blue-300" : "text-blue-600")}>
                加载中...
              </div>
            </div>
          ) : historyThreads.length > 0 ? (
            historyThreads.map((historyThread) => (
              <div
                key={historyThread.thread_id}
                className={cn(
                  "p-4 rounded-lg border cursor-pointer transition-all duration-200 hover:shadow-md",
                  (thread as any).threadId === historyThread.thread_id 
                    ? (isDark 
                        ? 'bg-blue-800/50 border-blue-400 shadow-sm' 
                        : 'bg-blue-50 border-blue-300 shadow-sm')
                    : (isDark 
                        ? 'border-gray-600 hover:bg-gray-700/50 bg-gray-800' 
                        : 'border-gray-200 hover:bg-gray-50 bg-white')
                )}
                onClick={() => {
                  handleSwitchToThread(historyThread.thread_id);
                  setShowHistoryDrawer(false);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className={cn(
                      "text-sm font-medium truncate",
                      isDark ? "text-gray-200" : "text-gray-900"
                    )}>
                      {historyThread.thread_title || '未命名对话'}
                    </div>
                    <div className={cn(
                      "text-xs mt-1",
                      isDark ? "text-gray-400" : "text-gray-500"
                    )}>
                      {new Date(historyThread.create_at).toLocaleString('zh-CN', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                    <div className={cn(
                      "text-xs mt-1 font-mono",
                      isDark ? "text-gray-500" : "text-gray-400"
                    )}>
                      ID: {historyThread.thread_id.substring(0, 8)}...
                    </div>
                  </div>
                  {(thread as any).threadId === historyThread.thread_id && (
                    <div className={cn(
                      "text-xs font-medium ml-2",
                      isDark ? "text-cyan-400" : "text-blue-600"
                    )}>
                      当前
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className={cn(
              "text-center py-8",
              isDark ? "text-gray-400" : "text-gray-500"
            )}>
              暂无历史会话
            </div>
          )}
          
          {/* 加载更多按钮 */}
          {historyThreads.length > 0 && hasMore && (
            <div className="mt-4 text-center">
              <Button
                onClick={loadMore}
                disabled={loadingMore}
                className={cn(
                  "w-full",
                  isDark 
                    ? "bg-gray-700 hover:bg-gray-600 text-gray-200" 
                    : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                )}
              >
                {loadingMore ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    加载中...
                  </span>
                ) : (
                  '加载更多'
                )}
              </Button>
            </div>
          )}
          
          {/* 没有更多数据提示 */}
          {historyThreads.length > 0 && !hasMore && (
            <div className={cn(
              "text-center py-2 text-sm",
              isDark ? "text-gray-500" : "text-gray-400"
            )}>
              没有更多会话了
            </div>
          )}
        </div>
      </Drawer>
    </>
  );
}