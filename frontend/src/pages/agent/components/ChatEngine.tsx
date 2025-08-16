import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import ChatMessages, { type ProcessedEvent } from "./ChatMessage";
import { Drawer } from "antd";
import { useTheme } from "@/hooks/ThemeContext";
import { cn } from "@/utils/lib-utils";
import { omind_get, getBaseUrl } from "@/utils/base_api";
import { type Agent } from "@/services/agentApi";

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
  onSubmit: (message: string) => void;
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
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<ProcessedEvent[]>([]);
  const [historicalActivities, setHistoricalActivities] = useState<Record<string, ProcessedEvent[]>>({});
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [historyThreads, setHistoryThreads] = useState<HistoryThread[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  
  // 模型管理状态
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [currentModel, setCurrentModel] = useState<string>('');

  // 获取agentId，用于LangGraph SDK的assistantId字段
  const getAgentId = () => {
    // 如果agent不存在，使用传入的agentId参数
    if (!agent) {
      return agentId;
    }
    
    // 优先使用agent_id（来自API的agent对象），如果没有则使用id（硬编码的agent对象）
    const id = agent.agent_id || agent.id;
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

  // 获取线程ID配置 - 只有当URL中有线程ID时才传递，否则让LangGraph自动生成
  const getThreadIdConfig = () => {
    const threadIdFromUrl = getThreadIdFromUrl();
    return threadIdFromUrl ? { threadId: threadIdFromUrl } : {};
  };

  // 构造完整的 API URL
  const baseUrl = getBaseUrl() || window.location.origin;
  const apiUrl = `${baseUrl}/api/chat`;
  
  // 如果agent不存在，使用占位的agent_id
  const thread = useStream<{
    messages: Message[];
  }>({
    apiUrl: apiUrl,
    assistantId: getAgentId(),
    messagesKey: "messages",
    ...getThreadIdConfig(),
    onUpdateEvent: (event: any) => {
      let processedEvent: ProcessedEvent | null = null;
      if (event.diagnostic_step) {
        processedEvent = {
          title: "Diagnostic Step",
          data: event.diagnostic_step || "",
        };
      } else if (event.analysis) {
        processedEvent = {
          title: "Analysis",
          data: event.analysis || "",
        };
      } else if (event.finalize_diagnosis) {
        processedEvent = {
          title: "Finalizing Diagnosis",
          data: "Composing final diagnostic report.",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
    onError: (error: any) => {
      setError(error.message);
    },
  });

  // 使用传入的agent数据获取配置信息，避免重复API请求
  useEffect(() => {
    if (!agent) return;
    
    try {
      // 直接从传入的agent对象中获取配置信息
      const availableModelNames = agent.llm_info?.available_models || [];
      
      // 转换为ModelInfo格式
      const models: ModelInfo[] = availableModelNames.map((modelName: string) => ({
        id: modelName,
        name: modelName,
        provider: 'default',
        type: modelName
      }));
      
      setAvailableModels(models);
      // 智能体可用模型列表
      
      // 设置默认选中当前使用的模型
      // 只在 currentModel 未设置时才设置默认值
      if (!currentModel) {
        const currentModelName = agent.llm_info?.model_name;
        if (currentModelName) {
          setCurrentModel(currentModelName);
        } else if (models.length > 0) {
          setCurrentModel(models[0].type);
        }
      }
    } catch (error) {
      // 处理agent配置信息失败
    }
  }, [agent]); // 移除 currentModel 依赖，避免循环更新

  // 当新线程创建时，将线程ID同步到URL
  useEffect(() => {
    if (thread.threadId && !getThreadIdFromUrl()) {
      const url = new URL(window.location.href);
      url.searchParams.set('thread_id', thread.threadId);
      window.history.replaceState({}, '', url.toString());
    }
  }, [thread.threadId]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, fileIds?: string[]) => {
      if (!submittedInputValue.trim() && !fileIds?.length) return;
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      
      // 构建完整的提交数据，包含模型选择信息
      const submitData = {
        messages: newMessages,
        user_name: "zhangsan123", // 临时固定用户名，后续可从用户系统获取
      };
      
      const submitConfig = {
        configurable: {
          ...(currentModel && { selected_model: currentModel }),
          ...(fileIds && fileIds.length > 0 && { file_ids: fileIds })
        }
      };
      
      // 前端提交数据
      // 前端提交配置
      
      const submitOptions = {
        config: submitConfig,
        user_name: "zhangsan123"
      };
      
      // 最终提交选项
      thread.submit(submitData, submitOptions);
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

  const handleInterruptResume = useCallback((approved: boolean) => {
    thread.submit(undefined, { 
      command: { resume: approved },
      user_name: "zhangsan123"
    });
  }, [thread]);

  // 加载历史线程数据
  const loadHistoryThreads = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const data = await omind_get('/api/chat/users/zhangsan123/threads?limit=20&offset=0');
      
      // omind_get 直接返回解析后的数据
      const threads = data.threads || [];
      setHistoryThreads(threads);
      setError(null); // 清除错误状态
    } catch (error) {
      // 获取历史线程出错
      setError('获取历史线程出错');
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  // 切换历史会话抽屉显示/隐藏
  const handleToggleHistoryDrawer = useCallback(() => {
    setShowHistoryDrawer(prev => !prev);
    // 如果抽屉要打开，加载历史数据
    if (!showHistoryDrawer) {
      loadHistoryThreads();
    }
  }, [showHistoryDrawer, loadHistoryThreads]);

  // 切换到历史会话
  const handleSwitchToThread = useCallback((threadId: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set('thread_id', threadId);
    window.location.href = url.toString();
  }, []);

  // 如果有自定义欢迎组件且没有消息，显示自定义欢迎页面
  const shouldShowCustomWelcome = WelcomeComponent && (!thread.messages || thread.messages.length === 0);

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
            liveActivityEvents={processedEventsTimeline}
            historicalActivities={historicalActivities}
            interrupt={thread.interrupt}
            onInterruptResume={handleInterruptResume}
            onNewSession={onNewSession}
            onHistoryToggle={handleToggleHistoryDrawer}
            availableModels={availableModels}
            currentModel={currentModel}
            onModelChange={handleModelChange}
            WelcomeComponent={WelcomeComponent}
            agent={agent}
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
                  thread.threadId === historyThread.thread_id 
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
                  {thread.threadId === historyThread.thread_id && (
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
        </div>
      </Drawer>
    </>
  );
}